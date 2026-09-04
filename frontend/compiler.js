/**
 * QXL IDE — Compiler Interface
 * =============================
 * Handles communication with the Flask backend API and renders
 * compilation results into the IDE output panels.
 */

const QXLCompiler = (() => {
    const API_BASE = 'http://localhost:5000';

    let lastResult = null;
    let statsChart = null;

    // ═════════════════════════════════════════════════════════
    // API CALLS
    // ═════════════════════════════════════════════════════════

    /**
     * Send source code to the backend for compilation.
     */
    async function compile(code) {
        try {
            const response = await fetch(`${API_BASE}/compile`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ code }),
            });
            lastResult = await response.json();
            return lastResult;
        } catch (error) {
            throw new Error(`Connection failed: ${error.message}. Is the server running?`);
        }
    }

    /**
     * Execute the generated Python code.
     */
    async function run(userInput = '') {
        try {
            const response = await fetch(`${API_BASE}/run`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ input: userInput }),
            });
            return await response.json();
        } catch (error) {
            throw new Error(`Execution failed: ${error.message}`);
        }
    }

    /**
     * Load a sample program by name.
     */
    async function loadExample(name) {
        try {
            const response = await fetch(`${API_BASE}/examples/${name}`);
            return await response.json();
        } catch (error) {
            throw new Error(`Failed to load example: ${error.message}`);
        }
    }

    // ═════════════════════════════════════════════════════════
    // RENDER FUNCTIONS
    // ═════════════════════════════════════════════════════════

    /**
     * Render tokens into the Tokens tab.
     */
    function renderTokens(tokens) {
        const container = document.getElementById('tab-tokens');
        if (!tokens || tokens.length === 0) {
            container.innerHTML = '<div class="empty-state"><i class="bi bi-list-ul"></i><p>No tokens generated</p></div>';
            return;
        }

        // Categorize tokens for color-coding
        const keywordTypes = new Set([
            'START', 'END', 'SHOW', 'READ', 'NUMBER', 'DECIMAL', 'TEXT', 'BOOL',
            'IF', 'OTHERWISE', 'ENDIF', 'REPEAT', 'ENDREPEAT', 'FUNCTION',
            'RETURN', 'ENDFUNCTION', 'BREAK', 'CONTINUE', 'TRUE', 'FALSE'
        ]);
        const operatorTypes = new Set([
            'PLUS', 'MINUS', 'TIMES', 'DIVIDE', 'MOD', 'GT', 'LT', 'GTE',
            'LTE', 'EQEQ', 'NEQ', 'AND', 'OR', 'NOT', 'ASSIGN'
        ]);
        const literalTypes = new Set(['NUMBER_LIT', 'DECIMAL_LIT', 'STRING_LIT']);

        let html = `<table class="token-table">
            <thead><tr>
                <th>#</th><th>Type</th><th>Value</th><th>Line</th><th>Col</th>
            </tr></thead><tbody>`;

        tokens.forEach((tok, i) => {
            let typeClass = 'token-type';
            if (keywordTypes.has(tok.type)) typeClass = 'token-keyword';
            else if (operatorTypes.has(tok.type)) typeClass = 'token-operator';
            else if (literalTypes.has(tok.type)) typeClass = 'token-literal';

            const value = typeof tok.value === 'string' && tok.value.length > 30
                ? tok.value.substring(0, 27) + '...'
                : tok.value;

            html += `<tr>
                <td style="color:var(--text-muted)">${i + 1}</td>
                <td class="${typeClass}">${tok.type}</td>
                <td class="token-value">${escapeHtml(String(value))}</td>
                <td>${tok.line}</td>
                <td>${tok.column}</td>
            </tr>`;
        });

        html += '</tbody></table>';
        container.innerHTML = html;
    }

    /**
     * Render the parse tree image or fallback.
     */
    function renderParseTree(base64Image) {
        const container = document.getElementById('tab-parse-tree');
        if (base64Image) {
            container.innerHTML = `<div class="tree-image-container">
                <img src="data:image/png;base64,${base64Image}" alt="Parse Tree">
            </div>`;
        } else {
            container.innerHTML = '<div class="empty-state"><i class="bi bi-diagram-3"></i><p>Parse tree visualization requires Graphviz.<br>Install it for visual trees.</p></div>';
        }
    }

    /**
     * Render the AST as an interactive tree view.
     */
    function renderAST(ast, base64Image) {
        const container = document.getElementById('tab-ast');
        if (!ast) {
            container.innerHTML = '<div class="empty-state"><i class="bi bi-tree"></i><p>No AST available</p></div>';
            return;
        }

        // If we have an image, show both the image and JSON tree
        let html = '';
        if (base64Image) {
            html += `<div class="tree-image-container" style="max-height:400px;margin-bottom:16px;">
                <img src="data:image/png;base64,${base64Image}" alt="AST">
            </div>`;
        }

        html += '<div class="ast-tree">';
        html += renderASTNode(ast, 0);
        html += '</div>';

        container.innerHTML = html;
    }

    /**
     * Recursively render an AST node as HTML.
     */
    function renderASTNode(node, depth) {
        if (!node || typeof node !== 'object') return '';
        if (Array.isArray(node)) {
            return node.map(n => renderASTNode(n, depth)).join('');
        }

        const nodeType = node.node_type || 'Unknown';
        let info = '';

        // Extract meaningful properties
        if (node.name) info += ` <span class="ast-node-value">${escapeHtml(node.name)}</span>`;
        if (node.op) info += ` <span class="ast-node-prop">[${escapeHtml(node.op)}]</span>`;
        if (node.value !== undefined && node.value !== null && typeof node.value !== 'object') {
            info += ` <span class="ast-node-value">= ${escapeHtml(String(node.value))}</span>`;
        }
        if (node.var_type) info += ` <span class="ast-node-prop">: ${node.var_type}</span>`;

        let html = `<div class="ast-node" style="padding-left:${depth * 18}px">`;
        html += `<div class="ast-node-label">
            <span class="ast-node-type">${nodeType.replace('Node', '')}</span>${info}
        </div>`;

        // Recurse into children
        for (const [key, value] of Object.entries(node)) {
            if (['node_type', 'line', 'column', 'name', 'op', 'value', 'var_type', 'param_type'].includes(key)) continue;
            if (Array.isArray(value)) {
                value.forEach(child => {
                    if (child && typeof child === 'object' && child.node_type) {
                        html += renderASTNode(child, depth + 1);
                    }
                });
            } else if (value && typeof value === 'object' && value.node_type) {
                html += renderASTNode(value, depth + 1);
            }
        }

        html += '</div>';
        return html;
    }

    /**
     * Render the symbol table.
     */
    function renderSymbolTable(symbolTable) {
        const container = document.getElementById('tab-symbol-table');
        if (!symbolTable) {
            container.innerHTML = '<div class="empty-state"><i class="bi bi-table"></i><p>No symbol table available</p></div>';
            return;
        }

        let html = '';

        // Variables section
        if (symbolTable.variables && symbolTable.variables.length > 0) {
            html += `<div class="symbol-section">
                <div class="symbol-section-title">Variables (${symbolTable.variables.length})</div>
                <table class="symbol-table">
                    <thead><tr><th>Name</th><th>Type</th><th>Scope</th><th>Line</th><th>Init</th></tr></thead>
                    <tbody>`;
            symbolTable.variables.forEach(v => {
                const initIcon = v.initialized
                    ? '<span style="color:var(--accent-green)">✓</span>'
                    : '<span style="color:var(--accent-red)">✗</span>';
                html += `<tr>
                    <td style="color:var(--accent-lavender);font-weight:500">${escapeHtml(v.name)}</td>
                    <td style="color:var(--accent-yellow)">${v.type}</td>
                    <td style="color:var(--text-muted)">${escapeHtml(v.scope)}</td>
                    <td>${v.line}</td>
                    <td>${initIcon}</td>
                </tr>`;
            });
            html += '</tbody></table></div>';
        }

        // Functions section
        if (symbolTable.functions && symbolTable.functions.length > 0) {
            html += `<div class="symbol-section">
                <div class="symbol-section-title">Functions (${symbolTable.functions.length})</div>
                <table class="symbol-table">
                    <thead><tr><th>Name</th><th>Params</th><th>Line</th><th>Returns</th></tr></thead>
                    <tbody>`;
            symbolTable.functions.forEach(f => {
                const params = f.params.map(p => `${p.type} ${p.name}`).join(', ') || 'none';
                const retIcon = f.has_return
                    ? '<span style="color:var(--accent-green)">✓</span>'
                    : '<span style="color:var(--text-muted)">—</span>';
                html += `<tr>
                    <td style="color:var(--accent-green);font-weight:500">${escapeHtml(f.name)}</td>
                    <td style="color:var(--text-secondary)">${escapeHtml(params)}</td>
                    <td>${f.line}</td>
                    <td>${retIcon}</td>
                </tr>`;
            });
            html += '</tbody></table></div>';
        }

        // Summary
        html += `<div class="symbol-section" style="margin-top:12px;">
            <div style="font-size:11px;color:var(--text-muted);">
                Total: ${symbolTable.variable_count || 0} variables, 
                ${symbolTable.function_count || 0} functions, 
                ${symbolTable.scope_count || 0} scopes
            </div>
        </div>`;

        container.innerHTML = html;
    }

    /**
     * Render intermediate code (TAC).
     */
    function renderIntermediate(tacText) {
        const container = document.getElementById('tab-intermediate');
        if (!tacText) {
            container.innerHTML = '<div class="empty-state"><i class="bi bi-cpu"></i><p>No intermediate code generated</p></div>';
            return;
        }

        // Syntax highlight the TAC
        const highlighted = tacText
            .replace(/\b(GOTO|IF_FALSE|LABEL|CALL|RETURN|PARAM|PRINT|READ|FUNC_BEGIN|FUNC_END)\b/g,
                '<span class="keyword">$1</span>')
            .replace(/\b(ADD|SUB|MUL|DIV|MOD|GT|LT|GTE|LTE|EQ|NEQ|AND|OR|NOT|NEG|ASSIGN)\b/g,
                '<span class="operator">$1</span>')
            .replace(/\b(t\d+)\b/g, '<span class="function">$1</span>')
            .replace(/\b(L\d+)\b/g, '<span class="number">$1</span>')
            .replace(/"([^"]*)"/g, '<span class="string">"$1"</span>');

        container.innerHTML = `<div class="code-display">${highlighted}</div>`;
    }

    /**
     * Render generated Python code with syntax highlighting.
     */
    function renderGeneratedPython(pythonCode) {
        const container = document.getElementById('tab-generated');
        if (!pythonCode) {
            container.innerHTML = '<div class="empty-state"><i class="bi bi-filetype-py"></i><p>No Python code generated</p></div>';
            return;
        }

        // Simple Python syntax highlighting
        const highlighted = escapeHtml(pythonCode)
            .replace(/\b(def|return|if|else|elif|while|for|break|continue|pass|print|input|True|False|None|and|or|not|in)\b/g,
                '<span class="keyword">$1</span>')
            .replace(/(#[^\n]*)/g, '<span class="comment">$1</span>')
            .replace(/"([^"]*)"/g, '<span class="string">"$1"</span>')
            .replace(/\b(\d+\.?\d*)\b/g, '<span class="number">$1</span>');

        container.innerHTML = `<div class="code-display">${highlighted}</div>`;
    }

    /**
     * Render compilation statistics with Chart.js.
     */
    function renderStatistics(stats) {
        const container = document.getElementById('tab-statistics');
        if (!stats) {
            container.innerHTML = '<div class="empty-state"><i class="bi bi-bar-chart-fill"></i><p>No statistics available</p></div>';
            return;
        }

        let html = '<div class="stats-grid">';

        const cards = [
            { label: 'Total Time', value: stats.total_ms || 0, unit: 'ms', accent: 'accent-blue' },
            { label: 'Tokens', value: stats.token_count || 0, unit: 'tokens', accent: 'accent-green' },
            { label: 'Lexer', value: stats.lexer_ms || 0, unit: 'ms', accent: 'accent-mauve' },
            { label: 'Parser', value: stats.parser_ms || 0, unit: 'ms', accent: 'accent-peach' },
            { label: 'Semantic', value: stats.semantic_ms || 0, unit: 'ms', accent: 'accent-teal' },
            { label: 'IR Gen', value: stats.ir_ms || 0, unit: 'ms', accent: 'accent-blue' },
            { label: 'Code Gen', value: stats.codegen_ms || 0, unit: 'ms', accent: 'accent-green' },
            { label: 'IR Instructions', value: stats.ir_instruction_count || 0, unit: 'instructions', accent: 'accent-mauve' },
        ];

        cards.forEach(card => {
            html += `<div class="stat-card ${card.accent}">
                <div class="stat-label">${card.label}</div>
                <div class="stat-value">${card.value}<span class="stat-unit"> ${card.unit}</span></div>
            </div>`;
        });

        html += '</div>';

        // Phase timing chart
        html += '<div class="chart-container"><canvas id="stats-chart"></canvas></div>';
        container.innerHTML = html;

        // Create Chart.js bar chart
        const ctx = document.getElementById('stats-chart');
        if (ctx && typeof Chart !== 'undefined') {
            if (statsChart) statsChart.destroy();

            statsChart = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: ['Lexer', 'Parser', 'Semantic', 'IR Gen', 'Code Gen', 'Visualization'],
                    datasets: [{
                        label: 'Phase Time (ms)',
                        data: [
                            stats.lexer_ms || 0,
                            stats.parser_ms || 0,
                            stats.semantic_ms || 0,
                            stats.ir_ms || 0,
                            stats.codegen_ms || 0,
                            stats.visualization_ms || 0,
                        ],
                        backgroundColor: [
                            'rgba(203, 166, 247, 0.7)',
                            'rgba(250, 179, 135, 0.7)',
                            'rgba(148, 226, 213, 0.7)',
                            'rgba(137, 180, 250, 0.7)',
                            'rgba(166, 227, 161, 0.7)',
                            'rgba(249, 226, 175, 0.7)',
                        ],
                        borderColor: [
                            'rgb(203, 166, 247)',
                            'rgb(250, 179, 135)',
                            'rgb(148, 226, 213)',
                            'rgb(137, 180, 250)',
                            'rgb(166, 227, 161)',
                            'rgb(249, 226, 175)',
                        ],
                        borderWidth: 1,
                        borderRadius: 4,
                    }],
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: true,
                    plugins: {
                        legend: { display: false },
                    },
                    scales: {
                        y: {
                            beginAtZero: true,
                            title: { display: true, text: 'Time (ms)', color: '#6c7086' },
                            ticks: { color: '#6c7086' },
                            grid: { color: 'rgba(69, 71, 90, 0.3)' },
                        },
                        x: {
                            ticks: { color: '#a6adc8', font: { size: 10 } },
                            grid: { display: false },
                        },
                    },
                },
            });
        }
    }

    /**
     * Render all compilation results at once.
     */
    function renderAll(result) {
        renderTokens(result.tokens);
        renderParseTree(result.parse_tree);
        renderAST(result.ast, result.ast_image);
        renderSymbolTable(result.symbol_table);
        renderIntermediate(result.intermediate);
        renderGeneratedPython(result.generated_python);
        renderStatistics(result.statistics);
    }

    // ═════════════════════════════════════════════════════════
    // HELPERS
    // ═════════════════════════════════════════════════════════

    function escapeHtml(str) {
        const div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    }

    function getLastResult() {
        return lastResult;
    }

    return { compile, run, loadExample, renderAll, renderTokens, renderParseTree, renderAST, renderSymbolTable, renderIntermediate, renderGeneratedPython, renderStatistics, getLastResult, escapeHtml };
})();
