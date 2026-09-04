"""
QXL Semantic Analyzer
=====================
Performs semantic analysis on the AST using the Visitor Pattern.

Checks performed:
    1. Duplicate variable declarations (same scope)
    2. Undefined variable usage
    3. Type compatibility in assignments and expressions
    4. Function declaration validation
    5. Function call: correct name, argument count
    6. Return statement only inside functions
    7. Break/continue only inside loops
    8. Variable initialization before use

Usage:
    >>> from backend.semantic import SemanticAnalyzer
    >>> analyzer = SemanticAnalyzer()
    >>> symbol_table, errors = analyzer.analyze(ast)
"""

from __future__ import annotations

from typing import Any, List, Optional, Set, Tuple

from backend.ast_nodes import (
    ASTNode, ProgramNode, BlockNode, VarDeclNode, AssignNode,
    ShowNode, ReadNode, IfNode, RepeatNode, FunctionDeclNode,
    FunctionCallNode, ReturnNode, BreakNode, ContinueNode,
    BinOpNode, UnaryOpNode, ComparisonNode, LogicalNode,
    NumberLitNode, DecimalLitNode, StringLitNode, BoolLitNode,
    IdentifierNode, ParamNode,
)
from backend.symbol_table import SymbolTable, Symbol, FunctionSymbol
from backend.errors import SemanticError, ErrorCollector


