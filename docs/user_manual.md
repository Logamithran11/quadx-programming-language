# QXL User Manual

## Installation

### Prerequisites
- Python 3.12 or higher
- pip (Python package manager)
- A modern web browser (Chrome, Firefox, Edge)
- Graphviz (optional, for parse tree visualization)

### Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd "QUADX (QPL)"
   ```

2. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Install Graphviz** (optional, for visual trees)
   - Windows: Download from https://graphviz.org/download/ and add to PATH
   - macOS: `brew install graphviz`
   - Linux: `sudo apt install graphviz`

4. **Start the backend server**
   ```bash
   python backend/app.py
   ```
   The server runs at `http://localhost:5000`

5. **Open the IDE**
   Open `frontend/index.html` in your browser.

---

## Using the IDE

### Writing Code
The left panel contains a Monaco-based code editor with:
- **Syntax highlighting** for all QXL keywords
- **Auto-completion** — type a keyword and press Tab
- **Snippets** — type `program`, `ifelse`, `repeat`, `func` for templates
- **Bracket matching** and auto-indentation
- **Error markers** — red squiggly underlines on errors

### Compiling
- Click **Compile** or press `Ctrl+B`
- The right panel shows compilation artifacts in tabs:
  - **Tokens** — list of all tokens with types and positions
  - **Parse Tree** — visual tree (requires Graphviz)
  - **AST** — abstract syntax tree as interactive JSON view
  - **Symbols** — symbol table with variables and functions
  - **IR Code** — three-address code intermediate representation
  - **Python** — generated Python source code
  - **Stats** — compilation statistics with timing chart

### Running
- Click **Run** or press `Ctrl+R` to execute the generated Python
- Click **Compile & Run** or press `Ctrl+Shift+B` for both steps
- Output appears in the console panel at the bottom

### File Operations
- **Open** — load a `.qxl` file from disk
- **Save** — save to the database
- **Download** — download the generated Python as `output.py`

### Sample Programs
Click the code icon (⊞) in the top-right to load examples:
- Hello World, Calculator, Loop, Factorial, Fibonacci, Functions

### Theme
Toggle between dark and light themes using the moon/sun icon.

---

## Keyboard Shortcuts

| Shortcut           | Action          |
|--------------------|-----------------|
| `Ctrl+B`           | Compile         |
| `Ctrl+R`           | Run             |
| `Ctrl+Shift+B`     | Compile & Run   |
| `Ctrl+/`           | Toggle Comment  |
| `Ctrl+D`           | Duplicate Line  |
| `Ctrl+Space`       | Auto-Complete   |

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "Disconnected" in status bar | Make sure `python backend/app.py` is running |
| No parse tree image | Install Graphviz and add to PATH |
| ModuleNotFoundError | Run `pip install -r requirements.txt` |
| Port 5000 in use | Change the port in `backend/app.py` |

---

## Running Tests

```bash
python -m pytest tests/ -v
```
