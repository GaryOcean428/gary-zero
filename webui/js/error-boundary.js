/**
 * Global Error Boundary - Catches and handles JavaScript errors gracefully
 * Part of Phase 3: Error Handling & Boundaries implementation
 */

class ErrorBoundary {
    constructor() {
        this.setupGlobalErrorHandlers();
        this.errorLog = [];
        this.maxLogSize = 100;
    }

    /**
     * Set up global error handlers for the application
     */
    setupGlobalErrorHandlers() {
        // Handle unhandled promise rejections
        window.addEventListener('unhandledrejection', (event) => {
            console.error('Unhandled promise rejection:', event.reason);
            this.logError('Promise Rejection', event.reason, {
                type: 'unhandledrejection',
                timestamp: new Date().toISOString()
            });
            
            // Prevent the default browser behavior
            event.preventDefault();
            
            // Show user-friendly error message
            this.showUserError('An unexpected error occurred. Please try again.');
        });

        // Handle general JavaScript errors
        window.addEventListener('error', (event) => {
            console.error('JavaScript error:', event.error);
            this.logError('JavaScript Error', event.error, {
                type: 'javascript',
                filename: event.filename,
                lineno: event.lineno,
                colno: event.colno,
                timestamp: new Date().toISOString()
            });
            
            // Show user-friendly error message for critical errors
            if (this.isCriticalError(event.error)) {
                this.showUserError('A critical error occurred. Please refresh the page.');
            }
        });

        // Handle fetch API errors
        this.setupFetchErrorHandling();
    }

    /**
     * Set up fetch API error handling with retry logic
     */
    setupFetchErrorHandling() {
        const originalFetch = window.fetch;
        
        window.fetch = async (...args) => {
            try {
                const response = await originalFetch(...args);
                
                if (!response.ok) {
                    const error = new Error(`HTTP ${response.status}: ${response.statusText}`);
                    this.logError('Fetch Error', error, {
                        type: 'fetch',
                        url: args[0],
                        status: response.status,
                        timestamp: new Date().toISOString()
                    });
                    
                    // Implement retry logic for transient failures
                    if (this.isRetryableError(response.status)) {
                        return this.retryFetch(originalFetch, ...args);
                    }
                }
                
                return response;
            } catch (error) {
                this.logError('Network Error', error, {
                    type: 'network',
                    url: args[0],
                    timestamp: new Date().toISOString()
                });
                
                // Show network error to user
                this.showUserError('Network error. Please check your connection and try again.');
                throw error;
            }
        };
    }

    /**
     * Retry fetch with exponential backoff
     */
    async retryFetch(fetchFn, ...args) {
        const maxRetries = 3;
        const baseDelay = 1000; // 1 second
        
        for (let attempt = 1; attempt <= maxRetries; attempt++) {
            try {
                await this.delay(baseDelay * Math.pow(2, attempt - 1));
                const response = await fetchFn(...args);
                
                if (response.ok) {
                    return response;
                }
                
                if (attempt === maxRetries) {
                    throw new Error(`Request failed after ${maxRetries} attempts`);
                }
            } catch (error) {
                if (attempt === maxRetries) {
                    throw error;
                }
            }
        }
    }

    /**
     * Log error with structured data
     */
    logError(type, error, metadata = {}) {
        const errorEntry = {
            type,
            message: error?.message || String(error),
            stack: error?.stack,
            metadata,
            timestamp: new Date().toISOString(),
            userAgent: navigator.userAgent,
            url: window.location.href
        };

        this.errorLog.push(errorEntry);
        
        // Keep log size manageable
        if (this.errorLog.length > this.maxLogSize) {
            this.errorLog.shift();
        }

        // Send to error reporting service (if configured)
        this.reportError(errorEntry);
    }

    /**
     * Show user-friendly error message
     */
    showUserError(message, isRecoverable = true) {
        // Try to use existing toast/notification system
        if (typeof window.showToast === 'function') {
            window.showToast(message, 'error');
        } else if (typeof window.Alpine?.store === 'function') {
            // Use Alpine.js store if available
            const store = window.Alpine.store('notifications') || {};
            if (store.add) {
                store.add({ type: 'error', message, timeout: 5000 });
            }
        } else {
            // Fallback to browser alert
            alert(message);
        }

        // Add error UI if page is severely broken
        if (!isRecoverable) {
            this.showErrorFallbackUI(message);
        }
    }

    /**
     * Show fallback error UI when main UI is broken
     */
    showErrorFallbackUI(message) {
        const errorDiv = document.createElement('div');
        errorDiv.id = 'error-boundary-fallback';
        errorDiv.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.9);
            color: white;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            z-index: 10000;
            font-family: Arial, sans-serif;
        `;
        
        errorDiv.innerHTML = `
            <div style="text-align: center; padding: 20px; max-width: 500px;">
                <h2>Something went wrong</h2>
                <p>${message}</p>
                <button onclick="location.reload()" style="
                    padding: 10px 20px;
                    margin: 10px;
                    background: #007cba;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    cursor: pointer;
                ">Reload Page</button>
                <button onclick="document.getElementById('error-boundary-fallback').remove()" style="
                    padding: 10px 20px;
                    margin: 10px;
                    background: #666;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    cursor: pointer;
                ">Close</button>
            </div>
        `;
        
        document.body.appendChild(errorDiv);
    }

    /**
     * Determine if error is critical and requires immediate user attention
     */
    isCriticalError(error) {
        const criticalPatterns = [
            /ChunkLoadError/,
            /Loading chunk \d+ failed/,
            /Script error/,
            /Network request failed/
        ];
        
        const message = error?.message || String(error);
        return criticalPatterns.some(pattern => pattern.test(message));
    }

    /**
     * Determine if HTTP status code indicates a retryable error
     */
    isRetryableError(status) {
        const retryableCodes = [408, 429, 500, 502, 503, 504];
        return retryableCodes.includes(status);
    }

    /**
     * Report error to external service (implement based on your needs)
     */
    reportError(errorEntry) {
        // Example: Send to error reporting service
        // if (window.Sentry) {
        //     window.Sentry.captureException(new Error(errorEntry.message), {
        //         extra: errorEntry.metadata,
        //         tags: { type: errorEntry.type }
        //     });
        // }
        
        // For now, just log to console in development
        if (process.env.NODE_ENV === 'development') {
            console.group('🚨 Error Boundary Report');
            console.error('Type:', errorEntry.type);
            console.error('Message:', errorEntry.message);
            console.error('Metadata:', errorEntry.metadata);
            console.error('Stack:', errorEntry.stack);
            console.groupEnd();
        }
    }

    /**
     * Get error statistics for monitoring
     */
    getErrorStats() {
        const stats = {
            total: this.errorLog.length,
            byType: {},
            recent: this.errorLog.slice(-10)
        };

        this.errorLog.forEach(error => {
            stats.byType[error.type] = (stats.byType[error.type] || 0) + 1;
        });

        return stats;
    }

    /**
     * Clear error log
     */
    clearErrorLog() {
        this.errorLog = [];
    }

    /**
     * Utility delay function
     */
    delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
}

// Initialize global error boundary
const globalErrorBoundary = new ErrorBoundary();

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ErrorBoundary;
} else {
    window.ErrorBoundary = ErrorBoundary;
    window.globalErrorBoundary = globalErrorBoundary;
}