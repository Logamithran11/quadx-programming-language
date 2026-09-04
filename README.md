# ◆ QuadX Programming Language (QXL)

**Design and Implementation of a Custom Programming Language and Compiler**

> A complete compiler, IDE, and execution environment for a custom programming language — from lexical analysis to code generation and execution.

---

## 🎯 Overview

QXL is a fully functional programming language with a complete compiler pipeline, VS Code-inspired IDE, and Python code generation. The project demonstrates every classical phase of compilation: lexical analysis, syntax analysis (parsing), semantic analysis, intermediate code generation, target code generation, and execution.

### Key Features

- **Complete Compiler Pipeline** — Lexer → Parser → Semantic Analyzer → IR Generator → Code Generator → Executor
- **VS Code-Inspired IDE** — Monaco Editor with syntax highlighting, auto-completion, error markers
- **7 Compiler Phases Visualized** — Tokens, Parse Tree, AST, Symbol Table, Intermediate Code, Generated Python, Statistics
- **Python Code Generation** — QXL programs compile to executable Python
- **Real-time Error Diagnostics** — Line-level errors with fix suggestions
- **Sample Programs** — 6 ready-to-compile examples
- **Dark/Light Themes** — Premium glassmorphism UI

---

## 🛠 Tech Stack

| Layer      | Technology              |
|------------|-------------------------|
| Frontend   | HTML5, CSS3, JavaScript |
| Editor     | Monaco Editor           |
| UI         | Bootstrap 5, Chart.js   |
| Backend    | Python 3.12+, Flask     |
| Compiler   | PLY (Python Lex-Yacc)   |
| Graphs     | Graphviz                |
| Database   | SQLite                  |

---

## 📁 Project Structure

```
QUADX (QPL)/
├── backend/
│   ├── app.py              # Flask API server
│   ├── lexer.py            # Lexical analyzer (PLY Lex)
│   ├── parser.py           # Syntax analyzer (PLY Yacc)
│   ├── semantic.py         # Semantic analyzer (Visitor pattern)
│   ├── symbol_table.py     # Symbol table with scope stack
│   ├── intermediate.py     # Three-address code IR generator
│   ├── generator.py        # Python code generator
│   ├── executor.py         # Sandboxed code executor
│   ├── ast_nodes.py        # 23 AST node types
│   ├── grammar.py          # Formal grammar specification
│   ├── errors.py           # Error type hierarchy
│   └── utils.py            # Utility functions
├── frontend/
│   ├── index.html          # IDE layout
│   ├── style.css           # Premium dark theme
│   ├── app.js              # Application controller
│   ├── editor.js           # Monaco Editor setup
│   ├── compiler.js         # Compiler API interface
│   └── theme.js            # Theme manager
├── examples/               # Sample QXL programs
├── tests/                  # Unit tests (pytest)
├── docs/                   # Documentation
├── generated/              # Compiler output (auto-created)
├── graph/                  # Graphviz output (auto-created)
├── requirements.txt
├── LICENSE
└── README.md
```

---

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Start the Backend Server

```bash
python backend/app.py
```

### 3. Open the IDE

Open `frontend/index.html` in your web browser.

### 4. Write & Compile

```qxl
start
    show "Hello, World!"
end
```

Press **Ctrl+B** to compile and **Ctrl+R** to run.

---

## 📝 QXL Language Overview

### Hello World
```qxl
start
    show "Hello, World!"
end
```

### Variables & Arithmetic
```qxl
start
    number a = 10
    number b = 20
    show a + b
end
```

### Functions
```qxl
start
    function factorial(number n)
        number result = 1
        number i = 1
        repeat i <= n
            result = result * i
            i = i + 1
        endrepeat
        return result
    endfunction

    show factorial(5)
end
```

### Control Flow
```qxl
start
    number x = 42
    if x > 10
        show "big"
    otherwise
        show "small"
    endif
end
```

---

## 🔧 Compiler Pipeline

```
QXL Source → Lexer → Parser → Semantic → IR Gen → Python Gen → Executor
   .qxl      tokens    AST    validated   TAC      output.py    stdout
```

| Phase                  | Module              | Output                  |
|------------------------|---------------------|-------------------------|
| Lexical Analysis       | `lexer.py`          | Token stream            |
| Syntax Analysis        | `parser.py`         | Abstract Syntax Tree    |
| Semantic Analysis      | `semantic.py`       | Validated AST + Symbols |
| Intermediate Code Gen  | `intermediate.py`   | Three-Address Code      |
| Python Code Generation | `generator.py`      | `output.py`             |
| Execution              | `executor.py`       | Console output          |

---

## 🧪 Testing

```bash
python -m pytest tests/ -v
```

Tests cover all compiler phases: Lexer (17 tests), Parser (15 tests), Semantic Analyzer (14 tests), and Code Generator (16 tests).

---

## 📚 Documentation

- [Grammar Specification](docs/grammar.md) — Formal BNF grammar
- [Architecture](docs/architecture.md) — System design and patterns
- [Language Reference](docs/language_reference.md) — Complete QXL reference
- [User Manual](docs/user_manual.md) — Installation and usage guide

---

## 🎨 Design

The IDE features a premium dark theme inspired by Catppuccin Mocha with:
- Glassmorphism effects
- Smooth micro-animations
- Professional typography (Inter + JetBrains Mono)
- Responsive CSS Grid layout
- Chart.js compilation statistics

---

## 📄 License

MIT License — see [LICENSE](LICENSE).
