/**
 * Unified Error Handler - DRY Implementation
 * Consolidates error handling patterns across Gary-Zero web UI
 * Provides consistent error logging, user notification, and recovery strategies
 */

class UnifiedErrorHandler {
    constructor(options = {}) {
        this.logger = options.logger || (window.createLogger && window.createLogger('ErrorHandler')) || console;
        this.showUserNotifications = options.showUserNotifications !== false;
        this.enableRetry = options.enableRetry !== false;
        this.errorCounts = new Map();
        this.maxRetries = options.maxRetries || 3;
        this.retryDelay = options.retryDelay || 1000;
    }

    /**
     * Centralized error handling with consistent logging and user feedback
     * @param {Error} error - The error object
     * @param {Object} context - Context information about where the error occurred
     * @param {Object} options - Handling options
     */
    handle(error, context = {}, options = {}) {
        const errorKey = this.generateErrorKey(error, context);
        const errorCount = this.errorCounts.get(errorKey) || 0;
        this.errorCounts.set(errorKey, errorCount + 1);

        // Log the error with context
        this.logError(error, context, errorCount);

        // Show user notification if enabled
        if (this.showUserNotifications && options.notify !== false) {
            this.notifyUser(error, context, options);
        }

        // Handle recovery if specified
        if (options.recovery) {
            this.handleRecovery(error, context, options);
        }

        return {
            error,
            context,
            handled: true,
            count: errorCount + 1
        };
    }

    /**
     * Safe execution wrapper with automatic error handling
     * @param {Function} fn - Function to execute safely
     * @param {Object} context - Context information
     * @param {Object} options - Execution options
     */
    async safeExecute(fn, context = {}, options = {}) {
        const operation = context.operation || 'unknown operation';
        
        try {
            this.logger.debug && this.logger.debug(`Starting ${operation}`);
            const result = await fn();
            this.logger.debug && this.logger.debug(`Completed ${operation}`);
            return { success: true, result };
        } catch (error) {
            this.handle(error, { ...context, operation }, options);
            
            if (options.throwOnError !== false) {
                throw error;
            }
            
            return { 
                success: false, 
                error, 
                defaultValue: options.defaultValue 
            };
        }
    }

    /**
     * Retry wrapper with exponential backoff
     * @param {Function} fn - Function to retry
     * @param {Object} context - Context information
     * @param {Object} options - Retry options
     */
    async withRetry(fn, context = {}, options = {}) {
        const maxRetries = options.maxRetries || this.maxRetries;
        const baseDelay = options.retryDelay || this.retryDelay;
        const operation = context.operation || 'operation';

        for (let attempt = 1; attempt <= maxRetries; attempt++) {
            try {
                return await fn();
            } catch (error) {
                if (attempt === maxRetries) {
                    this.handle(error, { 
                        ...context, 
                        operation, 
                        finalAttempt: true,
                        totalAttempts: attempt 
                    }, options);
                    throw error;
                }

                const delay = baseDelay * Math.pow(2, attempt - 1);
                this.logger.warn && this.logger.warn(
                    `${operation} failed (attempt ${attempt}/${maxRetries}), retrying in ${delay}ms:`, 
                    error.message
                );

                await this.sleep(delay);
            }
        }
    }

    /**
     * DOM operation wrapper with safe error handling
     * @param {Function} domFn - DOM manipulation function
     * @param {Object} context - Context information
     * @param {Object} options - Options
     */
    async safeDOMOperation(domFn, context = {}, options = {}) {
        return this.safeExecute(domFn, {
            ...context,
            type: 'DOM operation',
            operation: context.operation || 'DOM manipulation'
        }, {
            ...options,
            notify: options.notify !== false,
            recovery: options.recovery || this.domErrorRecovery
        });
    }

    /**
     * API call wrapper with retry and error handling
     * @param {Function} apiFn - API call function
     * @param {Object} context - Context information
     * @param {Object} options - Options
     */
    async safeAPICall(apiFn, context = {}, options = {}) {
        return this.withRetry(apiFn, {
            ...context,
            type: 'API call',
            operation: context.operation || 'API request'
        }, {
            ...options,
            maxRetries: options.maxRetries || 2,
            notify: options.notify !== false
        });
    }

    /**
     * Generate a unique key for error tracking
     */
    generateErrorKey(error, context) {
        const errorType = error.constructor.name;
        const message = error.message.substring(0, 100);
        const operation = context.operation || 'unknown';
        return `${errorType}:${operation}:${message}`;
    }

    /**
     * Log error with appropriate level based on severity
     */
    logError(error, context, count) {
        const severity = this.determineSeverity(error, context, count);
        const logMethod = this.logger[severity] || this.logger.error;
        
        if (logMethod) {
            logMethod(`[${severity.toUpperCase()}] Error in ${context.operation || 'unknown operation'}:`, {
                error: error.message,
                stack: error.stack,
                context,
                count: count + 1
            });
        }
    }

