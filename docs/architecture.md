# QXL Compiler Architecture

## System Overview

The QXL compiler follows a classical multi-phase pipeline architecture where source code flows through sequential transformation stages, each producing an intermediate representation consumed by the next.

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  QXL Source  │────▸│    Lexer     │────▸│   Parser     │
│   (.qxl)     │     │  (PLY Lex)   │     │  (PLY Yacc)  │
└──────────────┘     └──────┬───────┘     └──────┬───────┘
                            │                     │
                       Token Stream            AST Tree
                            │                     │
                            ▼                     ▼
                     ┌──────────────┐     ┌──────────────┐
                     │   Semantic   │◂────│  Symbol      │
                     │  Analyzer    │────▸│  Table       │
                     └──────┬───────┘     └──────────────┘
                            │
                       Validated AST
                            │
              ┌─────────────┼─────────────┐
              ▼                           ▼
       ┌──────────────┐           ┌──────────────┐
       │  IR Generator │           │ Python Code  │
       │  (TAC)        │           │  Generator   │
       └──────┬───────┘           └──────┬───────┘
              │                           │
        intermediate.txt            output.py
              │                           │
              ▼                           ▼
       ┌──────────────┐           ┌──────────────┐
       │  IDE Display  │           │  Executor    │
       │  (Frontend)   │           │ (subprocess) │
       └──────────────┘           └──────┬───────┘
                                         │
                                    Console Output
```

## Design Patterns

### Visitor Pattern
The Semantic Analyzer, IR Generator, and Python Code Generator all implement the Visitor pattern. Each AST node has an `accept(visitor)` method that dispatches to the visitor's `visit_NodeType` method.

### Error Collector
All compiler phases report errors through a shared `ErrorCollector` that aggregates errors without halting the pipeline, enabling comprehensive error reporting.

### Scope Stack
The Symbol Table uses a stack of `Scope` objects for lexical scoping. Entering a function, if-block, or loop pushes a new scope; exiting pops it.

## Module Dependency Graph

```
errors.py ◂── lexer.py ◂── parser.py
    ▲              ▲
    │              │
utils.py    ast_nodes.py ◂── semantic.py
                   ▲              ▲
                   │              │
            symbol_table.py      │
                   │              │
            intermediate.py      │
                   │              │
            generator.py         │
                   │              │
            executor.py          │
                   │              │
            app.py ◂─────────────┘
```

## API Architecture

The Flask backend serves as the orchestration layer:

1. **POST /compile** triggers the full pipeline and returns all artifacts
2. Individual **GET** endpoints serve cached results for tab switching
3. **POST /run** executes the generated Python in an isolated subprocess
4. **SQLite** stores programs, history, and sample programs
