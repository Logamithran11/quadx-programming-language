/**
 * QXL IDE — Monaco Editor Setup
 * ===============================
 * Initializes Monaco Editor with QXL language support including:
 *   - Syntax highlighting (keywords, operators, literals, comments)
 *   - Auto-completion for QXL keywords and snippets
 *   - Bracket matching and auto-indentation
 *   - Custom dark and light themes
 *   - Error marker integration
 *   - Cursor position tracking
 */

const QXLEditor = (() => {
    let editor = null;
    let monacoInstance = null;

    // ── QXL Language Definition ────────────────────────────
    const QXL_LANGUAGE_ID = 'qxl';

    const QXL_KEYWORDS = [
        'start', 'end', 'show', 'read',
        'number', 'decimal', 'text', 'bool',
        'if', 'otherwise', 'endif',
        'repeat', 'endrepeat',
        'function', 'return', 'endfunction',
        'break', 'continue', 'true', 'false'
    ];

    const QXL_TYPES = ['number', 'decimal', 'text', 'bool'];

    const QXL_BUILTINS = ['show', 'read'];

    /**
     * Register the QXL language with Monaco.
     */
    function registerLanguage(monaco) {
        monacoInstance = monaco;

        // Register the language
        monaco.languages.register({
            id: QXL_LANGUAGE_ID,
            extensions: ['.qxl'],
            aliases: ['QXL', 'qxl', 'QuadX'],
        });

        // Syntax highlighting (Monarch tokenizer)
        monaco.languages.setMonarchTokensProvider(QXL_LANGUAGE_ID, {
            keywords: QXL_KEYWORDS,
            typeKeywords: QXL_TYPES,

            operators: ['+', '-', '*', '/', '%', '>', '<', '>=', '<=', '==', '!=', '&&', '||', '!', '='],

            tokenizer: {
                root: [
                    // Comments
                    [/\/\/.*$/, 'comment'],
                    [/\/\*/, 'comment', '@comment'],

                    // Strings
                    [/"([^"\\]|\\.)*"/, 'string'],

                    // Numbers
                    [/\d+\.\d+/, 'number.float'],
                    [/\d+/, 'number'],

                    // Keywords and identifiers
                    [/[a-zA-Z_]\w*/, {
                        cases: {
                            '@keywords': 'keyword',
                            '@typeKeywords': 'type',
                            '@default': 'identifier'
                        }
                    }],

                    // Operators
                    [/[>=<!=]+/, 'operator'],
                    [/[+\-*\/%]/, 'operator'],
                    [/&&|\|\|/, 'operator'],
                    [/!/, 'operator'],
                    [/=/, 'operator'],

                    // Delimiters
                    [/[(),:]/, 'delimiter'],

                    // Whitespace
                    [/\s+/, 'white'],
                ],

                comment: [
                    [/[^/*]+/, 'comment'],
                    [/\*\//, 'comment', '@pop'],
                    [/[/*]/, 'comment'],
                ],
            },
        });

        // Auto-completion provider
        monaco.languages.registerCompletionItemProvider(QXL_LANGUAGE_ID, {
            provideCompletionItems: (model, position) => {
                const word = model.getWordUntilPosition(position);
                const range = {
                    startLineNumber: position.lineNumber,
                    endLineNumber: position.lineNumber,
                    startColumn: word.startColumn,
                    endColumn: word.endColumn,
                };

                const suggestions = [
                    // Keyword completions
                    ...QXL_KEYWORDS.map(kw => ({
                        label: kw,
                        kind: monaco.languages.CompletionItemKind.Keyword,
                        insertText: kw,
                        range,
                        detail: 'QXL Keyword',
                    })),

                    // Snippet completions
                    {
                        label: 'program',
                        kind: monaco.languages.CompletionItemKind.Snippet,
                        insertText: 'start\n\t${1:// your code here}\nend',
                        insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet,
                        range,
                        detail: 'QXL Program Template',
                        documentation: 'Creates a new QXL program block',
                    },
                    {
                        label: 'ifelse',
                        kind: monaco.languages.CompletionItemKind.Snippet,
                        insertText: 'if ${1:condition}\n\t${2:// then}\notherwise\n\t${3:// else}\nendif',
                        insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet,
                        range,
                        detail: 'If-Otherwise Block',
                    },
                    {
                        label: 'repeat',
                        kind: monaco.languages.CompletionItemKind.Snippet,
                        insertText: 'repeat ${1:condition}\n\t${2:// body}\nendrepeat',
                        insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet,
                        range,
                        detail: 'Repeat Loop',
                    },
                    {
                        label: 'func',
                        kind: monaco.languages.CompletionItemKind.Snippet,
                        insertText: 'function ${1:name}(${2:params})\n\t${3:// body}\n\treturn ${4:value}\nendfunction',
                        insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet,
                        range,
                        detail: 'Function Declaration',
                    },
                    {
                        label: 'vardecl',
                        kind: monaco.languages.CompletionItemKind.Snippet,
                        insertText: '${1|number,decimal,text,bool|} ${2:name} = ${3:value}',
                        insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet,
                        range,
                        detail: 'Variable Declaration',
                    },
                    {
                        label: 'show',
                        kind: monaco.languages.CompletionItemKind.Snippet,
                        insertText: 'show ${1:expression}',
                        insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet,
                        range,
                        detail: 'Output Statement',
                    },
                ];

                return { suggestions };
            },
        });

        // Language configuration (brackets, comments, auto-close)
        monaco.languages.setLanguageConfiguration(QXL_LANGUAGE_ID, {
            comments: {
                lineComment: '//',
                blockComment: ['/*', '*/'],
            },
            brackets: [['(', ')']],
            autoClosingPairs: [
                { open: '(', close: ')' },
                { open: '"', close: '"' },
                { open: '/*', close: '*/' },
            ],
            surroundingPairs: [
                { open: '(', close: ')' },
                { open: '"', close: '"' },
            ],
            indentationRules: {
                increaseIndentPattern: /^\s*(start|if|otherwise|repeat|function)\b/,
                decreaseIndentPattern: /^\s*(end|endif|endrepeat|endfunction|otherwise)\b/,
            },
        });
    }

    /**
     * Register custom editor themes.
     */
    function registerThemes(monaco) {
        monaco.editor.defineTheme('qxl-dark', {
            base: 'vs-dark',
            inherit: true,
            rules: [
                { token: 'keyword',       foreground: 'cba6f7', fontStyle: 'bold' },
                { token: 'type',          foreground: 'f9e2af', fontStyle: 'bold' },
                { token: 'string',        foreground: 'a6e3a1' },
                { token: 'number',        foreground: 'fab387' },
                { token: 'number.float',  foreground: 'fab387' },
                { token: 'comment',       foreground: '6c7086', fontStyle: 'italic' },
                { token: 'operator',      foreground: '89dceb' },
                { token: 'delimiter',     foreground: '9399b2' },
                { token: 'identifier',    foreground: 'cdd6f4' },
            ],
            colors: {
                'editor.background':                '#1e1e2e',
                'editor.foreground':                '#cdd6f4',
                'editor.lineHighlightBackground':   '#313244',
                'editor.selectionBackground':       '#45475a',
                'editor.inactiveSelectionBackground':'#31324480',
                'editorCursor.foreground':          '#f5e0dc',
                'editorLineNumber.foreground':      '#585b70',
                'editorLineNumber.activeForeground':'#a6adc8',
                'editorIndentGuide.background':     '#313244',
                'editorIndentGuide.activeBackground':'#45475a',
                'editorBracketMatch.background':    '#45475a80',
                'editorBracketMatch.border':        '#89b4fa',
                'editorWidget.background':          '#1e1e2e',
                'editorSuggestWidget.background':   '#1e1e2e',
                'editorSuggestWidget.border':       '#45475a',
                'editorSuggestWidget.selectedBackground': '#313244',
                'scrollbar.shadow':                 '#00000000',
                'scrollbarSlider.background':       '#45475a80',
                'scrollbarSlider.hoverBackground':  '#585b70',
                'scrollbarSlider.activeBackground':  '#6c7086',
            },
        });

        monaco.editor.defineTheme('qxl-light', {
            base: 'vs',
            inherit: true,
            rules: [
                { token: 'keyword',       foreground: '8839ef', fontStyle: 'bold' },
                { token: 'type',          foreground: 'df8e1d', fontStyle: 'bold' },
                { token: 'string',        foreground: '40a02b' },
                { token: 'number',        foreground: 'fe640b' },
                { token: 'number.float',  foreground: 'fe640b' },
                { token: 'comment',       foreground: '9ca0b0', fontStyle: 'italic' },
                { token: 'operator',      foreground: '179299' },
                { token: 'delimiter',     foreground: '7c7f93' },
                { token: 'identifier',    foreground: '4c4f69' },
            ],
            colors: {
                'editor.background':                '#eff1f5',
                'editor.foreground':                '#4c4f69',
                'editor.lineHighlightBackground':   '#e6e9ef',
                'editor.selectionBackground':       '#ccd0da',
                'editorCursor.foreground':          '#dc8a78',
                'editorLineNumber.foreground':      '#9ca0b0',
            },
        });
    }

    /**
     * Initialize the Monaco Editor instance.
     */
    function init() {
        return new Promise((resolve) => {
            require.config({
                paths: {
                    vs: 'https://cdn.jsdelivr.net/npm/monaco-editor@0.52.2/min/vs'
                }
            });

            require(['vs/editor/editor.main'], (monaco) => {
                registerLanguage(monaco);
                registerThemes(monaco);

                const container = document.getElementById('editor-container');

                editor = monaco.editor.create(container, {
                    value: getDefaultCode(),
                    language: QXL_LANGUAGE_ID,
                    theme: ThemeManager.current() === 'dark' ? 'qxl-dark' : 'qxl-light',

                    // Editor settings
                    fontSize: 14,
                    fontFamily: "'JetBrains Mono', 'Fira Code', 'Cascadia Code', monospace",
                    fontLigatures: true,
                    lineHeight: 22,
                    letterSpacing: 0.3,

                    // Features
                    minimap: { enabled: false },
                    scrollBeyondLastLine: false,
                    automaticLayout: true,
                    tabSize: 4,
                    insertSpaces: true,
                    wordWrap: 'on',
                    bracketPairColorization: { enabled: true },
                    guides: {
                        indentation: true,
                        bracketPairs: true,
                    },
                    renderLineHighlight: 'all',
                    cursorBlinking: 'smooth',
                    cursorSmoothCaretAnimation: 'on',
                    smoothScrolling: true,
                    padding: { top: 12, bottom: 12 },
                    roundedSelection: true,
                    suggest: {
                        showKeywords: true,
                        showSnippets: true,
                    },
                });

                // Track cursor position
                editor.onDidChangeCursorPosition((e) => {
                    const pos = e.position;
                    const posEl = document.getElementById('cursor-position');
                    if (posEl) {
                        posEl.textContent = `Ln ${pos.lineNumber}, Col ${pos.column}`;
                    }
                });

                // Track content changes
                editor.onDidChangeModelContent(() => {
                    const indicator = document.getElementById('unsaved-indicator');
                    if (indicator) indicator.style.display = 'inline';

                    const lineCount = editor.getModel().getLineCount();
                    const lineCountEl = document.getElementById('status-line-count');
                    if (lineCountEl) lineCountEl.textContent = `Lines: ${lineCount}`;
                });

                // Keyboard shortcuts
                editor.addCommand(monaco.KeyMod.CtrlCmd | monaco.KeyCode.KeyB, () => {
                    document.getElementById('btn-compile')?.click();
                });

                editor.addCommand(monaco.KeyMod.CtrlCmd | monaco.KeyCode.KeyR, () => {
                    document.getElementById('btn-run')?.click();
                });

                editor.addCommand(
                    monaco.KeyMod.CtrlCmd | monaco.KeyMod.Shift | monaco.KeyCode.KeyB,
                    () => {
                        document.getElementById('btn-compile-run')?.click();
                    }
                );

                resolve(editor);
            });
        });
    }

    /**
     * Get the current editor content.
     */
    function getValue() {
        return editor ? editor.getValue() : '';
    }

    /**
     * Set the editor content.
     */
    function setValue(code) {
        if (editor) {
            editor.setValue(code);
            const indicator = document.getElementById('unsaved-indicator');
            if (indicator) indicator.style.display = 'none';
        }
    }

    /**
     * Set editor theme.
     */
    function setTheme(themeName) {
        if (editor && monacoInstance) {
            monacoInstance.editor.setTheme(themeName);
        }
    }

    /**
     * Set error markers (squiggly underlines) on the editor.
     */
    function setMarkers(errors) {
        if (!editor || !monacoInstance) return;

        const model = editor.getModel();
        const markers = errors
            .filter(e => e.line > 0)
            .map(e => ({
                severity: e.severity === 'warning'
                    ? monacoInstance.MarkerSeverity.Warning
                    : monacoInstance.MarkerSeverity.Error,
                message: e.message + (e.suggestion ? `\n💡 ${e.suggestion}` : ''),
                startLineNumber: e.line,
                startColumn: e.column || 1,
                endLineNumber: e.line,
                endColumn: (e.column || 1) + 10,
            }));

        monacoInstance.editor.setModelMarkers(model, 'qxl', markers);
    }

    /**
     * Clear all error markers.
     */
    function clearMarkers() {
        if (editor && monacoInstance) {
            monacoInstance.editor.setModelMarkers(editor.getModel(), 'qxl', []);
        }
    }

    /**
     * Default code shown when the editor loads.
     */
    function getDefaultCode() {
        return `// ─── QuadX Programming Language ───
// Welcome to QXL! Press Ctrl+B to compile.

start
    // Variable declarations
    text greeting = "Hello, World!"
    number x = 10
    number y = 20

    // Output
    show greeting
    show x + y

    // Conditional
    if x < y
        show "x is less than y"
    otherwise
        show "x is not less than y"
    endif
end
`;
    }

    // Expose public API
    return { init, getValue, setValue, setTheme, setMarkers, clearMarkers };
})();

// Make globally accessible for theme manager
window.QXLEditor = QXLEditor;
