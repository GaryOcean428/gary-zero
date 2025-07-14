(() => {
    const originalInit = window.initializeApp;
    window.initializeApp = function (...args) {
        // Skip UI structure builder - use existing HTML structure
        if (originalInit) {
            return originalInit.apply(this, args);
        }
    };

    // Don't automatically build the interface - use existing HTML
    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", () => {
            // Just verify elements exist, don't rebuild
            const rightPanel = document.getElementById("right-panel");
            if (rightPanel) {
                // Elements exist, no need to rebuild
                return;
            }
        });
    }
})();
