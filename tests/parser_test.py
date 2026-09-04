"""
QXL Parser Unit Tests
======================
Tests AST generation for all QXL grammar constructs.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from backend.lexer import QXLLexer
from backend.parser import QXLParser
from backend.ast_nodes import *


class TestParserBasic:
    """Test basic program structure parsing."""

    def setup_method(self):
        self.parser = QXLParser()

    def _parse(self, code):
        lexer = QXLLexer()
        ast, errors = self.parser.parse(code, lexer)
        return ast, errors

    def test_empty_program(self):
        ast, errors = self._parse("start\nend")
        assert ast is not None
        assert isinstance(ast, ProgramNode)
        assert not errors.has_errors()

    def test_program_with_show(self):
        ast, errors = self._parse('start\nshow "Hello"\nend')
        assert ast is not None
        assert len(ast.body) == 1
        assert isinstance(ast.body[0], ShowNode)
        assert not errors.has_errors()


class TestParserVarDecl:
    """Test variable declaration parsing."""

    def setup_method(self):
        self.parser = QXLParser()

    def _parse(self, code):
        lexer = QXLLexer()
        ast, errors = self.parser.parse(code, lexer)
        return ast, errors

    def test_number_decl_with_init(self):
        ast, _ = self._parse("start\nnumber x = 10\nend")
        assert isinstance(ast.body[0], VarDeclNode)
        assert ast.body[0].var_type == "number"
        assert ast.body[0].name == "x"
        assert isinstance(ast.body[0].value, NumberLitNode)

    def test_text_decl(self):
        ast, _ = self._parse('start\ntext name = "Alice"\nend')
        decl = ast.body[0]
        assert isinstance(decl, VarDeclNode)
        assert decl.var_type == "text"
        assert isinstance(decl.value, StringLitNode)

    def test_bool_decl(self):
        ast, _ = self._parse("start\nbool flag = true\nend")
        decl = ast.body[0]
        assert isinstance(decl, VarDeclNode)
        assert decl.var_type == "bool"
        assert isinstance(decl.value, BoolLitNode)
        assert decl.value.value is True

    def test_decimal_decl(self):
        ast, _ = self._parse("start\ndecimal pi = 3.14\nend")
        decl = ast.body[0]
        assert isinstance(decl, VarDeclNode)
        assert decl.var_type == "decimal"
        assert isinstance(decl.value, DecimalLitNode)


class TestParserExpressions:
    """Test expression parsing."""

    def setup_method(self):
        self.parser = QXLParser()

    def _parse(self, code):
        lexer = QXLLexer()
        ast, errors = self.parser.parse(code, lexer)
        return ast, errors

    def test_arithmetic(self):
        ast, _ = self._parse("start\nshow 1 + 2\nend")
        show = ast.body[0]
        assert isinstance(show, ShowNode)
        assert isinstance(show.value, BinOpNode)
        assert show.value.op == "+"

    def test_comparison(self):
        ast, _ = self._parse("start\nnumber x = 1\nif x > 5\nshow x\nendif\nend")
        if_node = ast.body[1]
        assert isinstance(if_node, IfNode)
        assert isinstance(if_node.condition, ComparisonNode)
        assert if_node.condition.op == ">"

    def test_nested_arithmetic(self):
        ast, _ = self._parse("start\nshow 1 + 2 * 3\nend")
        show = ast.body[0]
        # Due to precedence, should be 1 + (2 * 3)
        assert isinstance(show.value, BinOpNode)
        assert show.value.op == "+"

    def test_unary_minus(self):
        ast, _ = self._parse("start\nshow -5\nend")
        show = ast.body[0]
        assert isinstance(show.value, UnaryOpNode)
        assert show.value.op == "-"


class TestParserControlFlow:
    """Test control flow parsing."""

    def setup_method(self):
        self.parser = QXLParser()

    def _parse(self, code):
        lexer = QXLLexer()
        ast, errors = self.parser.parse(code, lexer)
        return ast, errors

    def test_if_endif(self):
        ast, _ = self._parse("start\nnumber x = 1\nif x > 0\nshow x\nendif\nend")
        if_node = ast.body[1]
        assert isinstance(if_node, IfNode)
        assert len(if_node.then_body) == 1
        assert len(if_node.else_body) == 0

    def test_if_otherwise(self):
        code = "start\nnumber x = 1\nif x > 0\nshow 1\notherwise\nshow 0\nendif\nend"
        ast, _ = self._parse(code)
        if_node = ast.body[1]
        assert isinstance(if_node, IfNode)
        assert len(if_node.then_body) == 1
        assert len(if_node.else_body) == 1

    def test_repeat_loop(self):
        code = "start\nnumber i = 0\nrepeat i < 5\ni = i + 1\nendrepeat\nend"
        ast, _ = self._parse(code)
        repeat = ast.body[1]
        assert isinstance(repeat, RepeatNode)
        assert isinstance(repeat.condition, ComparisonNode)

    def test_break_continue(self):
        code = "start\nnumber i = 0\nrepeat i < 10\nif i == 5\nbreak\nendif\ni = i + 1\nendrepeat\nend"
        ast, errors = self._parse(code)
        assert not errors.has_errors()


class TestParserFunctions:
    """Test function declaration and call parsing."""

    def setup_method(self):
        self.parser = QXLParser()

    def _parse(self, code):
        lexer = QXLLexer()
        ast, errors = self.parser.parse(code, lexer)
        return ast, errors

    def test_function_decl(self):
        code = "start\nfunction add(number a, number b)\nreturn a + b\nendfunction\nend"
        ast, _ = self._parse(code)
        func = ast.body[0]
        assert isinstance(func, FunctionDeclNode)
        assert func.name == "add"
        assert len(func.params) == 2

    def test_function_call(self):
        code = "start\nfunction greet()\nshow \"hi\"\nendfunction\ngreet()\nend"
        ast, _ = self._parse(code)
        call = ast.body[1]
        assert isinstance(call, FunctionCallNode)
        assert call.name == "greet"

    def test_function_with_return(self):
        code = "start\nfunction double(number x)\nreturn x * 2\nendfunction\nend"
        ast, _ = self._parse(code)
        func = ast.body[0]
        ret = func.body[0]
        assert isinstance(ret, ReturnNode)
        assert isinstance(ret.value, BinOpNode)


class TestParserErrors:
    """Test parser error reporting."""

    def setup_method(self):
        self.parser = QXLParser()

    def _parse(self, code):
        lexer = QXLLexer()
        ast, errors = self.parser.parse(code, lexer)
        return ast, errors

    def test_missing_end(self):
        _, errors = self._parse("start\nshow 5")
        assert errors.has_errors()

    def test_missing_start(self):
        _, errors = self._parse("show 5\nend")
        assert errors.has_errors()
