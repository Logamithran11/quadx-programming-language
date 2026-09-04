"""
QXL Lexical Analyzer (Lexer)
============================
Implements tokenization of QXL source code using PLY Lex.

Responsibilities:
    - Recognize all QXL tokens (keywords, operators, literals, identifiers)
    - Handle single-line (//) and multi-line (/* */) comments
    - Track line and column numbers for error reporting
    - Collect lexical errors without halting (error recovery)
    - Produce a serializable token list for the IDE

Usage:
    >>> from backend.lexer import QXLLexer
    >>> lexer = QXLLexer()
    >>> tokens, errors = lexer.tokenize('start show "Hello" end')
"""

from __future__ import annotations

import ply.lex as lex
from typing import Any, Dict, List, Tuple

from backend.errors import LexerError, ErrorCollector, CompilerPhase


class QXLLexer:
    """PLY-based lexical analyzer for the QXL language.
    
    Converts raw source code into a stream of tokens. Each token carries
    its type, value, line number, and column position.
    """

    # ── Reserved Words ──────────────────────────────────────────
    reserved: Dict[str, str] = {
        "start":       "START",
        "end":         "END",
        "show":        "SHOW",
        "read":        "READ",
        "number":      "NUMBER",
        "decimal":     "DECIMAL",
        "text":        "TEXT",
        "bool":        "BOOL",
        "if":          "IF",
        "otherwise":   "OTHERWISE",
        "endif":       "ENDIF",
        "repeat":      "REPEAT",
        "endrepeat":   "ENDREPEAT",
        "function":    "FUNCTION",
        "return":      "RETURN",
        "endfunction": "ENDFUNCTION",
        "break":       "BREAK",
        "continue":    "CONTINUE",
        "true":        "TRUE",
        "false":       "FALSE",
    }

    # ── Token List ──────────────────────────────────────────────
    tokens: List[str] = [
        # Literals
        "NUMBER_LIT",
        "DECIMAL_LIT",
        "STRING_LIT",
        "IDENTIFIER",

        # Arithmetic operators
        "PLUS",
        "MINUS",
        "TIMES",
        "DIVIDE",
        "MOD",

        # Comparison operators
        "GT",
        "LT",
        "GTE",
        "LTE",
        "EQEQ",
        "NEQ",

        # Logical operators
        "AND",
        "OR",
        "NOT",

        # Assignment
        "ASSIGN",

        # Delimiters
        "LPAREN",
        "RPAREN",
        "COMMA",
        "COLON",

        # Newline (statement separator)
        "NEWLINE",
    ] + list(reserved.values())

    # ── Simple Token Rules (string) ─────────────────────────────
    t_PLUS    = r"\+"
    t_MINUS   = r"-"
    t_TIMES   = r"\*"
    t_DIVIDE  = r"/"
    t_MOD     = r"%"
    t_GTE     = r">="
    t_LTE     = r"<="
    t_EQEQ    = r"=="
    t_NEQ     = r"!="
    t_GT      = r">"
    t_LT      = r"<"
    t_AND     = r"&&"
    t_OR      = r"\|\|"
    t_NOT     = r"!"
    t_ASSIGN  = r"="
    t_LPAREN  = r"\("
    t_RPAREN  = r"\)"
    t_COMMA   = r","
    t_COLON   = r":"

    # ── Ignored Characters ──────────────────────────────────────
    t_ignore = " \t\r"    # Spaces, tabs, carriage returns

    def __init__(self) -> None:
        """Initialize the lexer."""
        self.errors: ErrorCollector = ErrorCollector()
        self.lexer: Any = None
        self._token_list: List[Dict[str, Any]] = []
        self._build()

    def _build(self) -> None:
        """Build the PLY lexer from this class's token rules."""
        self.lexer = lex.lex(module=self, errorlog=lex.NullLogger())

    # ── Complex Token Rules (functions) ─────────────────────────

    def t_SINGLE_COMMENT(self, t: Any) -> None:
        r"//[^\n]*"
        # Single-line comment — discard entirely
        pass

    def t_MULTI_COMMENT(self, t: Any) -> None:
        r"/\*[\s\S]*?\*/"
        # Multi-line comment — count newlines for line tracking
        t.lexer.lineno += t.value.count("\n")

    def t_DECIMAL_LIT(self, t: Any) -> Any:
        r"\d+\.\d+"
        t.value = float(t.value)
        return t

    def t_NUMBER_LIT(self, t: Any) -> Any:
        r"\d+"
        t.value = int(t.value)
        return t

    def t_STRING_LIT(self, t: Any) -> Any:
        r'"([^"\\]|\\.)*"'
        # Strip surrounding quotes; keep the content
        t.value = t.value[1:-1]
        return t

    def t_IDENTIFIER(self, t: Any) -> Any:
        r"[a-zA-Z_][a-zA-Z0-9_]*"
        # Check if identifier is a reserved word
        t.type = self.reserved.get(t.value, "IDENTIFIER")
        return t

    def t_NEWLINE(self, t: Any) -> Any:
        r"\n+"
        t.lexer.lineno += len(t.value)
        t.type = "NEWLINE"
        return t

    def t_error(self, t: Any) -> None:
        """Handle illegal characters — record error and skip."""
        col = self._find_column(t)
        self.errors.add(LexerError(
            message=f"Illegal character '{t.value[0]}'",
            line=t.lexer.lineno,
            column=col,
            suggestion=f"Remove or replace the character '{t.value[0]}'"
        ))
        t.lexer.skip(1)

    # ── Tokenization ────────────────────────────────────────────

    def tokenize(self, source: str) -> Tuple[List[Dict[str, Any]], ErrorCollector]:
        """Tokenize QXL source code.
        
        Args:
            source: Raw QXL source string.
            
        Returns:
            Tuple of (token_list, error_collector).
            Each token is a dict with keys: type, value, line, column.
        """
        self.errors = ErrorCollector()
        self._token_list = []
        self._source = source

        self.lexer.lineno = 1
        self.lexer.input(source)

        while True:
            tok = self.lexer.token()
            if tok is None:
                break
            self._token_list.append({
                "type": tok.type,
                "value": tok.value,
                "line": tok.lineno,
                "column": self._find_column(tok),
            })

        return self._token_list, self.errors

    def get_tokens(self) -> List[Dict[str, Any]]:
        """Return the last tokenization result."""
        return self._token_list

    # ── Helpers ─────────────────────────────────────────────────

    def _find_column(self, token: Any) -> int:
        """Calculate column number from the token's lexpos."""
        if not hasattr(self, "_source") or self._source is None:
            return 0
        last_newline = self._source.rfind("\n", 0, token.lexpos)
        return (token.lexpos - last_newline)

    @classmethod
    def get_keywords(cls) -> List[str]:
        """Return all QXL reserved keywords (for IDE auto-complete)."""
        return list(cls.reserved.keys())

    @classmethod
    def get_token_types(cls) -> List[str]:
        """Return all recognized token type names."""
        return list(cls.tokens)
