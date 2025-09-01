/**
 * Global Error Boundary - Catches and handles JavaScript errors gracefully
 * Part of Phase 3: Error Handling & Boundaries implementation
 */

class ErrorBoundary {
    constructor(options = {}) {
        this.setupGlobalErrorHandlers();
        this.errorLog = [];
        this.maxLogSize = 100;
        this.isTestEnvironment = options.isTestEnvironment || false;
        
        // Only set up fetch handling if not disabled (for testing)
        if (!options.disableFetchHandling) {
            this.setupFetchErrorHandling();
        }
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
    }

    /**
     * Set up fetch API error handling with retry logic
     */
    setupFetchErrorHandling() {
        // Check if fetch exists and hasn't already been wrapped
        if (!window.fetch || window.fetch._errorBoundaryWrapped) {
            return;
        }
        
        const originalFetch = window.fetch;
        
        const wrappedFetch = async (...args) => {
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
                    
                    // For non-retryable errors, throw the error
                    throw error;
                }
                
                // Handle 204 No Content responses gracefully
                if (response.status === 204) {
                    // Create a synthetic response with empty content
                    return new Response(null, {
                        status: 204,
                        statusText: 'No Content',
                        headers: response.headers
                    });
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
        
        // Mark the wrapped fetch to avoid double-wrapping
        wrappedFetch._errorBoundaryWrapped = true;
        window.fetch = wrappedFetch;
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
                    const error = new Error(`Request failed after ${maxRetries} attempts: HTTP ${response.status}`);
                    this.logError('Fetch Retry Failed', error, {
                        type: 'fetch',
                        url: args[0],
                        status: response.status,
                        attempts: maxRetries,
                        timestamp: new Date().toISOString()
                    });
                    throw error;
                }
            } catch (error) {
                if (attempt === maxRetries) {
                    this.logError('Fetch Retry Failed', error, {
                        type: 'fetch',
                        url: args[0],
                        attempts: maxRetries,
                        timestamp: new Date().toISOString()
                    });
                    throw error;
                }
                // Continue to next retry attempt
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
        let messageShown = false;
        
        // Try to use existing toast/notification system
        if (typeof window.toast === 'function') {
            window.toast(message, 'error');
            messageShown = true;
        } else if (typeof window.showToast === 'function') {
            window.showToast(message, 'error');
            messageShown = true;
        } else if (typeof window.Alpine?.store === 'function') {
            // Use Alpine.js store if available
            try {
                const store = window.Alpine.store('notifications') || {};
                if (store.add) {
                    store.add({ type: 'error', message, timeout: 5000 });
                    messageShown = true;
                }
            } catch (e) {
                // Alpine store failed, continue to fallback
            }
        }
        
        // Fallback to browser alert if no other method worked
        if (!messageShown) {
            window.alert(message);
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
        // Use global error reporter if available
        if (window.errorReporter) {
            window.errorReporter.reportError(
                new Error(errorEntry.message), 
                {
                    type: errorEntry.type,
                    metadata: errorEntry.metadata,
                    stack: errorEntry.stack,
                    source: 'error-boundary'
                }
            );
        }
        
        // Example: Send to error reporting service
        // if (window.Sentry) {
        //     window.Sentry.captureException(new Error(errorEntry.message), {
        //         extra: errorEntry.metadata,
        //         tags: { type: errorEntry.type }
        //     });
        // }
        
        // For now, just log to console in development
        if (this.isDevelopmentMode()) {
            // Use safe console grouping
            if (typeof console.group === 'function') {
                console.group('🚨 Error Boundary Report');
                console.error('Type:', errorEntry.type);
                console.error('Message:', errorEntry.message);
                console.error('Metadata:', errorEntry.metadata);
                console.error('Stack:', errorEntry.stack);
                console.groupEnd();
            } else {
                // Fallback for environments without console.group
                console.error('🚨 Error Boundary Report');
                console.error('Type:', errorEntry.type);
                console.error('Message:', errorEntry.message);
                console.error('Metadata:', errorEntry.metadata);
                console.error('Stack:', errorEntry.stack);
            }
        }
    }

    /**
     * Check if running in development mode (browser-safe)
     */
    isDevelopmentMode() {
        // Multiple ways to detect development mode without Node.js globals
        return window.location.hostname === 'localhost' || 
               window.location.hostname === '127.0.0.1' ||
               window.location.hostname.includes('dev') ||
               window.location.port === '5173' || // Vite dev server default
               window.location.port === '3000' || // Common dev port
               window.location.port === '8080' || // Another common dev port
               !window.location.protocol.startsWith('https'); // Assume dev if not HTTPS
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

// Initialize global error boundary only if not in test environment
let globalErrorBoundary;
if (typeof window !== 'undefined' && !window.location.href.includes('test')) {
    try {
        globalErrorBoundary = new ErrorBoundary();
    } catch (error) {
        console.warn('Failed to initialize global error boundary:', error);
    }
}

// Provide early fallback for functions that Alpine.js might call before modules load
if (typeof window !== 'undefined') {
    // Improved fetchCurrentModel race condition handling
    let fetchModelQueue = [];
    let realFetchModel = null;
    
    window.fetchCurrentModel = function() {
        if (realFetchModel) {
            return realFetchModel();
        }
        
        // Queue the call with promise support
        return new Promise((resolve, reject) => {
            fetchModelQueue.push({ resolve, reject });
            console.log('🔄 fetchCurrentModel queued, waiting for initialization...');
        });
    };
    
    // Register real implementation when available
    window.registerFetchCurrentModel = function(fn) {
        realFetchModel = fn;
        console.log('✅ Real fetchCurrentModel registered, processing queue...');
        // Process queued calls
        while (fetchModelQueue.length > 0) {
            const { resolve, reject } = fetchModelQueue.shift();
            try {
                const result = fn();
                resolve(result);
            } catch (error) {
                reject(error);
            }
        }
    };
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ErrorBoundary;
} else {
    window.ErrorBoundary = ErrorBoundary;
    if (globalErrorBoundary) {
        window.globalErrorBoundary = globalErrorBoundary;
    }
}