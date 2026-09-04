"""
QXL Compiler — Flask Backend API
==================================
Central API server that orchestrates the entire compiler pipeline
and serves results to the frontend IDE.

Endpoints:
    POST /compile          — Full compilation pipeline
    POST /run              — Execute generated Python
    GET  /tokens           — Last compilation's token list
    GET  /ast              — AST as JSON tree
    GET  /symbol-table     — Symbol table data
    GET  /intermediate     — Three-address code text
    GET  /generated-python — Generated Python source
    GET  /parse-tree       — Parse tree as base64 PNG
    GET  /programs         — List saved programs
    POST /programs         — Save a program
    GET  /programs/<id>    — Load a program
    GET  /examples         — List sample programs
    GET  /examples/<name>  — Load a sample program
    GET  /history          — Compilation history
"""

from __future__ import annotations

import base64
import json
import os
import sqlite3
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

from flask import Flask, jsonify, request, send_file, send_from_directory
from flask_cors import CORS
import sys

# Add the project root to sys.path so 'backend' can be resolved
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# ── Compiler Pipeline Imports ───────────────────────────────
from backend.lexer import QXLLexer
from backend.parser import QXLParser
from backend.semantic import SemanticAnalyzer
from backend.intermediate import IRGenerator
from backend.generator import PythonGenerator
from backend.executor import QXLExecutor
from backend.utils import (
    serialize_ast, get_generated_dir, get_graph_dir,
    ensure_directory, write_file, read_file
)

# ═════════════════════════════════════════════════════════════
# APPLICATION SETUP
# ═════════════════════════════════════════════════════════════

app = Flask(__name__)
CORS(app)

# Project paths
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXAMPLES_DIR = os.path.join(PROJECT_ROOT, "examples")
DB_PATH = os.path.join(PROJECT_ROOT, ".qxl_database.db")
FRONTEND_DIR = os.path.join(PROJECT_ROOT, "frontend")

@app.route("/")
def serve_frontend():
    return send_from_directory(FRONTEND_DIR, "index.html")

@app.route("/<path:path>")
def serve_frontend_files(path):
    file_path = os.path.join(FRONTEND_DIR, path)
    if os.path.isfile(file_path):
        return send_from_directory(FRONTEND_DIR, path)
    return jsonify({"error": "Resource not found"}), 404

# ── Compilation State (last compilation results) ────────────
_state: Dict[str, Any] = {
    "tokens": [],
    "ast": None,
    "ast_json": None,
    "symbol_table": None,
    "intermediate": "",
    "generated_python": "",
    "errors": [],
    "statistics": {},
    "parse_tree_png": None,
    "ast_png": None,
}


# ═════════════════════════════════════════════════════════════
# DATABASE
# ═════════════════════════════════════════════════════════════