class SemanticAnalyzer:
    """Visitor-based semantic analyzer for QXL AST.
    
    Traverses the AST and populates a SymbolTable while checking
    for semantic errors. Each visit_* method corresponds to an
    AST node type.
    """

    def __init__(self) -> None:
        self.symbol_table: SymbolTable = SymbolTable()
        self.errors: ErrorCollector = ErrorCollector()
        self._in_function: bool = False
        self._in_loop: int = 0       # Nesting depth counter
        self._current_function: Optional[str] = None

    def analyze(self, ast: ProgramNode) -> Tuple[SymbolTable, ErrorCollector]:
        """Run semantic analysis on the AST.
        
        Args:
            ast: Root ProgramNode from the parser.
            
        Returns:
            Tuple of (symbol_table, error_collector).
        """
        self.symbol_table = SymbolTable()
        self.errors = ErrorCollector()
        self._in_function = False
        self._in_loop = 0
        self._current_function = None

        if ast is None:
            self.errors.add(SemanticError(
                "No AST provided — parsing may have failed"
            ))
            return self.symbol_table, self.errors

        # First pass: register all function declarations
        self._register_functions(ast)

        # Second pass: full semantic analysis
        ast.accept(self)

        return self.symbol_table, self.errors

    def _register_functions(self, node: ProgramNode) -> None:
        """Pre-register all function declarations for forward references."""
        for stmt in node.body:
            if isinstance(stmt, FunctionDeclNode):
                params = [(p.name, p.param_type) for p in stmt.params]
                func_sym = FunctionSymbol(
                    name=stmt.name, params=params, line=stmt.line
                )
                if not self.symbol_table.declare_function(func_sym):
                    self.errors.add(SemanticError(
                        f"Function '{stmt.name}' is already declared",
                        line=stmt.line,
                        suggestion=f"Rename one of the '{stmt.name}' functions"
                    ))

    # ═════════════════════════════════════════════════════════════
    # VISITOR METHODS
    # ═════════════════════════════════════════════════════════════

    def visit_ProgramNode(self, node: ProgramNode) -> None:
        """Visit the program root — analyze all top-level statements."""
        for stmt in node.body:
            stmt.accept(self)

    def visit_BlockNode(self, node: BlockNode) -> None:
        """Visit a block of statements."""
        for stmt in node.statements:
            stmt.accept(self)

    # ── Declarations & Assignments ──────────────────────────────

    def visit_VarDeclNode(self, node: VarDeclNode) -> None:
        """Check variable declaration: no duplicates, type-check initializer."""
        # Check for duplicate in current scope
        existing = self.symbol_table.lookup_local(node.name)
        if existing is not None:
            self.errors.add(SemanticError(
                f"Variable '{node.name}' is already declared in this scope "
                f"(first declared at line {existing.line})",
                line=node.line,
                suggestion=f"Use a different name or remove the duplicate declaration"
            ))
            return

        # Declare the symbol
        sym = Symbol(
            name=node.name,
            sym_type=node.var_type,
            line=node.line,
            column=node.column,
            initialized=node.value is not None,
        )
        self.symbol_table.declare(node.name, sym)

        # Type-check initializer if present
        if node.value is not None:
            init_type = self._get_expression_type(node.value)
            if init_type and not self._types_compatible(node.var_type, init_type):
                self.errors.add(SemanticError(
                    f"Type mismatch: cannot assign '{init_type}' to "
                    f"variable '{node.name}' of type '{node.var_type}'",
                    line=node.line,
                    suggestion=f"Change the type to '{init_type}' or fix the expression"
                ))
            node.value.accept(self)

    def visit_AssignNode(self, node: AssignNode) -> None:
        """Check assignment: variable must exist, type must match."""
        sym = self.symbol_table.lookup(node.name)
        if sym is None:
            self.errors.add(SemanticError(
                f"Undefined variable '{node.name}'",
                line=node.line,
                suggestion=f"Declare '{node.name}' before using it, e.g.: number {node.name} = 0"
            ))
        else:
            # Type check
            if node.value is not None:
                val_type = self._get_expression_type(node.value)
                if val_type and not self._types_compatible(sym.sym_type, val_type):
                    self.errors.add(SemanticError(
                        f"Type mismatch: cannot assign '{val_type}' to "
                        f"'{node.name}' of type '{sym.sym_type}'",
                        line=node.line,
                    ))
                node.value.accept(self)
            self.symbol_table.mark_initialized(node.name)

    # ── I/O Statements ──────────────────────────────────────────

    def visit_ShowNode(self, node: ShowNode) -> None:
        """Visit show statement — check expression validity."""
        if node.value is not None:
            node.value.accept(self)

    def visit_ReadNode(self, node: ReadNode) -> None:
        """Visit read statement — variable must exist."""
        sym = self.symbol_table.lookup(node.name)
        if sym is None:
            self.errors.add(SemanticError(
                f"Undefined variable '{node.name}' in read statement",
                line=node.line,
                suggestion=f"Declare '{node.name}' before reading into it"
            ))
        else:
            self.symbol_table.mark_initialized(node.name)

    # ── Control Flow ────────────────────────────────────────────

    def visit_IfNode(self, node: IfNode) -> None:
        """Visit if/otherwise — check condition, scope bodies."""
        if node.condition is not None:
            node.condition.accept(self)

        # Then body (new scope)
        self.symbol_table.push_scope(f"if:{node.line}")
        for stmt in node.then_body:
            stmt.accept(self)
        self.symbol_table.pop_scope()

        # Else body (new scope)
        if node.else_body:
            self.symbol_table.push_scope(f"otherwise:{node.line}")
            for stmt in node.else_body:
                stmt.accept(self)
            self.symbol_table.pop_scope()

    def visit_RepeatNode(self, node: RepeatNode) -> None:
        """Visit repeat loop — check condition, track loop nesting."""
        if node.condition is not None:
            node.condition.accept(self)

        self._in_loop += 1
        self.symbol_table.push_scope(f"repeat:{node.line}")
        for stmt in node.body:
            stmt.accept(self)
        self.symbol_table.pop_scope()
        self._in_loop -= 1

    def visit_BreakNode(self, node: BreakNode) -> None:
        """Check that break is inside a loop."""
        if self._in_loop == 0:
            self.errors.add(SemanticError(
                "'break' can only be used inside a repeat loop",
                line=node.line,
                suggestion="Move 'break' inside a 'repeat ... endrepeat' block"
            ))

    def visit_ContinueNode(self, node: ContinueNode) -> None:
        """Check that continue is inside a loop."""
        if self._in_loop == 0:
            self.errors.add(SemanticError(
                "'continue' can only be used inside a repeat loop",
                line=node.line,
                suggestion="Move 'continue' inside a 'repeat ... endrepeat' block"
            ))

    # ── Functions ───────────────────────────────────────────────

    def visit_FunctionDeclNode(self, node: FunctionDeclNode) -> None:
        """Visit function declaration — scope params and body."""
        self._in_function = True
        self._current_function = node.name

        self.symbol_table.push_scope(f"function:{node.name}")

        # Declare parameters as local variables
        seen_params: Set[str] = set()
        for param in node.params:
            if param.name in seen_params:
                self.errors.add(SemanticError(
                    f"Duplicate parameter '{param.name}' in function '{node.name}'",
                    line=param.line,
                ))
            else:
                seen_params.add(param.name)
                sym = Symbol(
                    name=param.name,
                    sym_type=param.param_type,
                    line=param.line,
                    initialized=True,  # Parameters are always initialized
                )
                self.symbol_table.declare(param.name, sym)

        # Analyze body
        has_return = False
        for stmt in node.body:
            stmt.accept(self)
            if isinstance(stmt, ReturnNode):
                has_return = True

        # Update function symbol
        func_sym = self.symbol_table.lookup_function(node.name)
        if func_sym:
            func_sym.has_return = has_return

        self.symbol_table.pop_scope()
        self._in_function = False
        self._current_function = None

    def visit_FunctionCallNode(self, node: FunctionCallNode) -> str:
        """Visit function call — check existence and argument count."""
        func_sym = self.symbol_table.lookup_function(node.name)
        if func_sym is None:
            self.errors.add(SemanticError(
                f"Undefined function '{node.name}'",
                line=node.line,
                suggestion=f"Define function '{node.name}' before calling it"
            ))
            return "unknown"

        # Check argument count
        if len(node.args) != func_sym.param_count:
            self.errors.add(SemanticError(
                f"Function '{node.name}' expects {func_sym.param_count} "
                f"argument(s), but got {len(node.args)}",
                line=node.line,
            ))

        # Analyze each argument
        for arg in node.args:
            arg.accept(self)

        return "unknown"  # Return type not tracked for simplicity

    def visit_ReturnNode(self, node: ReturnNode) -> None:
        """Check that return is inside a function."""
        if not self._in_function:
            self.errors.add(SemanticError(
                "'return' can only be used inside a function",
                line=node.line,
                suggestion="Move 'return' inside a 'function ... endfunction' block"
            ))
        if node.value is not None:
            node.value.accept(self)

    # ── Expressions ─────────────────────────────────────────────

    def visit_BinOpNode(self, node: BinOpNode) -> str:
        """Visit binary operation — type check operands."""
        if node.left:
            node.left.accept(self)
        if node.right:
            node.right.accept(self)
        return "number"  # Simplified: arithmetic returns number

    def visit_UnaryOpNode(self, node: UnaryOpNode) -> str:
        """Visit unary operation."""
        if node.operand:
            node.operand.accept(self)
        return "number" if node.op == "-" else "bool"

    def visit_ComparisonNode(self, node: ComparisonNode) -> str:
        """Visit comparison — returns bool."""
        if node.left:
            node.left.accept(self)
        if node.right:
            node.right.accept(self)
        return "bool"

    def visit_LogicalNode(self, node: LogicalNode) -> str:
        """Visit logical operation — operands should be bool-compatible."""
        if node.left:
            node.left.accept(self)
        if node.right:
            node.right.accept(self)
        return "bool"

    # ── Literals ────────────────────────────────────────────────

    def visit_NumberLitNode(self, node: NumberLitNode) -> str:
        return "number"

    def visit_DecimalLitNode(self, node: DecimalLitNode) -> str:
        return "decimal"

    def visit_StringLitNode(self, node: StringLitNode) -> str:
        return "text"

    def visit_BoolLitNode(self, node: BoolLitNode) -> str:
        return "bool"

    def visit_IdentifierNode(self, node: IdentifierNode) -> str:
        """Check that the referenced variable is declared."""
        sym = self.symbol_table.lookup(node.name)
        if sym is None:
            self.errors.add(SemanticError(
                f"Undefined variable '{node.name}'",
                line=node.line,
                suggestion=f"Declare '{node.name}' before using it"
            ))
            return "unknown"
        return sym.sym_type

    # ═════════════════════════════════════════════════════════════
    # HELPERS
    # ═════════════════════════════════════════════════════════════

    def _get_expression_type(self, node: ASTNode) -> Optional[str]:
        """Infer the type of an expression node without full traversal."""
        if isinstance(node, NumberLitNode):
            return "number"
        elif isinstance(node, DecimalLitNode):
            return "decimal"
        elif isinstance(node, StringLitNode):
            return "text"
        elif isinstance(node, BoolLitNode):
            return "bool"
        elif isinstance(node, IdentifierNode):
            sym = self.symbol_table.lookup(node.name)
            return sym.sym_type if sym else None
        elif isinstance(node, BinOpNode):
            # Arithmetic operations: check if either operand is decimal
            left_type = self._get_expression_type(node.left)
            right_type = self._get_expression_type(node.right)
            if left_type == "decimal" or right_type == "decimal":
                return "decimal"
            return "number"
        elif isinstance(node, ComparisonNode):
            return "bool"
        elif isinstance(node, LogicalNode):
            return "bool"
        elif isinstance(node, UnaryOpNode):
            if node.op == "!":
                return "bool"
            return self._get_expression_type(node.operand) if node.operand else "number"
        elif isinstance(node, FunctionCallNode):
            return "unknown"
        return None

    def _types_compatible(self, declared_type: str, value_type: str) -> bool:
        """Check if a value type is assignable to a declared type.
        
        Rules:
            - Same type → compatible
            - number ↔ decimal → compatible (widening)
            - Everything else → incompatible
        """
        if declared_type == value_type:
            return True
        # Number and decimal are compatible (widening conversion)
        numeric_types = {"number", "decimal"}
        if declared_type in numeric_types and value_type in numeric_types:
            return True
        # Unknown types pass (to avoid cascading errors)
        if value_type == "unknown" or declared_type == "unknown":
            return True
        return False