    /**
     * Determine error severity based on type and frequency
     */
    determineSeverity(error, context, count) {
        // Frequent errors get upgraded to warn/error
        if (count > 5) return 'error';
        if (count > 2) return 'warn';

        // Network/API errors are typically warnings
        if (error.name === 'NetworkError' || error.name === 'TypeError' && error.message.includes('fetch')) {
            return 'warn';
        }

        // Syntax errors and references errors are errors
        if (error instanceof SyntaxError || error instanceof ReferenceError) {
            return 'error';
        }

        return 'warn';
    }

    /**
     * Show user-friendly error notification
     */
    notifyUser(error, context, options) {
        if (!this.shouldNotifyUser(error, context)) return;

        const userMessage = this.generateUserMessage(error, context);
        
        // Try to use toast notification if available
        if (window.toastManager) {
            window.toastManager.show(userMessage, 'error', 5000);
        } else if (options.fallbackAlert !== false) {
            // Fallback to alert (can be disabled)
            setTimeout(() => alert(userMessage), 100);
        }
    }

    /**
     * Determine if user should be notified
     */
    shouldNotifyUser(error, context) {
        // Don't spam user with repeated errors
        const errorKey = this.generateErrorKey(error, context);
        const count = this.errorCounts.get(errorKey) || 0;
        
        // Show first error, then every 10th occurrence
        return count === 0 || count % 10 === 0;
    }

    /**
     * Generate user-friendly error message
     */
    generateUserMessage(error, context) {
        const operation = context.operation || 'operation';
        
        // Common error patterns
        if (error.message.includes('fetch')) {
            return `Network error during ${operation}. Please check your connection and try again.`;
        }
        
        if (error.message.includes('not found') || error.name === 'ReferenceError') {
            return `A component needed for ${operation} was not found. Please refresh the page.`;
        }
        
        if (error.message.includes('permission') || error.message.includes('unauthorized')) {
            return `Permission denied for ${operation}. Please check your access rights.`;
        }
        
        return `An error occurred during ${operation}. Please try again or refresh the page.`;
    }

    /**
     * Handle error recovery strategies
     */
    handleRecovery(error, context, options) {
        if (typeof options.recovery === 'function') {
            try {
                options.recovery(error, context);
            } catch (recoveryError) {
                this.logger.error && this.logger.error('Error recovery failed:', recoveryError);
            }
        }
    }

    /**
     * Default DOM error recovery strategy
     */
    domErrorRecovery = (error, context) => {
        // Attempt to reinitialize Alpine.js components if DOM error
        if (window.Alpine && error.message.includes('Alpine')) {
            setTimeout(() => {
                try {
                    window.Alpine.start();
                } catch (e) {
                    // Ignore recovery errors
                }
            }, 1000);
        }
    }

    /**
     * Utility: sleep function for delays
     */
    sleep(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    /**
     * Get error statistics
     */
    getStats() {
        return {
            totalErrors: Array.from(this.errorCounts.values()).reduce((a, b) => a + b, 0),
            uniqueErrors: this.errorCounts.size,
            errorBreakdown: Object.fromEntries(this.errorCounts)
        };
    }

    /**
     * Clear error statistics
     */
    clearStats() {
        this.errorCounts.clear();
    }
}

// Create global error handler instance
const errorHandler = new UnifiedErrorHandler();

// Global error event listeners
window.addEventListener('error', (event) => {
    errorHandler.handle(event.error, {
        operation: 'Global error',
        filename: event.filename,
        line: event.lineno,
        column: event.colno
    });
});

window.addEventListener('unhandledrejection', (event) => {
    errorHandler.handle(event.reason, {
        operation: 'Unhandled promise rejection'
    });
});

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { UnifiedErrorHandler, errorHandler };
}

// Global window object for browser usage
if (typeof window !== 'undefined') {
    window.UnifiedErrorHandler = UnifiedErrorHandler;
    window.errorHandler = errorHandler;
    
    // Convenience functions
    window.safeExecute = (fn, context, options) => errorHandler.safeExecute(fn, context, options);
    window.safeAPICall = (fn, context, options) => errorHandler.safeAPICall(fn, context, options);
    window.safeDOMOperation = (fn, context, options) => errorHandler.safeDOMOperation(fn, context, options);
}

/**
 * Usage Examples:
 * 
 * // Handle errors centrally
 * try {
 *     // risky operation
 * } catch (error) {
 *     errorHandler.handle(error, { operation: 'user action' });
 * }
 * 
 * // Safe execution with automatic error handling
 * const result = await errorHandler.safeExecute(async () => {
 *     return await fetch('/api/data');
 * }, { operation: 'fetch user data' });
 * 
 * // API calls with retry
 * const data = await errorHandler.safeAPICall(async () => {
 *     return await fetch('/api/endpoint').then(r => r.json());
 * }, { operation: 'load settings' });
 * 
 * // DOM operations
 * await errorHandler.safeDOMOperation(() => {
 *     document.getElementById('myElement').style.display = 'block';
 * }, { operation: 'show element' });
 */