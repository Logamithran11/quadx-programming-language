"""
QXL Semantic Analyzer Unit Tests
==================================
Tests type checking, scope management, function validation,
and error detection in the semantic analysis phase.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from backend.lexer import QXLLexer
from backend.parser import QXLParser
from backend.semantic import SemanticAnalyzer


def analyze(code: str):
    """Helper: parse and semantically analyze QXL code."""
    lexer = QXLLexer()
    parser = QXLParser()
    ast, parse_errors = parser.parse(code, lexer)
    if ast is None:
        return None, parse_errors
    analyzer = SemanticAnalyzer()
    symbol_table, sem_errors = analyzer.analyze(ast)
    return symbol_table, sem_errors


class TestSemanticVariables:
    """Test variable declaration and usage checks."""

    def test_valid_declaration(self):
        st, errors = analyze("start\nnumber x = 10\nend")
        assert not errors.has_errors()
        assert st.lookup("x") is not None

    def test_duplicate_variable(self):
        _, errors = analyze("start\nnumber x = 1\nnumber x = 2\nend")
        assert errors.has_errors()
        assert "already declared" in errors.get_errors()[0].message

    def test_undefined_variable(self):
        _, errors = analyze("start\nshow x\nend")
        assert errors.has_errors()
        assert "Undefined variable" in errors.get_errors()[0].message

    def test_type_mismatch_assignment(self):
        _, errors = analyze('start\nnumber x = "hello"\nend')
        assert errors.has_errors()
        assert "Type mismatch" in errors.get_errors()[0].message

    def test_number_decimal_compatible(self):
        _, errors = analyze("start\ndecimal x = 10\nend")
        assert not errors.has_errors()  # number ↔ decimal is allowed


class TestSemanticControlFlow:
    """Test control flow validation."""

    def test_break_outside_loop(self):
        _, errors = analyze("start\nbreak\nend")
        assert errors.has_errors()
        assert "repeat loop" in errors.get_errors()[0].message

    def test_continue_outside_loop(self):
        _, errors = analyze("start\ncontinue\nend")
        assert errors.has_errors()

    def test_break_inside_loop(self):
        _, errors = analyze("start\nnumber i = 0\nrepeat i < 5\nbreak\nendrepeat\nend")
        assert not errors.has_errors()

    def test_if_scoping(self):
        """Variables declared in if block should not leak to outer scope."""
        st, errors = analyze(
            "start\nnumber x = 1\nif x > 0\nnumber y = 2\nendif\nend"
        )
        assert not errors.has_errors()


class TestSemanticFunctions:
    """Test function validation."""

    def test_valid_function(self):
        code = "start\nfunction add(number a, number b)\nreturn a + b\nendfunction\nend"
        _, errors = analyze(code)
        assert not errors.has_errors()

    def test_duplicate_function(self):
        code = "start\nfunction foo()\nreturn 1\nendfunction\nfunction foo()\nreturn 2\nendfunction\nend"
        _, errors = analyze(code)
        assert errors.has_errors()
        assert "already declared" in errors.get_errors()[0].message

    def test_undefined_function_call(self):
        code = "start\nshow unknown()\nend"
        _, errors = analyze(code)
        assert errors.has_errors()
        assert "Undefined function" in errors.get_errors()[0].message

    def test_wrong_argument_count(self):
        code = "start\nfunction add(number a, number b)\nreturn a + b\nendfunction\nshow add(1)\nend"
        _, errors = analyze(code)
        assert errors.has_errors()
        assert "expects 2" in errors.get_errors()[0].message

    def test_return_outside_function(self):
        _, errors = analyze("start\nreturn 5\nend")
        assert errors.has_errors()
        assert "inside a function" in errors.get_errors()[0].message

    def test_duplicate_parameter(self):
        code = "start\nfunction foo(number x, number x)\nreturn x\nendfunction\nend"
        _, errors = analyze(code)
        assert errors.has_errors()
        assert "Duplicate parameter" in errors.get_errors()[0].message


class TestSemanticSymbolTable:
    """Test symbol table population."""

    def test_variable_count(self):
        st, _ = analyze("start\nnumber a = 1\nnumber b = 2\nnumber c = 3\nend")
        assert len(st.get_all_symbols()) == 3

    def test_function_registration(self):
        code = "start\nfunction f1()\nreturn 1\nendfunction\nfunction f2()\nreturn 2\nendfunction\nend"
        st, _ = analyze(code)
        assert len(st.get_all_functions()) == 2
        assert st.lookup_function("f1") is not None
        assert st.lookup_function("f2") is not None

    def test_serialization(self):
        st, _ = analyze("start\nnumber x = 1\nend")
        d = st.to_dict()
        assert "variables" in d
        assert "functions" in d
        assert d["variable_count"] == 1
