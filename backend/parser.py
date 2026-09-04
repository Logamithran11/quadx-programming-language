"""
QXL Syntax Analyzer (Parser)
=============================
Implements parsing of QXL token streams into an Abstract Syntax Tree
using PLY Yacc. Follows the grammar defined in grammar.py.

Responsibilities:
    - Parse token stream from the Lexer into a well-formed AST
    - Enforce syntactic structure (start/end, if/endif, etc.)
    - Report syntax errors with line numbers and suggestions
    - Handle operator precedence and associativity

Usage:
    >>> from backend.lexer import QXLLexer
    >>> from backend.parser import QXLParser
    >>> lexer = QXLLexer()
    >>> parser = QXLParser()
    >>> tokens, lex_errors = lexer.tokenize(source)
    >>> ast, parse_errors = parser.parse(source, lexer)
"""

from __future__ import annotations

import ply.yacc as yacc
from typing import Any, List, Optional, Tuple

from backend.lexer import QXLLexer
from backend.errors import ParserError, ErrorCollector
from backend.ast_nodes import (
    ASTNode, ProgramNode, BlockNode, VarDeclNode, AssignNode,
    ShowNode, ReadNode, IfNode, RepeatNode, FunctionDeclNode,
    FunctionCallNode, ReturnNode, BreakNode, ContinueNode,
    BinOpNode, UnaryOpNode, ComparisonNode, LogicalNode,
    NumberLitNode, DecimalLitNode, StringLitNode, BoolLitNode,
    IdentifierNode, ParamNode,
)


