"""
QXL Intermediate Code Generator
================================
Generates Three-Address Code (TAC) from the QXL AST using the Visitor Pattern.

Three-Address Code is a linear intermediate representation where each
instruction has at most three operands. This makes optimization and
target code generation straightforward.

Instruction format:
    result = arg1 OP arg2     (binary operation)
    result = OP arg1          (unary operation)
    result = arg1             (copy/assignment)
    LABEL Ln                  (label)
    GOTO Ln                   (unconditional jump)
    IF_FALSE arg1 GOTO Ln     (conditional jump)
    PARAM arg1                (function parameter)
    CALL func, n              (function call with n args)
    RETURN arg1               (return from function)
    PRINT arg1                (output)
    READ result               (input)

Usage:
    >>> from backend.intermediate import IRGenerator
    >>> ir_gen = IRGenerator()
    >>> tac_code, errors = ir_gen.generate(ast)
"""

from __future__ import annotations

import os
from typing import Any, List, Optional, Tuple

from backend.ast_nodes import (
    ASTNode, ProgramNode, BlockNode, VarDeclNode, AssignNode,
    ShowNode, ReadNode, IfNode, RepeatNode, FunctionDeclNode,
    FunctionCallNode, ReturnNode, BreakNode, ContinueNode,
    BinOpNode, UnaryOpNode, ComparisonNode, LogicalNode,
    NumberLitNode, DecimalLitNode, StringLitNode, BoolLitNode,
    IdentifierNode,
)
from backend.errors import ErrorCollector, CodeGenError
from backend.utils import get_generated_dir, write_file


class IRInstruction:
    """Represents a single Three-Address Code instruction.
    
    Attributes:
        op: Operation type (ADD, SUB, MUL, etc.)
        result: Destination variable/temp
        arg1: First operand
        arg2: Second operand (optional)
    """

    def __init__(self, op: str, result: str = "",
                 arg1: str = "", arg2: str = "") -> None:
        self.op = op
        self.result = result
        self.arg1 = arg1
        self.arg2 = arg2

    def __str__(self) -> str:
        if self.op == "LABEL":
            return f"{self.result}:"
        elif self.op == "GOTO":
            return f"    GOTO {self.result}"
        elif self.op == "IF_FALSE":
            return f"    IF_FALSE {self.arg1} GOTO {self.result}"
        elif self.op == "PARAM":
            return f"    PARAM {self.arg1}"
        elif self.op == "CALL":
            return f"    {self.result} = CALL {self.arg1}, {self.arg2}"
        elif self.op == "RETURN":
            if self.arg1:
                return f"    RETURN {self.arg1}"
            return "    RETURN"
        elif self.op == "PRINT":
            return f"    PRINT {self.arg1}"
        elif self.op == "READ":
            return f"    READ {self.result}"
        elif self.op == "ASSIGN":
            return f"    {self.result} = {self.arg1}"
        elif self.op == "FUNC_BEGIN":
            return f"\nFUNC_BEGIN {self.arg1}"
        elif self.op == "FUNC_END":
            return f"FUNC_END {self.arg1}"
        elif self.arg2:
            return f"    {self.result} = {self.arg1} {self.op} {self.arg2}"
        elif self.arg1:
            return f"    {self.result} = {self.op} {self.arg1}"
        else:
            return f"    {self.op} {self.result}"

    def to_dict(self) -> dict:
        """Serialize for API response."""
        return {
            "op": self.op,
            "result": self.result,
            "arg1": self.arg1,
            "arg2": self.arg2,
            "text": str(self),
        }