def get_db() -> sqlite3.Connection:
    """Get a database connection."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Initialize the SQLite database with required tables."""
    conn = get_db()
    cursor = conn.cursor()

    # Programs table — saved user programs
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS programs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            code TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Compilation history table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS compilation_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            program_name TEXT,
            source_code TEXT NOT NULL,
            success INTEGER NOT NULL DEFAULT 0,
            error_count INTEGER DEFAULT 0,
            token_count INTEGER DEFAULT 0,
            compilation_time_ms REAL DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Sample programs table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sample_programs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            description TEXT,
            code TEXT NOT NULL
        )
    """)

    conn.commit()

    # Load sample programs from examples/ directory
    _load_sample_programs(conn)

    conn.close()


def _load_sample_programs(conn: sqlite3.Connection) -> None:
    """Load sample .qxl files from the examples/ directory into the database."""
    if not os.path.exists(EXAMPLES_DIR):
        return

    cursor = conn.cursor()
    for filename in os.listdir(EXAMPLES_DIR):
        if filename.endswith(".qxl"):
            name = filename[:-4]  # Remove .qxl extension
            filepath = os.path.join(EXAMPLES_DIR, filename)
            code = read_file(filepath)
            if code:
                cursor.execute(
                    "INSERT OR REPLACE INTO sample_programs (name, description, code) VALUES (?, ?, ?)",
                    (name, f"Sample: {name}", code)
                )
    conn.commit()


# ═════════════════════════════════════════════════════════════
# INITIALIZATION (Runs on import for Gunicorn compatibility)
# ═════════════════════════════════════════════════════════════
init_db()
ensure_directory(get_generated_dir())
ensure_directory(get_graph_dir())

# ═════════════════════════════════════════════════════════════
# GRAPHVIZ VISUALIZATION
# ═════════════════════════════════════════════════════════════

def generate_tree_image(ast_node: Any, filename: str = "parse_tree") -> Optional[str]:
    """Generate a tree visualization using Graphviz and return base64 PNG.
    
    Falls back gracefully if Graphviz is not installed.
    """
    try:
        import graphviz
    except ImportError:
        return None

    dot = graphviz.Digraph(
        comment="QXL Parse Tree",
        format="png",
        graph_attr={
            "bgcolor": "#1e1e2e",
            "fontcolor": "#cdd6f4",
            "rankdir": "TB",
            "splines": "ortho",
            "nodesep": "0.6",
            "ranksep": "0.8",
        },
        node_attr={
            "style": "filled,rounded",
            "fillcolor": "#313244",
            "fontcolor": "#cdd6f4",
            "fontname": "JetBrains Mono",
            "fontsize": "12",
            "shape": "box",
            "penwidth": "0.5",
            "color": "#585b70",
        },
        edge_attr={
            "color": "#6c7086",
            "arrowsize": "0.6",
            "penwidth": "0.8",
        },
    )

    _counter = [0]

    def add_node(node: Any, parent_id: Optional[str] = None) -> str:
        """Recursively add AST nodes to the Graphviz graph."""
        if node is None:
            return ""

        _counter[0] += 1
        node_id = f"n{_counter[0]}"
        label = node.__class__.__name__.replace("Node", "")

        # Add node-specific info to label
        if hasattr(node, "name") and isinstance(node.name, str) and node.name:
            label += f"\n{node.name}"
        if hasattr(node, "op") and isinstance(node.op, str) and node.op:
            label += f"\n[{node.op}]"
        if hasattr(node, "value") and isinstance(node.value, (int, float, str, bool)):
            val = str(node.value)
            if len(val) > 20:
                val = val[:17] + "..."
            label += f"\n={val}"
        if hasattr(node, "var_type") and isinstance(node.var_type, str) and node.var_type:
            label += f"\n:{node.var_type}"

        # Color coding by node type
        colors = {
            "ProgramNode": "#89b4fa",
            "FunctionDeclNode": "#a6e3a1",
            "IfNode": "#f9e2af",
            "RepeatNode": "#fab387",
            "VarDeclNode": "#cba6f7",
            "AssignNode": "#cba6f7",
            "ShowNode": "#89dceb",
            "ReadNode": "#89dceb",
            "BinOpNode": "#f38ba8",
            "ComparisonNode": "#f38ba8",
            "LogicalNode": "#f38ba8",
            "NumberLitNode": "#94e2d5",
            "DecimalLitNode": "#94e2d5",
            "StringLitNode": "#94e2d5",
            "BoolLitNode": "#94e2d5",
            "IdentifierNode": "#b4befe",
            "FunctionCallNode": "#a6e3a1",
            "ReturnNode": "#eba0ac",
        }
        fill_color = colors.get(node.__class__.__name__, "#313244")
        node_font_color = "#11111b" if fill_color != "#313244" else "#cdd6f4"

        dot.node(node_id, label, fillcolor=fill_color, fontcolor=node_font_color)

        if parent_id:
            dot.edge(parent_id, node_id)

        # Recurse into children
        for key, value in vars(node).items():
            if key.startswith("_") or key in ("line", "column"):
                continue
            if isinstance(value, list):
                for item in value:
                    if hasattr(item, "__class__") and hasattr(item, "line"):
                        add_node(item, node_id)
            elif hasattr(value, "__class__") and hasattr(value, "line"):
                add_node(value, node_id)

        return node_id

    add_node(ast_node)

    # Render to file
    try:
        graph_dir = get_graph_dir()
        ensure_directory(graph_dir)
        output_path = os.path.join(graph_dir, filename)
        dot.render(output_path, cleanup=True)

        # Read PNG and return as base64
        png_path = output_path + ".png"
        if os.path.exists(png_path):
            with open(png_path, "rb") as f:
                return base64.b64encode(f.read()).decode("utf-8")
    except Exception:
        pass

    return None


# ═════════════════════════════════════════════════════════════
# API ROUTES
# ═════════════════════════════════════════════════════════════

@app.route("/compile", methods=["POST"])
def compile_code() -> Any:
    """Full compilation pipeline: Lex → Parse → Semantic → IR → CodeGen.
    
    Request JSON: { "code": "start ... end" }
    Returns all compilation artifacts and statistics.
    """
    data = request.get_json()
    if not data or "code" not in data:
        return jsonify({"error": "No code provided"}), 400

    source = data["code"]
    all_errors: List[Dict[str, Any]] = []
    stats: Dict[str, Any] = {}
    total_start = time.perf_counter()

    # Ensure output directories exist
    ensure_directory(get_generated_dir())
    ensure_directory(get_graph_dir())

    # ── Phase 1: Lexical Analysis ───────────────────────────
    phase_start = time.perf_counter()
    lexer = QXLLexer()
    tokens, lex_errors = lexer.tokenize(source)
    stats["lexer_ms"] = round((time.perf_counter() - phase_start) * 1000, 2)
    stats["token_count"] = len(tokens)
    _state["tokens"] = tokens
    all_errors.extend(lex_errors.to_list())

    # ── Phase 2: Syntax Analysis ────────────────────────────
    phase_start = time.perf_counter()
    parser = QXLParser()
    # Re-tokenize for parser (PLY requires its own lexer instance)
    parse_lexer = QXLLexer()
    ast, parse_errors = parser.parse(source, parse_lexer)
    stats["parser_ms"] = round((time.perf_counter() - phase_start) * 1000, 2)
    _state["ast"] = ast
    _state["ast_json"] = serialize_ast(ast) if ast else None
    all_errors.extend(parse_errors.to_list())

    # Stop if parsing failed
    if ast is None or parse_errors.has_errors():
        stats["total_ms"] = round((time.perf_counter() - total_start) * 1000, 2)
        _state["errors"] = all_errors
        _state["statistics"] = stats

        _record_history(source, False, len(all_errors), len(tokens), stats["total_ms"])

        return jsonify({
            "success": False,
            "errors": all_errors,
            "tokens": tokens,
            "statistics": stats,
            "ast": None,
            "symbol_table": None,
            "intermediate": "",
            "generated_python": "",
        })

    # ── Phase 3: Semantic Analysis ──────────────────────────
    phase_start = time.perf_counter()
    analyzer = SemanticAnalyzer()
    symbol_table, sem_errors = analyzer.analyze(ast)
    stats["semantic_ms"] = round((time.perf_counter() - phase_start) * 1000, 2)
    _state["symbol_table"] = symbol_table.to_dict()
    all_errors.extend(sem_errors.to_list())

    # Stop if semantic errors
    if sem_errors.has_errors():
        stats["total_ms"] = round((time.perf_counter() - total_start) * 1000, 2)
        _state["errors"] = all_errors
        _state["statistics"] = stats

        _record_history(source, False, len(all_errors), len(tokens), stats["total_ms"])

        return jsonify({
            "success": False,
            "errors": all_errors,
            "tokens": tokens,
            "ast": _state["ast_json"],
            "symbol_table": _state["symbol_table"],
            "statistics": stats,
            "intermediate": "",
            "generated_python": "",
        })

    # ── Phase 4: Intermediate Code Generation ───────────────
    phase_start = time.perf_counter()
    ir_gen = IRGenerator()
    ir_instructions, ir_errors = ir_gen.generate(ast)
    ir_text = ir_gen.get_tac_text()
    ir_gen.save_to_file()
    stats["ir_ms"] = round((time.perf_counter() - phase_start) * 1000, 2)
    stats["ir_instruction_count"] = len(ir_instructions)
    _state["intermediate"] = ir_text
    all_errors.extend(ir_errors.to_list())

    # ── Phase 5: Python Code Generation ─────────────────────
    phase_start = time.perf_counter()
    codegen = PythonGenerator()
    python_code, gen_errors = codegen.generate(ast)
    codegen.save_to_file()
    stats["codegen_ms"] = round((time.perf_counter() - phase_start) * 1000, 2)
    _state["generated_python"] = python_code
    all_errors.extend(gen_errors.to_list())

    # ── Phase 6: Parse Tree Visualization ───────────────────
    phase_start = time.perf_counter()
    parse_tree_b64 = generate_tree_image(ast, "parse_tree")
    ast_b64 = generate_tree_image(ast, "ast")
    stats["visualization_ms"] = round((time.perf_counter() - phase_start) * 1000, 2)
    _state["parse_tree_png"] = parse_tree_b64
    _state["ast_png"] = ast_b64

    # ── Finalize ────────────────────────────────────────────
    stats["total_ms"] = round((time.perf_counter() - total_start) * 1000, 2)
    _state["errors"] = all_errors
    _state["statistics"] = stats

    success = not any(e.get("severity") == "error" for e in all_errors)

    _record_history(source, success, len(all_errors), len(tokens), stats["total_ms"])

    return jsonify({
        "success": success,
        "errors": all_errors,
        "tokens": tokens,
        "ast": _state["ast_json"],
        "symbol_table": _state["symbol_table"],
        "intermediate": ir_text,
        "generated_python": python_code,
        "parse_tree": parse_tree_b64,
        "ast_image": ast_b64,
        "statistics": stats,
    })


@app.route("/run", methods=["POST"])
def run_code() -> Any:
    """Execute the generated Python code.
    
    Request JSON: { "input": "optional stdin input" }
    """
    data = request.get_json() or {}
    user_input = data.get("input", "")

    executor = QXLExecutor(timeout=10)
    result = executor.execute(user_input=user_input)

    return jsonify(result)


# ── Cached Result Endpoints ─────────────────────────────────

@app.route("/tokens", methods=["GET"])
def get_tokens() -> Any:
    """Return the token list from the last compilation."""
    return jsonify({"tokens": _state["tokens"]})


@app.route("/ast", methods=["GET"])
def get_ast() -> Any:
    """Return the AST as a JSON tree."""
    return jsonify({"ast": _state["ast_json"]})


@app.route("/symbol-table", methods=["GET"])
def get_symbol_table() -> Any:
    """Return the symbol table."""
    return jsonify({"symbol_table": _state["symbol_table"]})


@app.route("/intermediate", methods=["GET"])
def get_intermediate() -> Any:
    """Return the three-address code."""
    return jsonify({"intermediate": _state["intermediate"]})


@app.route("/generated-python", methods=["GET"])
def get_generated_python() -> Any:
    """Return the generated Python source code."""
    return jsonify({"generated_python": _state["generated_python"]})


@app.route("/parse-tree", methods=["GET"])
def get_parse_tree() -> Any:
    """Return the parse tree image as base64 PNG."""
    return jsonify({"parse_tree": _state["parse_tree_png"]})


# ── Program Storage ─────────────────────────────────────────

@app.route("/programs", methods=["GET"])
def list_programs() -> Any:
    """List all saved programs."""
    conn = get_db()
    programs = conn.execute(
        "SELECT id, name, created_at, updated_at FROM programs ORDER BY updated_at DESC"
    ).fetchall()
    conn.close()
    return jsonify({"programs": [dict(p) for p in programs]})


@app.route("/programs", methods=["POST"])
def save_program() -> Any:
    """Save a program."""
    data = request.get_json()
    if not data or "name" not in data or "code" not in data:
        return jsonify({"error": "Name and code required"}), 400

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO programs (name, code) VALUES (?, ?)",
        (data["name"], data["code"])
    )
    conn.commit()
    program_id = cursor.lastrowid
    conn.close()

    return jsonify({"id": program_id, "message": "Program saved"})


@app.route("/programs/<int:program_id>", methods=["GET"])
def load_program(program_id: int) -> Any:
    """Load a saved program by ID."""
    conn = get_db()
    program = conn.execute(
        "SELECT * FROM programs WHERE id = ?", (program_id,)
    ).fetchone()
    conn.close()

    if program is None:
        return jsonify({"error": "Program not found"}), 404

    return jsonify(dict(program))


# ── Sample Programs ─────────────────────────────────────────

@app.route("/examples", methods=["GET"])
def list_examples() -> Any:
    """List all sample programs."""
    conn = get_db()
    examples = conn.execute(
        "SELECT id, name, description FROM sample_programs ORDER BY name"
    ).fetchall()
    conn.close()
    return jsonify({"examples": [dict(e) for e in examples]})


@app.route("/examples/<name>", methods=["GET"])
def load_example(name: str) -> Any:
    """Load a sample program by name."""
    conn = get_db()
    example = conn.execute(
        "SELECT * FROM sample_programs WHERE name = ?", (name,)
    ).fetchone()
    conn.close()

    if example is None:
        # Try loading from file
        filepath = os.path.join(EXAMPLES_DIR, f"{name}.qxl")
        if os.path.exists(filepath):
            code = read_file(filepath)
            return jsonify({"name": name, "code": code})
        return jsonify({"error": "Example not found"}), 404

    return jsonify(dict(example))


# ── Compilation History ─────────────────────────────────────

@app.route("/history", methods=["GET"])
def get_history() -> Any:
    """Return compilation history."""
    conn = get_db()
    history = conn.execute(
        "SELECT * FROM compilation_history ORDER BY created_at DESC LIMIT 50"
    ).fetchall()
    conn.close()
    return jsonify({"history": [dict(h) for h in history]})


def _record_history(source: str, success: bool, error_count: int,
                    token_count: int, compilation_time: float) -> None:
    """Record a compilation run in the history table."""
    try:
        conn = get_db()
        conn.execute(
            """INSERT INTO compilation_history 
               (source_code, success, error_count, token_count, compilation_time_ms)
               VALUES (?, ?, ?, ?, ?)""",
            (source[:5000], int(success), error_count, token_count, compilation_time)
        )
        conn.commit()
        conn.close()
    except Exception:
        pass  # Don't let history recording break compilation


# ═════════════════════════════════════════════════════════════
# SERVER STARTUP
# ═════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("================================================")
    print("    QXL Compiler Server                         ")
    print("    QuadX Programming Language                  ")
    print("    http://localhost:5000                       ")
    print("================================================")

    app.run(debug=False, host="0.0.0.0", port=5000)
