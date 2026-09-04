"""
QXL Formal Grammar Specification
=================================
Documents the complete context-free grammar for the QXL language
in BNF notation. Used as a reference for the parser implementation.

This module also exports grammar rule constants used by the parser
for documentation and error messages.
"""

# ─────────────────────────────────────────────────────────────
# QXL Grammar (BNF)
# ─────────────────────────────────────────────────────────────
#
# <program>         ::= START <statement_list> END
#
# <statement_list>  ::= <statement>
#                      | <statement_list> NEWLINE <statement>
#                      | <statement_list> NEWLINE
#                      | ε
#
# <statement>       ::= <var_decl>
#                      | <assignment>
#                      | <show_stmt>
#                      | <read_stmt>
#                      | <if_stmt>
#                      | <repeat_stmt>
#                      | <function_decl>
#                      | <function_call>
#                      | <return_stmt>
#                      | <break_stmt>
#                      | <continue_stmt>
#
# <var_decl>        ::= <type> IDENTIFIER ASSIGN <expression>
#                      | <type> IDENTIFIER
#
# <type>            ::= NUMBER | DECIMAL | TEXT | BOOL
#
# <assignment>      ::= IDENTIFIER ASSIGN <expression>
#
# <show_stmt>       ::= SHOW <expression>
#
# <read_stmt>       ::= READ IDENTIFIER
#
# <if_stmt>         ::= IF <expression> NEWLINE <statement_list> ENDIF
#                      | IF <expression> NEWLINE <statement_list>
#                        OTHERWISE NEWLINE <statement_list> ENDIF
#
# <repeat_stmt>     ::= REPEAT <expression> NEWLINE <statement_list> ENDREPEAT
#
# <function_decl>   ::= FUNCTION IDENTIFIER LPAREN <param_list> RPAREN
#                        NEWLINE <statement_list> ENDFUNCTION
#                      | FUNCTION IDENTIFIER LPAREN RPAREN
#                        NEWLINE <statement_list> ENDFUNCTION
#
# <param_list>      ::= <param>
#                      | <param_list> COMMA <param>
#
# <param>           ::= <type> IDENTIFIER
#
# <function_call>   ::= IDENTIFIER LPAREN <arg_list> RPAREN
#                      | IDENTIFIER LPAREN RPAREN
#
# <arg_list>        ::= <expression>
#                      | <arg_list> COMMA <expression>
#
# <return_stmt>     ::= RETURN <expression>
#                      | RETURN
#
# <break_stmt>      ::= BREAK
#
# <continue_stmt>   ::= CONTINUE
#
# <expression>      ::= <logical_or>
#
# <logical_or>      ::= <logical_and>
#                      | <logical_or> OR <logical_and>
#
# <logical_and>     ::= <equality>
#                      | <logical_and> AND <equality>
#
# <equality>        ::= <comparison>
#                      | <equality> EQEQ <comparison>
#                      | <equality> NEQ <comparison>
#
# <comparison>      ::= <additive>
#                      | <comparison> GT <additive>
#                      | <comparison> LT <additive>
#                      | <comparison> GTE <additive>
#                      | <comparison> LTE <additive>
#
# <additive>        ::= <multiplicative>
#                      | <additive> PLUS <multiplicative>
#                      | <additive> MINUS <multiplicative>
#
# <multiplicative>  ::= <unary>
#                      | <multiplicative> TIMES <unary>
#                      | <multiplicative> DIVIDE <unary>
#                      | <multiplicative> MOD <unary>
#
# <unary>           ::= <atom>
#                      | MINUS <unary>
#                      | NOT <unary>
#
# <atom>            ::= NUMBER_LIT
#                      | DECIMAL_LIT
#                      | STRING_LIT
#                      | TRUE
#                      | FALSE
#                      | IDENTIFIER
#                      | <function_call>
#                      | LPAREN <expression> RPAREN
#

# ─────────────────────────────────────────────────────────────
# Grammar Rule Names (for error messages)
# ─────────────────────────────────────────────────────────────

RULE_PROGRAM = "program → START statement_list END"
RULE_VAR_DECL = "var_decl → type IDENTIFIER [= expression]"
RULE_ASSIGNMENT = "assignment → IDENTIFIER = expression"
RULE_SHOW = "show_stmt → SHOW expression"
RULE_READ = "read_stmt → READ IDENTIFIER"
RULE_IF = "if_stmt → IF expression ... [OTHERWISE ...] ENDIF"
RULE_REPEAT = "repeat_stmt → REPEAT expression ... ENDREPEAT"
RULE_FUNCTION = "function_decl → FUNCTION IDENTIFIER(params) ... ENDFUNCTION"
RULE_RETURN = "return_stmt → RETURN [expression]"
RULE_EXPRESSION = "expression → logical_or"

# Data types recognized by the grammar
QXL_TYPES = {"number", "decimal", "text", "bool"}

# Operator precedence (lowest to highest)
PRECEDENCE_TABLE = [
    ("left", "OR"),
    ("left", "AND"),
    ("left", "EQEQ", "NEQ"),
    ("left", "GT", "LT", "GTE", "LTE"),
    ("left", "PLUS", "MINUS"),
    ("left", "TIMES", "DIVIDE", "MOD"),
    ("right", "NOT", "UMINUS"),
]
