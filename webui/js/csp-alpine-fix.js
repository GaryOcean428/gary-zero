// Alpine.js Components Registration
// Server-side CSP is now properly configured in run_ui.py

(() => {
    // Initialize Alpine.js components
    function initializeAlpineComponents() {
        if (typeof Alpine !== "undefined") {
            // Register global app state component for common data patterns
            Alpine.data("appState", () => ({
                connected: true,
                showQuickActions: true,
                contexts: [],
                tasks: [],
                selected: "",

                // Chat management methods
                resetChat() {
                    if (window.resetChat) {
                        window.resetChat();
                    } else {
                        console.log("Reset chat - function not available");
                    }
                },

                newChat() {
                    if (window.newChat) {
                        window.newChat();
                    } else {
                        console.log("New chat - function not available");
                    }
                },

                loadChats() {
                    if (window.loadChats) {
                        window.loadChats();
                    } else {
                        console.log("Load chats - function not available");
                    }
                },

                saveChat() {
                    if (window.saveChat) {
                        window.saveChat();
                    } else {
                        console.log("Save chat - function not available");
                    }
                },

                restart() {
                    if (window.restart) {
                        window.restart();
                    } else {
                        console.log("Restart - function not available");
                    }
                },
            }));

            // Create global Alpine magic helpers
            Alpine.magic("safeCall", () => (name, ...args) => {
                if (window[name] && typeof window[name] === "function") {
                    return window[name](...args);
                } else {
                    console.warn(`Function ${name} not available`);
                }
            });

            // Add null-safe text binding helper
            Alpine.magic("safeText", () => (value, fallback = "") => {
                try {
                    if (value === null || value === undefined) {
                        return fallback;
                    }
                    return String(value);
                } catch (error) {
                    console.warn("Alpine safeText error:", error);
                    return fallback;
                }
            });

            console.log("✅ Alpine.js components registered successfully");
        } else {
            console.warn("Alpine.js not available for component registration");
        }
    }

    // 3. Fix ToastManager DOM initialization issues
    function fixToastManager() {
        if (typeof ToastManager !== "undefined" && !window.ToastManagerFixed) {
            // Create enhanced ToastManager
            class RobustToastManager extends ToastManager {
                constructor() {
                    super();
                    this.initializeWhenReady();
                }

                initializeWhenReady() {
                    if (document.readyState === "loading") {
                        document.addEventListener("DOMContentLoaded", () => this.ensureContainer());
                    } else {
                        // DOM already loaded, wait for next tick
                        setTimeout(() => this.ensureContainer(), 0);
                    }
                }

                ensureContainer() {
                    if (this.container && this.container.parentElement) {
                        return; // Container already exists and is attached
                    }

                    // Wait for document.body to be available if needed
                    if (!document.body) {
                        setTimeout(() => this.ensureContainer(), 100);
                        return;
                    }

                    // Multiple fallback strategies for container creation
                    const targetSelectors = [
                        "body",
                        "#app",
                        "#root",
                        ".main-container",
                        "main",
                        "div", // Last resort
                    ];

                    let parent = null;
                    for (const selector of targetSelectors) {
                        parent = document.querySelector(selector);
                        if (parent) break;
                    }

                    if (!parent) {
                        console.warn("ToastManager: No suitable parent element found, using document.body as fallback");
                        parent = document.body;
                    }

                    if (!parent) {
                        console.error("ToastManager: document.body not available, cannot create container");
                        return;
                    }

                    // Remove existing container if found
                    const existingContainer = document.querySelector("#toast-container, #toast-container-fallback");
                    if (existingContainer) {
                        existingContainer.remove();
                    }

                    // Create new container
                    this.container = document.createElement("div");
                    this.container.id = "toast-container-enhanced";
                    this.container.className = "toast-container";
                    this.container.style.cssText = `
                        position: fixed;
                        top: 20px;
                        right: 20px;
                        z-index: 10000;
                        pointer-events: none;
                        max-width: 400px;
                    `;

                    try {
                        parent.appendChild(this.container);
                        console.log("✅ Enhanced ToastManager container created");
                    } catch (error) {
                        console.error("ToastManager: Failed to append container:", error);
                    }
                }

                show(message, type = "info", duration = 5000) {
                    this.ensureContainer();

                    if (!this.container) {
                        console.warn("ToastManager: Container not available, falling back to console");
                        console.log(`[${type.toUpperCase()}] ${message}`);
                        return;
                    }

                    return super.show(message, type, duration);
                }
            }

            // Replace the global ToastManager
            window.ToastManager = RobustToastManager;

            // Create a global instance
            if (!window.toastManager) {
                window.toastManager = new RobustToastManager();
            }

            window.ToastManagerFixed = true;
            console.log("✅ ToastManager enhanced successfully");
        }
    }

    // 4. Add Alpine.js error boundary
    function setupAlpineErrorBoundary() {
        // Enhanced error handling for Alpine.js
        if (typeof Alpine !== "undefined") {
            // Override Alpine's default error handling
            const originalStart = Alpine.start;
            Alpine.start = function () {
                try {
                    return originalStart.apply(this, arguments);
                } catch (error) {
                    console.error("Alpine.js initialization error:", error);
                    if (window.toastManager) {
                        window.toastManager.show(
                            "Interface initialization encountered an error. Some features may not work correctly.",
                            "warning",
                            6000
                        );
                    }
                    throw error;
                }
            };
        }

        // Global error handler for Alpine.js expressions
        window.addEventListener("error", (event) => {
            if (event.error && event.error.message) {
                const errorMessage = event.error.message;

                // Handle specific null.trim() error
                if (errorMessage.includes("null") && errorMessage.includes("trim")) {
                    console.error("Alpine.js null trim error detected:", event.error);
                    if (window.toastManager) {
                        window.toastManager.show(
                            "Interface initialization issue resolved. Some features may have been temporarily unavailable.",
                            "info",
                            4000
                        );
                    }
                    return; // Don't throw this to user
                }

                // Handle other Alpine.js errors
                if (errorMessage.includes("Alpine")) {
                    console.error("Alpine.js runtime error:", event.error);
                    if (window.toastManager) {
                        window.toastManager.show(
                            "Interface error detected. Please refresh if issues persist.",
                            "warning",
                            5000
                        );
                    }
                }
            }
        });

        console.log("✅ Alpine.js error boundary established");
    }

    // Execution sequence
    function applyFixes() {
        console.log("🔧 Applying Alpine.js component registration...");

        // Apply fixes in sequence
        setupAlpineErrorBoundary();
        fixToastManager();

        // Wait for Alpine to be available, then initialize components
        if (typeof Alpine !== "undefined") {
            initializeAlpineComponents();
        } else {
            // Wait for Alpine to load
            const checkAlpine = setInterval(() => {
                if (typeof Alpine !== "undefined") {
                    clearInterval(checkAlpine);
                    initializeAlpineComponents();
                }
            }, 100);

            // Timeout after 5 seconds
            setTimeout(() => {
                clearInterval(checkAlpine);
                if (typeof Alpine === "undefined") {
                    console.warn("Alpine.js not loaded within timeout period");
                }
            }, 5000);
        }

        console.log("✅ Alpine.js component registration complete");
    }

    // Execute fixes when DOM is ready
    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", applyFixes);
    } else {
        // DOM already loaded
        applyFixes();
    }
})();
