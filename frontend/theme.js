/**
 * QXL IDE — Theme Manager
 * ========================
 * Handles dark/light theme toggling with localStorage persistence.
 */

const ThemeManager = (() => {
    const STORAGE_KEY = 'qxl-theme';
    const DARK = 'dark';
    const LIGHT = 'light';

    /**
     * Initialize theme from localStorage or default to dark.
     */
    function init() {
        const saved = localStorage.getItem(STORAGE_KEY) || DARK;
        apply(saved);
        updateIcon(saved);
    }

    /**
     * Toggle between dark and light themes.
     */
    function toggle() {
        const current = document.documentElement.getAttribute('data-theme');
        const next = current === DARK ? LIGHT : DARK;
        apply(next);
        updateIcon(next);
        localStorage.setItem(STORAGE_KEY, next);
    }

    /**
     * Apply a theme by setting the data-theme attribute.
     */
    function apply(theme) {
        document.documentElement.setAttribute('data-theme', theme);
        // Update Monaco editor theme if available
        if (window.QXLEditor && window.QXLEditor.setTheme) {
            window.QXLEditor.setTheme(theme === DARK ? 'qxl-dark' : 'qxl-light');
        }
    }

    /**
     * Update the theme toggle button icon.
     */
    function updateIcon(theme) {
        const btn = document.getElementById('btn-theme');
        if (btn) {
            const icon = btn.querySelector('i');
            if (icon) {
                icon.className = theme === DARK
                    ? 'bi bi-moon-stars-fill'
                    : 'bi bi-sun-fill';
            }
        }
    }

    /**
     * Get the current theme name.
     */
    function current() {
        return document.documentElement.getAttribute('data-theme') || DARK;
    }

    return { init, toggle, current };
})();

// Initialize theme on load
ThemeManager.init();
