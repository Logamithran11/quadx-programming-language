"""
QXL Abstract Syntax Tree Node Definitions
==========================================
Defines every AST node type used by the QXL compiler.

Each node implements the Visitor Pattern via an `accept(visitor)` method,
enabling clean separation between tree structure and tree operations
(semantic analysis, IR generation, code generation).

Node Hierarchy:
    ASTNode (base)
    ├── ProgramNode          — Root: contains list of statements
    ├── BlockNode            — Sequence of statements
    ├── VarDeclNode          — Variable declaration
    ├── AssignNode           — Variable assignment
    ├── ShowNode             — Output statement
    ├── ReadNode             — Input statement
    ├── IfNode               — If/otherwise conditional
    ├── RepeatNode           — Loop construct
    ├── FunctionDeclNode     — Function definition
    ├── FunctionCallNode     — Function invocation
    ├── ReturnNode           — Return from function
    ├── BreakNode            — Loop break
    ├── ContinueNode         — Loop continue
    ├── BinOpNode            — Binary operation
    ├── UnaryOpNode          — Unary operation
    ├── ComparisonNode       — Comparison operation
    ├── LogicalNode          — Logical AND/OR
    ├── NumberLitNode        — Integer literal
    ├── DecimalLitNode       — Float literal
    ├── StringLitNode        — String literal
    ├── BoolLitNode          — Boolean literal
    └── IdentifierNode       — Variable reference
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, List, Optional


# ─────────────────────────────────────────────────────────────
# Base Node
# ─────────────────────────────────────────────────────────────

@dataclass
class ASTNode:
    """Base class for all AST nodes.
    
    Attributes:
        line: Source line number (1-indexed) for error reporting.
        column: Source column number (1-indexed) for error reporting.
    """
    line: int = 0
    column: int = 0

    def accept(self, visitor: Any) -> Any:
        """Dispatch to the visitor's corresponding visit_* method.
        
        Uses the class name to resolve the method dynamically:
            ProgramNode → visitor.visit_ProgramNode(self)
        """
        method_name = f"visit_{self.__class__.__name__}"
        visitor_method = getattr(visitor, method_name, None)
        if visitor_method is None:
            raise NotImplementedError(
                f"Visitor {visitor.__class__.__name__} does not implement {method_name}"
            )
        return visitor_method(self)


# ─────────────────────────────────────────────────────────────
# Program Structure Nodes
# ─────────────────────────────────────────────────────────────

@dataclass
class ProgramNode(ASTNode):
    """Root node: represents an entire QXL program.
    
    A valid program is wrapped in `start ... end`.
    Contains a list of top-level statements (including function declarations).
    """
    body: List[ASTNode] = field(default_factory=list)


@dataclass
class BlockNode(ASTNode):
    """A sequence of statements (used inside if/repeat/function bodies)."""
    statements: List[ASTNode] = field(default_factory=list)


# ─────────────────────────────────────────────────────────────
# Declaration & Assignment
# ─────────────────────────────────────────────────────────────

@dataclass
class VarDeclNode(ASTNode):
    """Variable declaration with type and optional initializer.
    
    QXL syntax:
        number x = 10
        text name = "Alice"
        decimal pi = 3.14
        bool flag = true
    """
    var_type: str = ""          # "number", "decimal", "text", "bool"
    name: str = ""              # Variable name
    value: Optional[ASTNode] = None   # Initializer expression (optional)


@dataclass
class AssignNode(ASTNode):
    """Variable assignment.
    
    QXL syntax:
        x = 42
        name = "Bob"
    """
    name: str = ""
    value: Optional[ASTNode] = None


# ─────────────────────────────────────────────────────────────
# I/O Statements
# ─────────────────────────────────────────────────────────────

@dataclass
class ShowNode(ASTNode):
    """Output statement — prints a value to console.
    
    QXL syntax:
        show "Hello, World!"
        show x + y
    """
    value: Optional[ASTNode] = None


@dataclass
class ReadNode(ASTNode):
    """Input statement — reads user input into a variable.
    
    QXL syntax:
        read x
    """
    name: str = ""


# ─────────────────────────────────────────────────────────────
# Control Flow
# ─────────────────────────────────────────────────────────────

@dataclass
class IfNode(ASTNode):
    """If/otherwise conditional.
    
    QXL syntax:
        if condition
            ...
        otherwise
            ...
        endif
    """
    condition: Optional[ASTNode] = None
    then_body: List[ASTNode] = field(default_factory=list)
    else_body: List[ASTNode] = field(default_factory=list)


@dataclass
class RepeatNode(ASTNode):
    """Loop construct.
    
    QXL syntax (while-style):
        repeat condition
            ...
        endrepeat
    """
    condition: Optional[ASTNode] = None
    body: List[ASTNode] = field(default_factory=list)


@dataclass
class BreakNode(ASTNode):
    """Break out of the nearest enclosing loop."""
    pass


@dataclass
class ContinueNode(ASTNode):
    """Skip to next iteration of the nearest enclosing loop."""
    pass


# ─────────────────────────────────────────────────────────────
# Functions
# ─────────────────────────────────────────────────────────────

@dataclass
class FunctionDeclNode(ASTNode):
    """Function declaration.
    
    QXL syntax:
        function add(number a, number b)
            return a + b
        endfunction
    """
    name: str = ""
    params: List[ParamNode] = field(default_factory=list)
    body: List[ASTNode] = field(default_factory=list)


@dataclass
class ParamNode(ASTNode):
    """Function parameter with type annotation.
    
    Example: `number x` in `function foo(number x)`
    """
    param_type: str = ""    # "number", "decimal", "text", "bool"
    name: str = ""


@dataclass
class FunctionCallNode(ASTNode):
    """Function call expression.
    
    QXL syntax:
        add(1, 2)
        show factorial(5)
    """
    name: str = ""
    args: List[ASTNode] = field(default_factory=list)


@dataclass
class ReturnNode(ASTNode):
    """Return statement inside a function.
    
    QXL syntax:
        return x + y
        return
    """
    value: Optional[ASTNode] = None


# ─────────────────────────────────────────────────────────────
# Expressions
# ─────────────────────────────────────────────────────────────

@dataclass
class BinOpNode(ASTNode):
    """Binary arithmetic operation.
    
    Operators: +, -, *, /, %
    """
    op: str = ""                      # "+", "-", "*", "/", "%"
    left: Optional[ASTNode] = None
    right: Optional[ASTNode] = None


@dataclass
class UnaryOpNode(ASTNode):
    """Unary operation.
    
    Operators: -, !
    """
    op: str = ""          # "-" (negation), "!" (logical not)
    operand: Optional[ASTNode] = None


@dataclass
class ComparisonNode(ASTNode):
    """Comparison operation.
    
    Operators: >, <, >=, <=, ==, !=
    """
    op: str = ""
    left: Optional[ASTNode] = None
    right: Optional[ASTNode] = None


@dataclass
class LogicalNode(ASTNode):
    """Logical operation.
    
    Operators: && (AND), || (OR)
    """
    op: str = ""          # "&&", "||"
    left: Optional[ASTNode] = None
    right: Optional[ASTNode] = None


# ─────────────────────────────────────────────────────────────
# Literals
# ─────────────────────────────────────────────────────────────

@dataclass
class NumberLitNode(ASTNode):
    """Integer literal.  Example: 42"""
    value: int = 0


@dataclass
class DecimalLitNode(ASTNode):
    """Floating-point literal.  Example: 3.14"""
    value: float = 0.0


@dataclass
class StringLitNode(ASTNode):
    """String literal.  Example: "Hello" """
    value: str = ""


@dataclass
class BoolLitNode(ASTNode):
    """Boolean literal.  Example: true, false"""
    value: bool = False


# ─────────────────────────────────────────────────────────────
# Identifier
# ─────────────────────────────────────────────────────────────

@dataclass
class IdentifierNode(ASTNode):
    """Variable reference by name.  Example: x, total"""
    name: str = ""
