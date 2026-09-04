/**
 * QXL IDE — Main Application Controller
 * ========================================
 * Orchestrates the IDE: event binding, tab management, file operations,
 * console output, and wiring compile/run actions to the editor and backend.
 */

document.addEventListener('DOMContentLoaded', async () => {

    // ═════════════════════════════════════════════════════════
    // INITIALIZATION
    // ═════════════════════════════════════════════════════════

    // Initialize Monaco Editor
    await QXLEditor.init();

    // Check server connection
    checkServerConnection();

    // ═════════════════════════════════════════════════════════
    // TAB MANAGEMENT
    // ═════════════════════════════════════════════════════════

    // Output tabs
    document.querySelectorAll('.output-tab').forEach(tab => {
        tab.addEventListener('click', () => {
            // Deactivate all tabs and panes
            document.querySelectorAll('.output-tab').forEach(t => t.classList.remove('active'));
            document.querySelectorAll('.tab-pane').forEach(p => p.classList.remove('active'));

            // Activate clicked tab and corresponding pane
            tab.classList.add('active');
            const tabName = tab.dataset.tab;
            const pane = document.getElementById(`tab-${tabName}`);
            if (pane) pane.classList.add('active');
        });
    });

    // Console tabs
    document.querySelectorAll('.console-tab').forEach(tab => {
        tab.addEventListener('click', () => {
            document.querySelectorAll('.console-tab').forEach(t => t.classList.remove('active'));
            tab.classList.add('active');

            const consoleName = tab.dataset.console;
            const outputEl = document.getElementById('console-output');
            const errorsEl = document.getElementById('console-errors');

            if (consoleName === 'output') {
                outputEl.style.display = 'block';
                errorsEl.style.display = 'none';
            } else {
                outputEl.style.display = 'none';
                errorsEl.style.display = 'block';
            }
        });
    });

    // ═════════════════════════════════════════════════════════
    // COMPILE
    // ═════════════════════════════════════════════════════════

    document.getElementById('btn-compile').addEventListener('click', async () => {
        await handleCompile();
    });

    async function handleCompile() {
        const code = QXLEditor.getValue();
        if (!code.trim()) {
            logConsole('⚠ No code to compile.', 'warning');
            return null;
        }

        // UI: show compiling state
        const btn = document.getElementById('btn-compile');
        btn.classList.add('compiling');
        btn.disabled = true;
        QXLEditor.clearMarkers();

        logConsole('⟳ Compiling...', 'info');

        try {
            const result = await QXLCompiler.compile(code);

            // Render all output panels
            try {
                QXLCompiler.renderAll(result);
            } catch (renderError) {
                logConsole(`✗ UI Render Error: ${renderError.message}`, 'error');
                console.error("Render Error:", renderError);
            }

            // Handle errors
            if (result.errors && result.errors.length > 0) {
                QXLEditor.setMarkers(result.errors);
                renderErrors(result.errors);
                showErrorBadge(result.errors.filter(e => e.severity === 'error').length);
            } else {
                clearErrors();
                hideErrorBadge();
            }

            // Console feedback
            if (result.success) {
                logConsole(`✓ Compilation successful (${result.statistics.total_ms}ms)`, 'success');
                logConsole(`  Tokens: ${result.statistics.token_count} | IR: ${result.statistics.ir_instruction_count || 0} instructions`, 'info');

                // Update status bar
                const compileTimeEl = document.getElementById('status-compile-time');
                if (compileTimeEl) compileTimeEl.textContent = `Compiled: ${result.statistics.total_ms}ms`;
            } else {
                logConsole(`✗ Compilation failed with ${result.errors.length} error(s)`, 'error');
                result.errors.forEach(err => {
                    const loc = err.line ? ` [line ${err.line}]` : '';
                    logConsole(`  ${err.phase}${loc}: ${err.message}`, 'error');
                    if (err.suggestion) {
                        logConsole(`  💡 ${err.suggestion}`, 'info');
                    }
                });
            }

            return result;
        } catch (error) {
            logConsole(`✗ ${error.message}`, 'error');
            return null;
        } finally {
            btn.classList.remove('compiling');
            btn.disabled = false;
        }
    }

    // ═════════════════════════════════════════════════════════
    // RUN
    // ═════════════════════════════════════════════════════════

    document.getElementById('btn-run').addEventListener('click', async () => {
        await handleRun();
    });

    async function handleRun() {
        logConsole('▸ Running...', 'info');

        try {
            const result = await QXLCompiler.run();

            if (result.success) {
                if (result.output) {
                    logConsole('─── Program Output ───', 'info');
                    result.output.split('\n').forEach(line => {
                        if (line) logConsole(line, 'success');
                    });
                } else {
                    logConsole('(no output)', 'info');
                }
                logConsole(`▸ Finished in ${result.execution_time_ms}ms (exit code: ${result.exit_code})`, 'info');
            } else {
                logConsole('✗ Runtime error:', 'error');
                logConsole(`  ${result.errors}`, 'error');
            }
        } catch (error) {
            logConsole(`✗ ${error.message}`, 'error');
        }
    }

    // ═════════════════════════════════════════════════════════
    // COMPILE & RUN
    // ═════════════════════════════════════════════════════════

    document.getElementById('btn-compile-run').addEventListener('click', async () => {
        const result = await handleCompile();
        if (result && result.success) {
            await handleRun();
        }
    });

    // ═════════════════════════════════════════════════════════
    // CLEAR
    // ═════════════════════════════════════════════════════════

    document.getElementById('btn-clear').addEventListener('click', () => {
        clearConsole();
        clearErrors();
        hideErrorBadge();
        QXLEditor.clearMarkers();
        logConsole('▸ Console cleared.', 'info');
    });

    document.getElementById('btn-clear-console').addEventListener('click', () => {
        clearConsole();
    });

    // ═════════════════════════════════════════════════════════
    // FILE OPERATIONS
    // ═════════════════════════════════════════════════════════

    // Open file
    document.getElementById('btn-open').addEventListener('click', () => {
        document.getElementById('file-input').click();
    });

    document.getElementById('file-input').addEventListener('change', (e) => {
        const file = e.target.files[0];
        if (!file) return;

        const reader = new FileReader();
        reader.onload = (event) => {
            QXLEditor.setValue(event.target.result);
            document.getElementById('editor-filename').textContent = file.name;
            logConsole(`▸ Opened: ${file.name}`, 'info');
        };
        reader.readAsText(file);
        e.target.value = ''; // Reset for re-opening same file
    });

    // Save file
    document.getElementById('btn-save').addEventListener('click', () => {
        const modal = new bootstrap.Modal(document.getElementById('saveModal'));
        modal.show();
    });

    document.getElementById('btn-save-confirm').addEventListener('click', async () => {
        const name = document.getElementById('save-name').value.trim();
        if (!name) return;

        const code = QXLEditor.getValue();

        try {
            const response = await fetch('/programs', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name, code }),
            });
            const result = await response.json();
            logConsole(`▸ Saved: ${name} (ID: ${result.id})`, 'success');

            document.getElementById('editor-filename').textContent = `${name}.qxl`;
            document.getElementById('unsaved-indicator').style.display = 'none';

            bootstrap.Modal.getInstance(document.getElementById('saveModal')).hide();
        } catch (error) {
            logConsole(`✗ Save failed: ${error.message}`, 'error');
        }
    });

    // Download Python
    document.getElementById('btn-download').addEventListener('click', () => {
        const result = QXLCompiler.getLastResult();
        if (!result || !result.generated_python) {
            logConsole('⚠ No Python code to download. Compile first.', 'warning');
            return;
        }

        const blob = new Blob([result.generated_python], { type: 'text/plain' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'output.py';
        a.click();
        URL.revokeObjectURL(url);

        logConsole('▸ Downloaded output.py', 'success');
    });

    // ═════════════════════════════════════════════════════════
    // SAMPLE PROGRAMS
    // ═════════════════════════════════════════════════════════

    document.querySelectorAll('[data-example]').forEach(item => {
        item.addEventListener('click', async (e) => {
            e.preventDefault();
            const name = item.dataset.example;

            try {
                const result = await QXLCompiler.loadExample(name);
                if (result.code) {
                    QXLEditor.setValue(result.code);
                    document.getElementById('editor-filename').textContent = `${name}.qxl`;
                    logConsole(`▸ Loaded example: ${name}`, 'info');
                } else {
                    logConsole(`⚠ Example '${name}' not found`, 'warning');
                }
            } catch (error) {
                logConsole(`✗ Failed to load example: ${error.message}`, 'error');
            }
        });
    });

    // ═════════════════════════════════════════════════════════
    // THEME TOGGLE
    // ═════════════════════════════════════════════════════════

    document.getElementById('btn-theme').addEventListener('click', () => {
        ThemeManager.toggle();
    });

    // ═════════════════════════════════════════════════════════
    // CONSOLE TOGGLE
    // ═════════════════════════════════════════════════════════

    document.getElementById('btn-toggle-console').addEventListener('click', () => {
        const consolePanel = document.getElementById('console-panel');
        const icon = document.querySelector('#btn-toggle-console i');

        if (consolePanel.style.height === '36px') {
            consolePanel.style.height = 'var(--console-height)';
            icon.className = 'bi bi-chevron-down';
        } else {
            consolePanel.style.height = '36px';
            icon.className = 'bi bi-chevron-up';
        }
    });

    // ═════════════════════════════════════════════════════════
    // CONSOLE OUTPUT HELPERS
    // ═════════════════════════════════════════════════════════

    function logConsole(message, type = '') {
        const output = document.getElementById('console-output');
        const line = document.createElement('div');
        line.className = `console-line ${type}`;

        const prefix = document.createElement('span');
        prefix.className = 'console-prefix';
        prefix.textContent = type === 'error' ? '✗' : type === 'success' ? '✓' : type === 'warning' ? '⚠' : '▸';

        const text = document.createElement('span');
        text.textContent = message;

        line.appendChild(prefix);
        line.appendChild(text);
        output.appendChild(line);

        // Auto-scroll to bottom
        output.scrollTop = output.scrollHeight;
    }

    function clearConsole() {
        const output = document.getElementById('console-output');
        output.innerHTML = '';
    }

    function renderErrors(errors) {
        const container = document.getElementById('console-errors');
        container.innerHTML = '';

        errors.forEach(err => {
            const item = document.createElement('div');
            item.className = 'error-item';

            const isWarning = err.severity === 'warning';
            const iconClass = isWarning ? 'warning-icon' : 'error-icon';
            const icon = isWarning ? 'bi-exclamation-triangle-fill' : 'bi-x-circle-fill';

            let html = `<i class="bi ${icon} ${iconClass}"></i><div>`;
            html += `<div class="error-message">${QXLCompiler.escapeHtml(err.message)}</div>`;
            if (err.line) {
                html += `<div class="error-location">${err.phase} — line ${err.line}${err.column ? `, col ${err.column}` : ''}</div>`;
            }
            if (err.suggestion) {
                html += `<div class="error-suggestion">💡 ${QXLCompiler.escapeHtml(err.suggestion)}</div>`;
            }
            html += '</div>';

            item.innerHTML = html;
            container.appendChild(item);
        });
    }

    function clearErrors() {
        document.getElementById('console-errors').innerHTML = '';
    }

    function showErrorBadge(count) {
        const badge = document.getElementById('error-count');
        if (badge) {
            badge.textContent = count;
            badge.style.display = count > 0 ? 'inline' : 'none';
        }
    }

    function hideErrorBadge() {
        const badge = document.getElementById('error-count');
        if (badge) badge.style.display = 'none';
    }

    // ═════════════════════════════════════════════════════════
    // SERVER CONNECTION CHECK
    // ═════════════════════════════════════════════════════════

    async function checkServerConnection() {
        const statusEl = document.getElementById('status-connection');
        try {
            await fetch('/tokens', { method: 'GET' });
            statusEl.innerHTML = '<i class="bi bi-circle-fill status-dot connected"></i> Connected';
        } catch {
            statusEl.innerHTML = '<i class="bi bi-circle-fill status-dot disconnected"></i> Disconnected';
            logConsole('⚠ Backend server not responding', 'warning');
            logConsole('  Run: python backend/app.py', 'info');
        }
    }
});
