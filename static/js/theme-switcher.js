/**
 * Theme Switcher with localStorage Persistence
 * Allows users to select and persist theme preferences across visits
 */

(function() {
    'use strict';

    const THEME_STORAGE_KEY = 'mountain-weather-theme';
    const DEFAULT_THEME = 'modern-light';
    const themeSelect = document.getElementById('theme-select');

    /**
     * Get the current theme from localStorage or return default
     */
    function getCurrentTheme() {
        try {
            const savedTheme = localStorage.getItem(THEME_STORAGE_KEY);
            return savedTheme || DEFAULT_THEME;
        } catch (e) {
            console.warn('localStorage not available, using default theme');
            return DEFAULT_THEME;
        }
    }

    /**
     * Apply theme to the document
     */
    function applyTheme(theme) {
        const html = document.documentElement;
        html.setAttribute('data-theme', theme);
    }

    /**
     * Save theme preference to localStorage
     */
    function saveTheme(theme) {
        try {
            localStorage.setItem(THEME_STORAGE_KEY, theme);
        } catch (e) {
            console.warn('Could not save theme to localStorage');
        }
    }

    /**
     * Handle theme change event
     */
    function handleThemeChange(event) {
        const selectedTheme = event.target.value;
        applyTheme(selectedTheme);
        saveTheme(selectedTheme);
    }

    /**
     * Initialize theme on page load
     */
    function initTheme() {
        // Load saved theme or use default
        const currentTheme = getCurrentTheme();

        // Apply theme immediately to prevent flash of wrong theme
        applyTheme(currentTheme);

        // Set dropdown to match current theme
        if (themeSelect) {
            themeSelect.value = currentTheme;

            // Add change event listener
            themeSelect.addEventListener('change', handleThemeChange);
        }
    }

    // Initialize theme as early as possible
    // This runs immediately when script loads to minimize theme flash
    initTheme();

    // Also initialize on DOMContentLoaded as a fallback
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initTheme);
    }
})();
