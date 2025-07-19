import * as _components from "./components.js";
import * as _modals from "./modals.js";

// Import Alpine.js directly
import "./alpine.min.js";

// Pre-initialize root store as early as possible to prevent race conditions
if (typeof Alpine !== "undefined") {
    // Initialize store immediately when Alpine is available
    document.addEventListener("alpine:init", () => {
        try {
            Alpine.store("root", {
                activeTab: localStorage.getItem("settingsActiveTab") || "agent",
                isOpen: false,
                toggleSettings() {
                    try {
                        this.isOpen = !this.isOpen;
                    } catch (error) {
                        console.error("Error toggling settings:", error);
                    }
                },
            });
            console.log("✅ Alpine root store pre-initialized successfully");
        } catch (error) {
            console.error("❌ Error pre-initializing Alpine root store:", error);
        }
    });
}

// Add Alpine.js Collapse plugin support
if (typeof Alpine !== "undefined") {
    // Add null-safe magic helper for Alpine.js expressions
    Alpine.magic("safe", () => {
        return (value, defaultValue = "") => {
            try {
                return value != null ? String(value).trim() : defaultValue;
            } catch (error) {
                console.warn("Alpine safe magic error:", error);
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
                        console.warn("Error evaluating x-show for collapse:", error);
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

    console.log("✅ Alpine.js Collapse directive registered");
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
            console.warn("Alpine expression evaluation error:", error, "Expression:", expression);
            return defaultValue;
        }
    };

    // add x-destroy directive
    Alpine.directive("destroy", (el, { expression }, { evaluateLater, cleanup }) => {
        const onDestroy = evaluateLater(expression);
        cleanup(() => onDestroy());
    });
} else {
    console.error("Alpine.js not loaded properly");
}
