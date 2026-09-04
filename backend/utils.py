"""
QXL Utility Functions
=====================
Shared helpers for timing, serialization, and file I/O
used across all compiler modules.
"""

from __future__ import annotations

import json
import os
import time
import functools
from typing import Any, Callable, Dict


def timer(func: Callable) -> Callable:
    """Decorator that measures execution time of a function.
    
    Returns a tuple of (result, elapsed_ms) so callers can
    report compilation statistics per phase.
    
    Example:
        >>> @timer
        ... def lex(source): ...
        >>> tokens, elapsed = lex("start end")
    """
    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> tuple:
        start = time.perf_counter()
        result = func(*args, **kwargs)
        elapsed_ms = (time.perf_counter() - start) * 1000
        return result, round(elapsed_ms, 2)
    return wrapper


def ensure_directory(path: str) -> None:
    """Create directory (and parents) if it does not exist."""
    os.makedirs(path, exist_ok=True)


def write_file(filepath: str, content: str) -> None:
    """Write content to file, creating parent directories as needed."""
    ensure_directory(os.path.dirname(filepath))
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)


def read_file(filepath: str) -> str:
    """Read and return file contents, or empty string if missing."""
    if not os.path.exists(filepath):
        return ""
    with open(filepath, "r", encoding="utf-8") as f:
        return f.read()


def serialize_ast(node: Any) -> Dict[str, Any]:
    """Recursively serialize an AST node to a JSON-compatible dict.
    
    Handles nested nodes, lists of nodes, and primitive values.
    Used by the /ast API endpoint.
    """
    if node is None:
        return None

    if isinstance(node, list):
        return [serialize_ast(item) for item in node]

    if isinstance(node, (int, float, str, bool)):
        return node

    # AST node — serialize all attributes
    result: Dict[str, Any] = {
        "node_type": node.__class__.__name__
    }

    for key, value in vars(node).items():
        if key.startswith("_"):
            continue
        if hasattr(value, "__class__") and hasattr(value, "__dict__") and \
                not isinstance(value, (int, float, str, bool, type(None))):
            result[key] = serialize_ast(value)
        elif isinstance(value, list):
            result[key] = [serialize_ast(v) for v in value]
        else:
            result[key] = value

    return result


def format_token_table(tokens: list) -> str:
    """Format token list as a human-readable table string."""
    if not tokens:
        return "No tokens generated."

    header = f"{'Type':<20} {'Value':<25} {'Line':<6} {'Col':<6}"
    separator = "-" * 60
    lines = [header, separator]

    for tok in tokens:
        t = tok.get("type", "")
        v = str(tok.get("value", ""))
        if len(v) > 22:
            v = v[:19] + "..."
        ln = str(tok.get("line", ""))
        col = str(tok.get("column", ""))
        lines.append(f"{t:<20} {v:<25} {ln:<6} {col:<6}")

    return "\n".join(lines)


def get_project_root() -> str:
    """Return the absolute path to the project root directory."""
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def get_generated_dir() -> str:
    """Return the path to the generated/ output directory."""
    return os.path.join(get_project_root(), ".generated")


def get_graph_dir() -> str:
    """Return the path to the graph/ output directory."""
    return os.path.join(get_project_root(), ".graph")
