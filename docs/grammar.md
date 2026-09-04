# QXL Formal Grammar Specification

## Notation
- `::=` — is defined as
- `|` — or
- `ε` — empty production
- `UPPERCASE` — terminal (token)
- `<lowercase>` — non-terminal

---

## Program Structure

```
<program>         ::= START <statement_list> END
```

## Statements

```
<statement_list>  ::= <statement>
                    | <statement_list> NEWLINE <statement>
                    | <statement_list> NEWLINE
                    | ε

<statement>       ::= <var_decl>
                    | <assignment>
                    | <show_stmt>
                    | <read_stmt>
                    | <if_stmt>
                    | <repeat_stmt>
                    | <function_decl>
                    | <function_call>
                    | <return_stmt>
                    | BREAK
                    | CONTINUE
```

## Declarations

```
<var_decl>        ::= <type> IDENTIFIER ASSIGN <expression>
                    | <type> IDENTIFIER

<type>            ::= NUMBER | DECIMAL | TEXT | BOOL

<assignment>      ::= IDENTIFIER ASSIGN <expression>
```

## I/O Statements

```
<show_stmt>       ::= SHOW <expression>

<read_stmt>       ::= READ IDENTIFIER
```

## Control Flow

```
<if_stmt>         ::= IF <expression> NEWLINE <statement_list> ENDIF
                    | IF <expression> NEWLINE <statement_list>
                      OTHERWISE NEWLINE <statement_list> ENDIF

<repeat_stmt>     ::= REPEAT <expression> NEWLINE <statement_list> ENDREPEAT
```

## Functions

```
<function_decl>   ::= FUNCTION IDENTIFIER LPAREN <param_list> RPAREN
                      NEWLINE <statement_list> ENDFUNCTION
                    | FUNCTION IDENTIFIER LPAREN RPAREN
                      NEWLINE <statement_list> ENDFUNCTION

<param_list>      ::= <param>
                    | <param_list> COMMA <param>

<param>           ::= <type> IDENTIFIER

<function_call>   ::= IDENTIFIER LPAREN <arg_list> RPAREN
                    | IDENTIFIER LPAREN RPAREN

<arg_list>        ::= <expression>
                    | <arg_list> COMMA <expression>

<return_stmt>     ::= RETURN <expression>
                    | RETURN
```

## Expressions (Precedence: lowest → highest)

```
<expression>      ::= <logical_or>

<logical_or>      ::= <logical_and>
                    | <logical_or> OR <logical_and>

<logical_and>     ::= <equality>
                    | <logical_and> AND <equality>

<equality>        ::= <comparison>
                    | <equality> EQEQ <comparison>
                    | <equality> NEQ <comparison>

<comparison>      ::= <additive>
                    | <comparison> GT <additive>
                    | <comparison> LT <additive>
                    | <comparison> GTE <additive>
                    | <comparison> LTE <additive>

<additive>        ::= <multiplicative>
                    | <additive> PLUS <multiplicative>
                    | <additive> MINUS <multiplicative>

<multiplicative>  ::= <unary>
                    | <multiplicative> TIMES <unary>
                    | <multiplicative> DIVIDE <unary>
                    | <multiplicative> MOD <unary>

<unary>           ::= <atom>
                    | MINUS <unary>
                    | NOT <unary>

<atom>            ::= NUMBER_LIT
                    | DECIMAL_LIT
                    | STRING_LIT
                    | TRUE
                    | FALSE
                    | IDENTIFIER
                    | <function_call>
                    | LPAREN <expression> RPAREN
```

## Operator Precedence Table

| Precedence | Operators          | Associativity |
|:----------:|:------------------:|:-------------:|
| 1 (lowest) | `\|\|`             | Left          |
| 2          | `&&`               | Left          |
| 3          | `==` `!=`          | Left          |
| 4          | `>` `<` `>=` `<=`  | Left          |
| 5          | `+` `-`            | Left          |
| 6          | `*` `/` `%`        | Left          |
| 7 (highest)| `-` (unary) `!`    | Right         |