class IRGenerator:
    """Generates Three-Address Code from a QXL AST.
    
    Uses temporary variables (t1, t2, ...) for intermediate results
    and labels (L1, L2, ...) for control flow.
    """

    def __init__(self) -> None:
        self._temp_counter: int = 0
        self._label_counter: int = 0
        self._instructions: List[IRInstruction] = []
        self.errors: ErrorCollector = ErrorCollector()
        self._break_labels: List[str] = []     # Stack for break targets
        self._continue_labels: List[str] = []  # Stack for continue targets

    def _new_temp(self) -> str:
        """Generate a fresh temporary variable name."""
        self._temp_counter += 1
        return f"t{self._temp_counter}"

    def _new_label(self) -> str:
        """Generate a fresh label name."""
        self._label_counter += 1
        return f"L{self._label_counter}"

    def _emit(self, op: str, result: str = "",
              arg1: str = "", arg2: str = "") -> None:
        """Emit a single TAC instruction."""
        self._instructions.append(IRInstruction(op, result, arg1, arg2))

    # ═════════════════════════════════════════════════════════════
    # PUBLIC API
    # ═════════════════════════════════════════════════════════════

    def generate(self, ast: ProgramNode) -> Tuple[List[IRInstruction], ErrorCollector]:
        """Generate TAC from the AST.
        
        Returns:
            Tuple of (instructions, errors).
        """
        self._temp_counter = 0
        self._label_counter = 0
        self._instructions = []
        self.errors = ErrorCollector()
        self._break_labels = []
        self._continue_labels = []

        if ast is None:
            self.errors.add(CodeGenError("No AST provided for IR generation"))
            return self._instructions, self.errors

        self._visit(ast)
        return self._instructions, self.errors

    def get_tac_text(self) -> str:
        """Return the TAC as a formatted string."""
        return "\n".join(str(instr) for instr in self._instructions)

    def save_to_file(self) -> str:
        """Save TAC to generated/intermediate.txt and return the path."""
        filepath = os.path.join(get_generated_dir(), "intermediate.txt")
        write_file(filepath, self.get_tac_text())
        return filepath

    # ═════════════════════════════════════════════════════════════
    # VISITOR DISPATCH
    # ═════════════════════════════════════════════════════════════

    def _visit(self, node: ASTNode) -> str:
        """Dispatch to the appropriate visit method. Returns a temp/name."""
        method_name = f"_visit_{node.__class__.__name__}"
        method = getattr(self, method_name, None)
        if method is None:
            self.errors.add(CodeGenError(
                f"IR generator does not handle {node.__class__.__name__}",
                line=node.line
            ))
            return ""
        return method(node)

    # ═════════════════════════════════════════════════════════════
    # VISITOR METHODS
    # ═════════════════════════════════════════════════════════════

    def _visit_ProgramNode(self, node: ProgramNode) -> str:
        for stmt in node.body:
            self._visit(stmt)
        return ""

    def _visit_BlockNode(self, node: BlockNode) -> str:
        for stmt in node.statements:
            self._visit(stmt)
        return ""

    # ── Declarations & Assignments ──────────────────────────────

    def _visit_VarDeclNode(self, node: VarDeclNode) -> str:
        if node.value is not None:
            val = self._visit(node.value)
            self._emit("ASSIGN", node.name, val)
        return node.name

    def _visit_AssignNode(self, node: AssignNode) -> str:
        val = self._visit(node.value)
        self._emit("ASSIGN", node.name, val)
        return node.name

    # ── I/O ─────────────────────────────────────────────────────

    def _visit_ShowNode(self, node: ShowNode) -> str:
        val = self._visit(node.value)
        self._emit("PRINT", arg1=val)
        return ""

    def _visit_ReadNode(self, node: ReadNode) -> str:
        self._emit("READ", result=node.name)
        return node.name

    # ── Control Flow ────────────────────────────────────────────

    def _visit_IfNode(self, node: IfNode) -> str:
        cond = self._visit(node.condition)

        if node.else_body:
            # If-otherwise-endif
            else_label = self._new_label()
            end_label = self._new_label()

            self._emit("IF_FALSE", result=else_label, arg1=cond)
            for stmt in node.then_body:
                self._visit(stmt)
            self._emit("GOTO", result=end_label)
            self._emit("LABEL", result=else_label)
            for stmt in node.else_body:
                self._visit(stmt)
            self._emit("LABEL", result=end_label)
        else:
            # If-endif (no else)
            end_label = self._new_label()
            self._emit("IF_FALSE", result=end_label, arg1=cond)
            for stmt in node.then_body:
                self._visit(stmt)
            self._emit("LABEL", result=end_label)

        return ""

    def _visit_RepeatNode(self, node: RepeatNode) -> str:
        start_label = self._new_label()
        end_label = self._new_label()

        # Push break/continue targets
        self._break_labels.append(end_label)
        self._continue_labels.append(start_label)

        self._emit("LABEL", result=start_label)
        cond = self._visit(node.condition)
        self._emit("IF_FALSE", result=end_label, arg1=cond)

        for stmt in node.body:
            self._visit(stmt)

        self._emit("GOTO", result=start_label)
        self._emit("LABEL", result=end_label)

        # Pop break/continue targets
        self._break_labels.pop()
        self._continue_labels.pop()

        return ""

    def _visit_BreakNode(self, node: BreakNode) -> str:
        if self._break_labels:
            self._emit("GOTO", result=self._break_labels[-1])
        return ""

    def _visit_ContinueNode(self, node: ContinueNode) -> str:
        if self._continue_labels:
            self._emit("GOTO", result=self._continue_labels[-1])
        return ""

    # ── Functions ───────────────────────────────────────────────

    def _visit_FunctionDeclNode(self, node: FunctionDeclNode) -> str:
        self._emit("FUNC_BEGIN", arg1=node.name)
        for stmt in node.body:
            self._visit(stmt)
        self._emit("FUNC_END", arg1=node.name)
        return ""

    def _visit_FunctionCallNode(self, node: FunctionCallNode) -> str:
        # Emit parameters in order
        for arg in node.args:
            val = self._visit(arg)
            self._emit("PARAM", arg1=val)

        result = self._new_temp()
        self._emit("CALL", result=result, arg1=node.name,
                   arg2=str(len(node.args)))
        return result

    def _visit_ReturnNode(self, node: ReturnNode) -> str:
        if node.value is not None:
            val = self._visit(node.value)
            self._emit("RETURN", arg1=val)
        else:
            self._emit("RETURN")
        return ""

    # ── Expressions ─────────────────────────────────────────────

    def _visit_BinOpNode(self, node: BinOpNode) -> str:
        left = self._visit(node.left)
        right = self._visit(node.right)
        result = self._new_temp()

        op_map = {
            "+": "ADD", "-": "SUB", "*": "MUL",
            "/": "DIV", "%": "MOD",
        }
        self._emit(op_map.get(node.op, node.op), result, left, right)
        return result

    def _visit_UnaryOpNode(self, node: UnaryOpNode) -> str:
        operand = self._visit(node.operand)
        result = self._new_temp()

        if node.op == "-":
            self._emit("NEG", result, operand)
        elif node.op == "!":
            self._emit("NOT", result, operand)

        return result

    def _visit_ComparisonNode(self, node: ComparisonNode) -> str:
        left = self._visit(node.left)
        right = self._visit(node.right)
        result = self._new_temp()

        op_map = {
            ">": "GT", "<": "LT", ">=": "GTE", "<=": "LTE",
            "==": "EQ", "!=": "NEQ",
        }
        self._emit(op_map.get(node.op, node.op), result, left, right)
        return result

    def _visit_LogicalNode(self, node: LogicalNode) -> str:
        left = self._visit(node.left)
        right = self._visit(node.right)
        result = self._new_temp()

        if node.op == "&&":
            self._emit("AND", result, left, right)
        elif node.op == "||":
            self._emit("OR", result, left, right)

        return result

    # ── Literals ────────────────────────────────────────────────

    def _visit_NumberLitNode(self, node: NumberLitNode) -> str:
        return str(node.value)

    def _visit_DecimalLitNode(self, node: DecimalLitNode) -> str:
        return str(node.value)

    def _visit_StringLitNode(self, node: StringLitNode) -> str:
        return f'"{node.value}"'

    def _visit_BoolLitNode(self, node: BoolLitNode) -> str:
        return "true" if node.value else "false"

    def _visit_IdentifierNode(self, node: IdentifierNode) -> str:
        return node.name
