// Import enhanced logger
import { logger } from './console-logger.js';

/**
 * Enhanced form validation and user feedback for Gary-Zero
 */

// Toast notification system
class ToastManager {
    constructor() {
        this.container = null;
        this.queue = [];
        this.initialized = false;
    }

    createContainer() {
        if (this.container && this.container.parentElement) return;

        // Wait for document.body to be available if needed
        if (!document.body) {
            logger.warn("ToastManager: document.body not available, deferring container creation");
            return false;
        }

        // Multiple fallback strategies for container parent
        const targetSelectors = ["body", "#app", "#root", ".main-container", "main"];

        let parent = null;
        for (const selector of targetSelectors) {
            parent = document.querySelector(selector);
            if (parent) break;
        }

        if (!parent) {
            logger.warn("ToastManager: No suitable parent element found, using document.body");
            parent = document.body;
        }

        this.container = document.createElement("div");
        this.container.id = "toast-container";
        this.container.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 10000;
            pointer-events: none;
        `;

        try {
            parent.appendChild(this.container);
            this.initialized = true;
            logger.log("✅ ToastManager container created successfully");
            return true;
        } catch (error) {
            logger.error("ToastManager: Failed to append container to parent:", error);
            // Fallback to document.body if the selected parent fails
            if (parent !== document.body && document.body) {
                try {
                    document.body.appendChild(this.container);
                    this.initialized = true;
                    logger.log("✅ ToastManager container created with fallback to body");
                    return true;
                } catch (fallbackError) {
                    logger.error("ToastManager: Fallback to body also failed:", fallbackError);
                    return false;
                }
            }
            return false;
        }
    }

    show(message, type = "info", duration = 5000) {
        // Queue the toast if container isn't ready yet
        if (!this.initialized) {
            this.queue.push({ message, type, duration });

            // Try to create container and process queue
            if (this.createContainer()) {
                this.processQueue();
            } else {
                // Set up retry mechanism if document.body still not available
                if (!this.retryTimer) {
                    this.retryTimer = setTimeout(() => {
                        this.retryTimer = null;
                        if (this.createContainer()) {
                            this.processQueue();
                        }
                    }, 100);
                }
                logger.warn("ToastManager: Container not available, queued toast message");
                return null;
            }
        }

        // Ensure container exists before showing toast
        if (!this.container || !this.container.parentElement) {
            logger.warn("ToastManager: Container not available, logging to console instead");
            logger.log(`[${type.toUpperCase()}] ${message}`);
            return null;
        }

        return this.displayToast(message, type, duration);
    }

    displayToast(message, type, duration) {
        const toast = document.createElement("div");
        toast.className = `toast toast-${type}`;
        toast.style.cssText = `
            background: var(--bg-secondary, #2a2a2a);
            color: var(--color-primary, #ffffff);
            padding: 12px 20px;
            margin-bottom: 10px;
            border-radius: 6px;
            border-left: 4px solid ${this.getTypeColor(type)};
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
            pointer-events: auto;
            max-width: 400px;
            word-wrap: break-word;
            animation: slideInRight 0.3s ease-out;
            position: relative;
        `;

        toast.innerHTML = `
            <div style="display: flex; align-items: center; gap: 10px;">
                <span style="font-size: 16px;">${this.getTypeIcon(type)}</span>
                <span>${message}</span>
                <button onclick="this.parentElement.parentElement.remove()" 
                        style="margin-left: auto; background: none; border: none; color: inherit; cursor: pointer; font-size: 18px; line-height: 1;">×</button>
            </div>
        `;

        this.container.appendChild(toast);

        // Auto-remove after duration
        if (duration > 0) {
            setTimeout(() => {
                if (toast.parentElement) {
                    toast.style.animation = "slideOutRight 0.3s ease-in forwards";
                    setTimeout(() => toast.remove(), 300);
                }
            }, duration);
        }

        return toast;
    }

    processQueue() {
        while (this.queue.length > 0) {
            const { message, type, duration } = this.queue.shift();
            this.displayToast(message, type, duration);
        }
    }

    getTypeColor(type) {
        const colors = {
            success: "#10b981",
            error: "#ef4444",
            warning: "#f59e0b",
            info: "#3b82f6",
        };
        return colors[type] || colors.info;
    }

    getTypeIcon(type) {
        const icons = {
            success: "✓",
            error: "✗",
            warning: "⚠",
            info: "ℹ",
        };
        return icons[type] || icons.info;
    }
}

// Enhanced input validation
class InputValidator {
    constructor() {
        this.rules = new Map();
        this.initializeDefaultRules();
    }

    initializeDefaultRules() {
        this.addRule(
            "required",
            (value) => {
                return value && value.toString().trim().length > 0;
            },
            "This field is required"
        );

        this.addRule(
            "email",
            (value) => {
                const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
                return !value || emailRegex.test(value);
            },
            "Please enter a valid email address"
        );

        this.addRule(
            "minLength",
            (value, param) => {
                return !value || value.toString().length >= param;
            },
            (param) => `Must be at least ${param} characters long`
        );

        this.addRule(
            "maxLength",
            (value, param) => {
                return !value || value.toString().length <= param;
            },
            (param) => `Must not exceed ${param} characters`
        );

        this.addRule(
            "url",
            (value) => {
                try {
                    return !value || new URL(value);
                } catch {
                    return false;
                }
            },
            "Please enter a valid URL"
        );
    }

    addRule(name, validator, message) {
        this.rules.set(name, { validator, message });
    }

    validate(element, rules = []) {
        const value = element.value;
        const errors = [];

        for (const rule of rules) {
            let ruleName, param;
            if (typeof rule === "string") {
                ruleName = rule;
            } else {
                ruleName = rule.name;
                param = rule.param;
            }

            const ruleObj = this.rules.get(ruleName);
            if (!ruleObj) continue;

            const isValid = ruleObj.validator(value, param);
            if (!isValid) {
                const message = typeof ruleObj.message === "function" ? ruleObj.message(param) : ruleObj.message;
                errors.push(message);
            }
        }

        return errors;
    }

    addValidationToElement(element, rules, options = {}) {
        const { showOnBlur = true, showOnInput = false, container = element.parentElement } = options;

        // Create error display element
        let errorElement = container.querySelector(".validation-error");
        if (!errorElement) {
            errorElement = document.createElement("div");
            errorElement.className = "validation-error";
            errorElement.style.cssText = `
                color: #ef4444;
                font-size: 0.875rem;
                margin-top: 4px;
                display: none;
            `;
            container.appendChild(errorElement);
        }

        const validateAndShow = () => {
            const errors = this.validate(element, rules);
            if (errors.length > 0) {
                errorElement.textContent = errors[0];
                errorElement.style.display = "block";
                element.style.borderColor = "#ef4444";
                element.setAttribute("aria-invalid", "true");
                element.setAttribute("aria-describedby", errorElement.id || "validation-error");
                return false;
            } else {
                errorElement.style.display = "none";
                element.style.borderColor = "";
                element.setAttribute("aria-invalid", "false");
                element.removeAttribute("aria-describedby");
                return true;
            }
        };

        if (showOnBlur) {
            element.addEventListener("blur", validateAndShow);
        }

        if (showOnInput) {
            element.addEventListener("input", validateAndShow);
        }

        // Return validation function for manual triggering
        return validateAndShow;
    }
}

// Loading state manager
class LoadingManager {
    constructor() {
        this.activeLoaders = new Set();
    }

    show(element, text = "Loading...") {
        if (!element) return;

        const loaderId = Math.random().toString(36).substr(2, 9);

        // Store original content
        const originalContent = element.innerHTML;
        const originalDisabled = element.disabled;

        // Create loading state
        element.innerHTML = `
            <span style="display: flex; align-items: center; gap: 8px;">
                <span class="loading-spinner" style="
                    width: 16px;
                    height: 16px;
                    border: 2px solid transparent;
                    border-top: 2px solid currentColor;
                    border-radius: 50%;
                    animation: spin 1s linear infinite;
                "></span>
                ${text}
            </span>
        `;
        element.disabled = true;

        this.activeLoaders.add({
            id: loaderId,
            element,
            originalContent,
            originalDisabled,
        });

        return loaderId;
    }

    hide(elementOrId) {
        let loaderToRemove = null;

        for (const loader of this.activeLoaders) {
            if (loader.id === elementOrId || loader.element === elementOrId) {
                loaderToRemove = loader;
                break;
            }
        }

        if (loaderToRemove) {
            loaderToRemove.element.innerHTML = loaderToRemove.originalContent;
            loaderToRemove.element.disabled = loaderToRemove.originalDisabled;
            this.activeLoaders.delete(loaderToRemove);
        }
    }

    hideAll() {
        for (const loader of this.activeLoaders) {
            loader.element.innerHTML = loader.originalContent;
            loader.element.disabled = loader.originalDisabled;
        }
        this.activeLoaders.clear();
    }
}

// Enhanced error boundary for Alpine.js components
class AlpineErrorBoundary {
    constructor() {
        this.setupGlobalErrorHandling();
        this.setupAlpineErrorHandling();
    }

    setupGlobalErrorHandling() {
        window.addEventListener("error", (event) => {
            logger.error("Global error:", event.error);
            this.handleError(event.error, "Global Error");
        });

        window.addEventListener("unhandledrejection", (event) => {
            logger.error("Unhandled promise rejection:", event.reason);
            this.handleError(event.reason, "Promise Rejection");
        });
    }

    setupAlpineErrorHandling() {
        // Alpine.js error handling setup
        document.addEventListener("alpine:init", () => {
            if (window.Alpine) {
                // Override Alpine's error handling
                const originalError = console.error;
                console.error = (...args) => {
                    if (args[0] && args[0].toString().includes("Alpine")) {
                        this.handleAlpineError(args);
                    }
                    originalError.apply(console, args);
                };
            }
        });
    }

    handleError(error, context = "Unknown") {
        const toast = getToastManager();
        toast.show(`An error occurred in ${context}. Please refresh the page if issues persist.`, "error", 8000);
    }

    handleAlpineError(args) {
        const toast = getToastManager();
        toast.show("Interface error detected. Some features may not work correctly.", "warning", 6000);
    }
}

// Initialize global instances with lazy initialization for ToastManager
function getToastManager() {
    if (!window._toastManagerInstance) {
        window._toastManagerInstance = new ToastManager();
    }
    return window._toastManagerInstance;
}

// Make toast manager available globally but only create when needed
Object.defineProperty(window, "toastManager", {
    get: getToastManager,
    configurable: true,
});

// Also create a global toast API for convenience
window.toast = {
    show: (message, type, duration) => getToastManager().show(message, type, duration),
    success: (message, duration) => getToastManager().show(message, "success", duration),
    error: (message, duration) => getToastManager().show(message, "error", duration),
    warning: (message, duration) => getToastManager().show(message, "warning", duration),
    info: (message, duration) => getToastManager().show(message, "info", duration),
};

window.inputValidator = new InputValidator();
window.loadingManager = new LoadingManager();
window.errorBoundary = new AlpineErrorBoundary();

// Add CSS animations
const style = document.createElement("style");
style.textContent = `
    @keyframes slideInRight {
        from {
            transform: translateX(100%);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }

    @keyframes slideOutRight {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(100%);
            opacity: 0;
        }
    }

    @keyframes spin {
        from { transform: rotate(0deg); }
        to { transform: rotate(360deg); }
    }

    .validation-error {
        animation: fadeIn 0.2s ease-out;
    }

    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(-5px); }
        to { opacity: 1; transform: translateY(0); }
    }

    /* Enhanced focus states for accessibility */
    input:focus,
    textarea:focus,
    select:focus,
    button:focus {
        outline: 2px solid var(--color-primary, #3b82f6);
        outline-offset: 2px;
    }

    /* Better form styling */
    input[aria-invalid="true"],
    textarea[aria-invalid="true"] {
        border-color: #ef4444 !important;
        box-shadow: 0 0 0 1px #ef4444;
    }

    input[aria-invalid="false"],
    textarea[aria-invalid="false"] {
        border-color: #10b981;
    }

    /* Fallback component styling */
    .fallback-component {
        padding: 20px;
        border: 2px dashed var(--color-border, #ccc);
        border-radius: 8px;
        text-align: center;
        background: var(--bg-secondary, #f9f9f9);
        color: var(--color-text, #333);
        margin: 10px 0;
    }

    .fallback-component h3 {
        margin: 0 0 10px 0;
        color: var(--color-primary, #3b82f6);
    }

    .fallback-component .error-message {
        color: #ef4444;
        font-size: 0.9em;
        margin: 10px 0;
        padding: 8px;
        background: rgba(239, 68, 68, 0.1);
        border-radius: 4px;
    }

    .fallback-component .btn {
        padding: 8px 16px;
        border-radius: 4px;
        border: none;
        cursor: pointer;
        font-size: 0.9em;
    }

    .fallback-component .btn-primary {
        background: var(--color-primary, #3b82f6);
        color: white;
    }

    .fallback-component .btn-primary:hover {
        background: var(--color-primary-dark, #2563eb);
    }
`;
document.head.appendChild(style);

// Export for module usage
if (typeof module !== "undefined" && module.exports) {
    module.exports = {
        ToastManager,
        InputValidator,
        LoadingManager,
        AlpineErrorBoundary,
    };
}