class QXLParser:
    """PLY-based parser for the QXL language.
    
    Builds a complete AST from the token stream produced by QXLLexer.
    Uses operator precedence declarations and PLY Yacc grammar rules
    (defined as method docstrings).
    """

    # Import token list from the lexer (required by PLY)
    tokens = QXLLexer.tokens

    # ── Operator Precedence (lowest → highest) ──────────────────
    precedence = (
        ("left", "OR"),
        ("left", "AND"),
        ("left", "EQEQ", "NEQ"),
        ("left", "GT", "LT", "GTE", "LTE"),
        ("left", "PLUS", "MINUS"),
        ("left", "TIMES", "DIVIDE", "MOD"),
        ("right", "NOT"),
        ("right", "UMINUS"),
    )

    def __init__(self) -> None:
        """Initialize the parser."""
        self.errors: ErrorCollector = ErrorCollector()
        self.ast: Optional[ProgramNode] = None
        self._parser: Any = None
        self._build()

    def _build(self) -> None:
        """Build the PLY parser from this class's grammar rules."""
        self._parser = yacc.yacc(
            module=self,
            debug=False,
            write_tables=False,
            errorlog=yacc.NullLogger(),
        )

    # ═════════════════════════════════════════════════════════════
    # GRAMMAR RULES
    # ═════════════════════════════════════════════════════════════

    # ── Program ─────────────────────────────────────────────────

    def p_program(self, p: Any) -> None:
        """program : newlines_opt START newlines_opt statement_list END newlines_opt"""
        p[0] = ProgramNode(body=p[4], line=p.lineno(2), column=0)

    def p_program_empty(self, p: Any) -> None:
        """program : newlines_opt START newlines_opt END newlines_opt"""
        p[0] = ProgramNode(body=[], line=p.lineno(2), column=0)

    # ── Newlines (optional separator handling) ──────────────────

    def p_newlines_opt(self, p: Any) -> None:
        """newlines_opt : newlines_opt NEWLINE
                        | NEWLINE
                        | empty"""
        pass

    # ── Statement List ──────────────────────────────────────────

    def p_statement_list(self, p: Any) -> None:
        """statement_list : statement_list NEWLINE statement"""
        if p[3] is not None:
            p[0] = p[1] + [p[3]]
        else:
            p[0] = p[1]

    def p_statement_list_newline(self, p: Any) -> None:
        """statement_list : statement_list NEWLINE"""
        p[0] = p[1]

    def p_statement_list_single(self, p: Any) -> None:
        """statement_list : statement"""
        if p[1] is not None:
            p[0] = [p[1]]
        else:
            p[0] = []

    # ── Statement ───────────────────────────────────────────────

    def p_statement(self, p: Any) -> None:
        """statement : var_decl
                     | assignment
                     | show_stmt
                     | read_stmt
                     | if_stmt
                     | repeat_stmt
                     | function_decl
                     | return_stmt
                     | break_stmt
                     | continue_stmt
                     | function_call_stmt"""
        p[0] = p[1]

    # ── Variable Declaration ────────────────────────────────────

    def p_var_decl_init(self, p: Any) -> None:
        """var_decl : type_spec IDENTIFIER ASSIGN expression"""
        p[0] = VarDeclNode(
            var_type=p[1], name=p[2], value=p[4],
            line=p.lineno(2), column=0
        )

    def p_var_decl_no_init(self, p: Any) -> None:
        """var_decl : type_spec IDENTIFIER"""
        p[0] = VarDeclNode(
            var_type=p[1], name=p[2], value=None,
            line=p.lineno(2), column=0
        )

    def p_type_spec(self, p: Any) -> None:
        """type_spec : NUMBER
                     | DECIMAL
                     | TEXT
                     | BOOL"""
        p[0] = p[1]

    # ── Assignment ──────────────────────────────────────────────

    def p_assignment(self, p: Any) -> None:
        """assignment : IDENTIFIER ASSIGN expression"""
        p[0] = AssignNode(name=p[1], value=p[3], line=p.lineno(1), column=0)

    # ── Show Statement ──────────────────────────────────────────

    def p_show_stmt(self, p: Any) -> None:
        """show_stmt : SHOW expression"""
        p[0] = ShowNode(value=p[2], line=p.lineno(1), column=0)

    # ── Read Statement ──────────────────────────────────────────

    def p_read_stmt(self, p: Any) -> None:
        """read_stmt : READ IDENTIFIER"""
        p[0] = ReadNode(name=p[2], line=p.lineno(1), column=0)

    # ── If Statement ────────────────────────────────────────────

    def p_if_stmt(self, p: Any) -> None:
        """if_stmt : IF expression newlines_opt statement_list OTHERWISE newlines_opt statement_list ENDIF"""
        p[0] = IfNode(
            condition=p[2], then_body=p[4], else_body=p[7],
            line=p.lineno(1), column=0
        )

    def p_if_stmt_no_else(self, p: Any) -> None:
        """if_stmt : IF expression newlines_opt statement_list ENDIF"""
        p[0] = IfNode(
            condition=p[2], then_body=p[4], else_body=[],
            line=p.lineno(1), column=0
        )

    # ── Repeat Statement ────────────────────────────────────────

    def p_repeat_stmt(self, p: Any) -> None:
        """repeat_stmt : REPEAT expression newlines_opt statement_list ENDREPEAT"""
        p[0] = RepeatNode(
            condition=p[2], body=p[4],
            line=p.lineno(1), column=0
        )

    # ── Function Declaration ────────────────────────────────────

    def p_function_decl(self, p: Any) -> None:
        """function_decl : FUNCTION IDENTIFIER LPAREN param_list RPAREN newlines_opt statement_list ENDFUNCTION"""
        p[0] = FunctionDeclNode(
            name=p[2], params=p[4], body=p[7],
            line=p.lineno(1), column=0
        )

    def p_function_decl_no_params(self, p: Any) -> None:
        """function_decl : FUNCTION IDENTIFIER LPAREN RPAREN newlines_opt statement_list ENDFUNCTION"""
        p[0] = FunctionDeclNode(
            name=p[2], params=[], body=p[6],
            line=p.lineno(1), column=0
        )

    def p_param_list(self, p: Any) -> None:
        """param_list : param_list COMMA param"""
        p[0] = p[1] + [p[3]]

    def p_param_list_single(self, p: Any) -> None:
        """param_list : param"""
        p[0] = [p[1]]

    def p_param(self, p: Any) -> None:
        """param : type_spec IDENTIFIER"""
        p[0] = ParamNode(
            param_type=p[1], name=p[2],
            line=p.lineno(2), column=0
        )

    # ── Function Call (as statement) ────────────────────────────

    def p_function_call_stmt(self, p: Any) -> None:
        """function_call_stmt : function_call"""
        p[0] = p[1]

    # ── Function Call (expression) ──────────────────────────────

    def p_function_call(self, p: Any) -> None:
        """function_call : IDENTIFIER LPAREN arg_list RPAREN"""
        p[0] = FunctionCallNode(
            name=p[1], args=p[3],
            line=p.lineno(1), column=0
        )

    def p_function_call_no_args(self, p: Any) -> None:
        """function_call : IDENTIFIER LPAREN RPAREN"""
        p[0] = FunctionCallNode(
            name=p[1], args=[],
            line=p.lineno(1), column=0
        )

    def p_arg_list(self, p: Any) -> None:
        """arg_list : arg_list COMMA expression"""
        p[0] = p[1] + [p[3]]

    def p_arg_list_single(self, p: Any) -> None:
        """arg_list : expression"""
        p[0] = [p[1]]

    # ── Return Statement ────────────────────────────────────────

    def p_return_stmt_value(self, p: Any) -> None:
        """return_stmt : RETURN expression"""
        p[0] = ReturnNode(value=p[2], line=p.lineno(1), column=0)

    def p_return_stmt_void(self, p: Any) -> None:
        """return_stmt : RETURN"""
        p[0] = ReturnNode(value=None, line=p.lineno(1), column=0)

    # ── Break / Continue ────────────────────────────────────────

    def p_break_stmt(self, p: Any) -> None:
        """break_stmt : BREAK"""
        p[0] = BreakNode(line=p.lineno(1), column=0)

    def p_continue_stmt(self, p: Any) -> None:
        """continue_stmt : CONTINUE"""
        p[0] = ContinueNode(line=p.lineno(1), column=0)

    # ═════════════════════════════════════════════════════════════
    # EXPRESSIONS (in precedence order, lowest → highest)
    # ═════════════════════════════════════════════════════════════

    # ── Logical OR ──────────────────────────────────────────────

    def p_expression_logical_or(self, p: Any) -> None:
        """expression : expression OR expression"""
        p[0] = LogicalNode(op="||", left=p[1], right=p[3],
                           line=p.lineno(2), column=0)

    # ── Logical AND ─────────────────────────────────────────────

    def p_expression_logical_and(self, p: Any) -> None:
        """expression : expression AND expression"""
        p[0] = LogicalNode(op="&&", left=p[1], right=p[3],
                           line=p.lineno(2), column=0)

    # ── Equality ────────────────────────────────────────────────

    def p_expression_equality(self, p: Any) -> None:
        """expression : expression EQEQ expression
                      | expression NEQ expression"""
        p[0] = ComparisonNode(op=p[2], left=p[1], right=p[3],
                              line=p.lineno(2), column=0)

    # ── Comparison ──────────────────────────────────────────────

    def p_expression_comparison(self, p: Any) -> None:
        """expression : expression GT expression
                      | expression LT expression
                      | expression GTE expression
                      | expression LTE expression"""
        p[0] = ComparisonNode(op=p[2], left=p[1], right=p[3],
                              line=p.lineno(2), column=0)

    # ── Additive ────────────────────────────────────────────────

    def p_expression_additive(self, p: Any) -> None:
        """expression : expression PLUS expression
                      | expression MINUS expression"""
        p[0] = BinOpNode(op=p[2], left=p[1], right=p[3],
                         line=p.lineno(2), column=0)

    # ── Multiplicative ──────────────────────────────────────────

    def p_expression_multiplicative(self, p: Any) -> None:
        """expression : expression TIMES expression
                      | expression DIVIDE expression
                      | expression MOD expression"""
        p[0] = BinOpNode(op=p[2], left=p[1], right=p[3],
                         line=p.lineno(2), column=0)

    # ── Unary ───────────────────────────────────────────────────

    def p_expression_uminus(self, p: Any) -> None:
        """expression : MINUS expression %prec UMINUS"""
        p[0] = UnaryOpNode(op="-", operand=p[2],
                           line=p.lineno(1), column=0)

    def p_expression_not(self, p: Any) -> None:
        """expression : NOT expression"""
        p[0] = UnaryOpNode(op="!", operand=p[2],
                           line=p.lineno(1), column=0)

    # ── Atoms ───────────────────────────────────────────────────

    def p_expression_number(self, p: Any) -> None:
        """expression : NUMBER_LIT"""
        p[0] = NumberLitNode(value=p[1], line=p.lineno(1), column=0)

    def p_expression_decimal(self, p: Any) -> None:
        """expression : DECIMAL_LIT"""
        p[0] = DecimalLitNode(value=p[1], line=p.lineno(1), column=0)

    def p_expression_string(self, p: Any) -> None:
        """expression : STRING_LIT"""
        p[0] = StringLitNode(value=p[1], line=p.lineno(1), column=0)

    def p_expression_true(self, p: Any) -> None:
        """expression : TRUE"""
        p[0] = BoolLitNode(value=True, line=p.lineno(1), column=0)

    def p_expression_false(self, p: Any) -> None:
        """expression : FALSE"""
        p[0] = BoolLitNode(value=False, line=p.lineno(1), column=0)

    def p_expression_identifier(self, p: Any) -> None:
        """expression : IDENTIFIER"""
        p[0] = IdentifierNode(name=p[1], line=p.lineno(1), column=0)

    def p_expression_function_call(self, p: Any) -> None:
        """expression : function_call"""
        p[0] = p[1]

    def p_expression_group(self, p: Any) -> None:
        """expression : LPAREN expression RPAREN"""
        p[0] = p[2]

    # ── Empty Production ────────────────────────────────────────

    def p_empty(self, p: Any) -> None:
        """empty :"""
        pass

    # ── Error Recovery ──────────────────────────────────────────

    def p_error(self, p: Any) -> None:
        """Handle syntax errors with descriptive messages."""
        if p is None:
            self.errors.add(ParserError(
                message="Unexpected end of input. Did you forget 'end'?",
                line=0,
                suggestion="Make sure your program ends with 'end'"
            ))
        else:
            # Build a helpful suggestion based on the token
            suggestion = self._get_suggestion(p)
            self.errors.add(ParserError(
                message=f"Unexpected token '{p.value}' ({p.type})",
                line=p.lineno,
                column=getattr(p, "lexpos", 0),
                suggestion=suggestion
            ))

    def _get_suggestion(self, token: Any) -> str:
        """Generate context-aware fix suggestions for parse errors."""
        suggestions = {
            "IDENTIFIER": "Check if you're missing a keyword or operator before this identifier",
            "NUMBER_LIT": "Unexpected number — check the previous line for missing operators",
            "STRING_LIT": "Unexpected string — did you forget 'show' or an assignment?",
            "END": "Unexpected 'end' — make sure all blocks (if/repeat/function) are properly closed",
            "ENDIF": "Unexpected 'endif' — make sure there's a matching 'if'",
            "ENDREPEAT": "Unexpected 'endrepeat' — make sure there's a matching 'repeat'",
            "ENDFUNCTION": "Unexpected 'endfunction' — make sure there's a matching 'function'",
            "ASSIGN": "Unexpected '=' — make sure the left side is a valid variable name",
        }
        return suggestions.get(token.type, "Check the syntax near this token")

    # ═════════════════════════════════════════════════════════════
    # PUBLIC API
    # ═════════════════════════════════════════════════════════════

    def parse(self, source: str, lexer: Optional[QXLLexer] = None) -> Tuple[Optional[ProgramNode], ErrorCollector]:
        """Parse QXL source code and build an AST.
        
        Args:
            source: Raw QXL source string.
            lexer: Optional pre-configured QXLLexer instance.
            
        Returns:
            Tuple of (ast_root, error_collector).
            ast_root is None if parsing fails entirely.
        """
        self.errors = ErrorCollector()

        if lexer is None:
            lexer = QXLLexer()

        try:
            self.ast = self._parser.parse(
                input=source,
                lexer=lexer.lexer,
                tracking=True,
            )
        except Exception as e:
            self.errors.add(ParserError(
                message=f"Parser internal error: {str(e)}",
                suggestion="Check your program structure (start/end blocks)"
            ))
            self.ast = None

        return self.ast, self.errors

    def get_ast(self) -> Optional[ProgramNode]:
        """Return the AST from the last parse operation."""
        return self.ast
