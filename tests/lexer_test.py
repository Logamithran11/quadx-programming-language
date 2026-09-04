"""
QXL Lexer Unit Tests
=====================
Tests tokenization of all QXL constructs: keywords, operators,
literals, identifiers, comments, and error handling.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from backend.lexer import QXLLexer


class TestLexerKeywords:
    """Test that all QXL keywords are tokenized correctly."""

    def setup_method(self):
        self.lexer = QXLLexer()

    def test_start_end(self):
        tokens, errors = self.lexer.tokenize("start end")
        types = [t["type"] for t in tokens if t["type"] != "NEWLINE"]
        assert "START" in types
        assert "END" in types
        assert not errors.has_errors()

    def test_all_keywords(self):
        source = "start end show read number decimal text bool if otherwise endif repeat endrepeat function return endfunction break continue true false"
        tokens, errors = self.lexer.tokenize(source)
        types = [t["type"] for t in tokens if t["type"] != "NEWLINE"]
        expected = [
            "START", "END", "SHOW", "READ", "NUMBER", "DECIMAL", "TEXT",
            "BOOL", "IF", "OTHERWISE", "ENDIF", "REPEAT", "ENDREPEAT",
            "FUNCTION", "RETURN", "ENDFUNCTION", "BREAK", "CONTINUE",
            "TRUE", "FALSE",
        ]
        assert types == expected
        assert not errors.has_errors()


class TestLexerLiterals:
    """Test literal tokenization."""

    def setup_method(self):
        self.lexer = QXLLexer()

    def test_integer(self):
        tokens, _ = self.lexer.tokenize("42")
        num_tokens = [t for t in tokens if t["type"] == "NUMBER_LIT"]
        assert len(num_tokens) == 1
        assert num_tokens[0]["value"] == 42

    def test_decimal(self):
        tokens, _ = self.lexer.tokenize("3.14")
        dec_tokens = [t for t in tokens if t["type"] == "DECIMAL_LIT"]
        assert len(dec_tokens) == 1
        assert dec_tokens[0]["value"] == 3.14

    def test_string(self):
        tokens, _ = self.lexer.tokenize('"Hello, World!"')
        str_tokens = [t for t in tokens if t["type"] == "STRING_LIT"]
        assert len(str_tokens) == 1
        assert str_tokens[0]["value"] == "Hello, World!"

    def test_boolean_true(self):
        tokens, _ = self.lexer.tokenize("true")
        assert any(t["type"] == "TRUE" for t in tokens)

    def test_boolean_false(self):
        tokens, _ = self.lexer.tokenize("false")
        assert any(t["type"] == "FALSE" for t in tokens)


class TestLexerOperators:
    """Test operator tokenization."""

    def setup_method(self):
        self.lexer = QXLLexer()

    def test_arithmetic_operators(self):
        tokens, _ = self.lexer.tokenize("+ - * / %")
        types = [t["type"] for t in tokens if t["type"] != "NEWLINE"]
        assert types == ["PLUS", "MINUS", "TIMES", "DIVIDE", "MOD"]

    def test_comparison_operators(self):
        tokens, _ = self.lexer.tokenize("> < >= <= == !=")
        types = [t["type"] for t in tokens if t["type"] != "NEWLINE"]
        assert types == ["GT", "LT", "GTE", "LTE", "EQEQ", "NEQ"]

    def test_logical_operators(self):
        tokens, _ = self.lexer.tokenize("&& || !")
        types = [t["type"] for t in tokens if t["type"] != "NEWLINE"]
        assert "AND" in types
        assert "OR" in types
        assert "NOT" in types

    def test_assignment(self):
        tokens, _ = self.lexer.tokenize("x = 5")
        types = [t["type"] for t in tokens if t["type"] != "NEWLINE"]
        assert "ASSIGN" in types


class TestLexerComments:
    """Test comment handling."""

    def setup_method(self):
        self.lexer = QXLLexer()

    def test_single_line_comment(self):
        tokens, _ = self.lexer.tokenize("// this is a comment\nshow 5")
        types = [t["type"] for t in tokens if t["type"] != "NEWLINE"]
        assert "SHOW" in types
        # Comment should not produce a token
        assert not any("COMMENT" in t["type"] for t in tokens)

    def test_multi_line_comment(self):
        tokens, _ = self.lexer.tokenize("/* multi\nline\ncomment */\nshow 5")
        types = [t["type"] for t in tokens if t["type"] != "NEWLINE"]
        assert "SHOW" in types


class TestLexerErrors:
    """Test error handling."""

    def setup_method(self):
        self.lexer = QXLLexer()

    def test_illegal_character(self):
        tokens, errors = self.lexer.tokenize("@")
        assert errors.has_errors()
        assert "Illegal character" in errors.get_errors()[0].message

    def test_continues_after_error(self):
        tokens, errors = self.lexer.tokenize("@ show 5")
        assert errors.has_errors()
        types = [t["type"] for t in tokens if t["type"] != "NEWLINE"]
        assert "SHOW" in types  # Lexer should continue past the error


class TestLexerLineTracking:
    """Test line and column tracking."""

    def setup_method(self):
        self.lexer = QXLLexer()

    def test_line_numbers(self):
        tokens, _ = self.lexer.tokenize("start\nshow 5\nend")
        start_tok = next(t for t in tokens if t["type"] == "START")
        show_tok = next(t for t in tokens if t["type"] == "SHOW")
        end_tok = next(t for t in tokens if t["type"] == "END")
        assert start_tok["line"] == 1
        assert show_tok["line"] == 2
        assert end_tok["line"] == 3
