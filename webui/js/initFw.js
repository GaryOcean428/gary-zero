// Import enhanced logger
import { logger } from './console-logger.js';

import * as _components from "./components.js";
import * as _modals from "./modals.js";

// Import Alpine.js directly
import "./alpine.min.js";

// Import Alpine Component Manager for centralized registration
import "./alpine-registration.js";

// Pre-initialize root store as early as possible to prevent race conditions
// Use the new Alpine Component Manager for proper timing control
function initializeRootStore() {
    if (!window.alpineManager) {
        logger.error("❌ Alpine Component Manager not available");
        return;
    }

    // Wait for Alpine Component Manager to be ready
    window.alpineManager.init().then(() => {
        try {
            if (window.Alpine && typeof window.Alpine.store === 'function') {
                Alpine.store("root", {
                    activeTab: localStorage.getItem("settingsActiveTab") || "agent",
                    isOpen: false,
                    toggleSettings() {
                        try {
                            this.isOpen = !this.isOpen;
                        } catch (error) {
                            logger.error("Error toggling settings:", error);
                        }
                    },
                });
                logger.log("✅ Alpine root store initialized via Component Manager");
            } else {
                logger.error("❌ Alpine.store not available");
            }
        } catch (error) {
            logger.error("❌ Error initializing Alpine root store:", error);
        }
    }).catch(error => {
        logger.error("❌ Failed to initialize Alpine Component Manager:", error);
    });
}

// Initialize root store with proper timing
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeRootStore);
} else {
    initializeRootStore();
}

// Add Alpine.js Collapse plugin support
if (typeof Alpine !== "undefined") {
    // Add null-safe magic helper for Alpine.js expressions
    Alpine.magic("safe", () => {
        return (value, defaultValue = "") => {
            try {
                return value != null ? String(value).trim() : defaultValue;
            } catch (error) {
                logger.warn("Alpine safe magic error:", error);
                return defaultValue;
            }
        };
    });

    // Register x-collapse directive manually since the plugin isn't loaded
    Alpine.directive("collapse", (el, { value, modifiers }, { effect, evaluate }) => {
        let initialUpdate = true;

        const closedStyles = {
            height: "0px",
            overflow: "hidden",
            paddingTop: "0px",
            paddingBottom: "0px",
            marginTop: "0px",
            marginBottom: "0px",
        };

        let openStyles = {};

        effect(() => {
            let isOpen;

            // Handle case where no value is provided (just x-collapse)
            if (!value) {
                // Default behavior: collapse based on x-show if present
                const showDirective = el.getAttribute("x-show");
                if (showDirective) {
                    try {
                        isOpen = evaluate(showDirective);
                    } catch (error) {
                        logger.warn("Error evaluating x-show for collapse:", error);
                        isOpen = true; // Default to open on error
                    }
                } else {
                    isOpen = true; // Default to open if no value specified
                }
            } else {
                isOpen = evaluate(value);
            }

            // Null-safe handling: ensure isOpen is a boolean
            if (isOpen === null || isOpen === undefined) {
                isOpen = false;
            }

            if (initialUpdate) {
                if (isOpen) {
                    // Store initial open styles
                    openStyles = {
                        height: el.style.height || "",
                        overflow: el.style.overflow || "",
                        paddingTop: el.style.paddingTop || "",
                        paddingBottom: el.style.paddingBottom || "",
                        marginTop: el.style.marginTop || "",
                        marginBottom: el.style.marginBottom || "",
                    };
                } else {
                    // Apply closed styles immediately on initial load if closed
                    Object.assign(el.style, closedStyles);
                }
                initialUpdate = false;
                return;
            }

            if (isOpen) {
                // Opening animation
                Object.assign(el.style, openStyles);
                el.style.transition = "all 0.3s ease-in-out";
            } else {
                // Closing animation
                el.style.transition = "all 0.3s ease-in-out";
                Object.assign(el.style, closedStyles);
            }
        });
    });

    logger.log("✅ Alpine.js Collapse directive registered");
}

// Wait for Alpine to be available
if (typeof Alpine !== "undefined") {
    // Add global null-safe wrapper function for Alpine expressions
    window.safeAlpineEval = (expression, context = {}, defaultValue = "") => {
        try {
            if (expression === null || expression === undefined) {
                return defaultValue;
            }
            const result = Alpine.evaluate(context, expression);
            return result != null ? result : defaultValue;
        } catch (error) {
            logger.warn("Alpine expression evaluation error:", error, "Expression:", expression);
            return defaultValue;
        }
    };

    // add x-destroy directive
    Alpine.directive("destroy", (el, { expression }, { evaluateLater, cleanup }) => {
        const onDestroy = evaluateLater(expression);
        cleanup(() => onDestroy());
    });
} else {
    logger.error("Alpine.js not loaded properly");
}
