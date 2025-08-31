/**
 * Enhanced Error Reporting Module
 * Provides centralized error tracking and reporting capabilities
 */

class ErrorReporter {
    constructor() {
        this.errorCount = 0;
        this.sessionId = this.generateSessionId();
        this.errorBuffer = [];
        this.maxBufferSize = 50;
    }

    generateSessionId() {
        return 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    }

    /**
     * Report an error with enhanced context
     */
    reportError(error, context = {}) {
        this.errorCount++;
        
        const errorReport = {
            id: this.errorCount,
            sessionId: this.sessionId,
            timestamp: new Date().toISOString(),
            url: window.location.href,
            userAgent: navigator.userAgent,
            error: {
                message: error?.message || String(error),
                stack: error?.stack,
                name: error?.name
            },
            context: {
                ...context,
                connectionStatus: window.connectionStatus || false,
                currentContext: window.getContext ? window.getContext() : null
            }
        };

        // Add to buffer
        this.errorBuffer.push(errorReport);
        if (this.errorBuffer.length > this.maxBufferSize) {
            this.errorBuffer.shift();
        }

        // Log to console in development
        if (this.isDevelopment()) {
            // Use safe console grouping
            if (typeof console.group === 'function') {
                console.group('🚨 Error Report #' + this.errorCount);
                console.error('Error:', error);
                console.log('Context:', context);
                console.log('Full Report:', errorReport);
                console.groupEnd();
            } else {
                // Fallback for environments without console.group
                console.error('🚨 Error Report #' + this.errorCount);
                console.error('Error:', error);
                console.log('Context:', context);
                console.log('Full Report:', errorReport);
            }
        }

        // Try to send to server (non-blocking)
        this.sendToServer(errorReport).catch(err => {
            console.warn('Failed to send error report to server:', err);
        });

        return errorReport;
    }

    /**
     * Send error report to server
     */
    async sendToServer(errorReport) {
        try {
            const response = await fetch('/api/error_report', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(errorReport)
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            // Handle 204 No Content responses gracefully
            if (response.status === 204) {
                return { success: true, message: 'Error report received' };
            }

            // Handle empty responses gracefully
            const contentType = response.headers.get('content-type');
            if (contentType && contentType.includes('application/json')) {
                return await response.json();
            } else {
                return { success: true, message: 'Error report processed' };
            }
        } catch (error) {
            // Store in localStorage as fallback
            this.storeLocally(errorReport);
            throw error;
        }
    }

    /**
     * Store error report locally for later retry
     */
    storeLocally(errorReport) {
        try {
            const stored = JSON.parse(localStorage.getItem('pendingErrorReports') || '[]');
            stored.push(errorReport);
            
            // Limit stored reports
            if (stored.length > 20) {
                stored.splice(0, stored.length - 20);
            }
            
            localStorage.setItem('pendingErrorReports', JSON.stringify(stored));
        } catch (e) {
            console.warn('Failed to store error report locally:', e);
        }
    }

    /**
     * Get error statistics
     */
    getStats() {
        return {
            totalErrors: this.errorCount,
            sessionId: this.sessionId,
            recentErrors: this.errorBuffer.slice(-10),
            bufferSize: this.errorBuffer.length
        };
    }

    /**
     * Check if running in development mode
     */
    isDevelopment() {
        return window.location.hostname === 'localhost' || 
               window.location.hostname === '127.0.0.1' ||
               window.location.hostname.includes('dev');
    }
}

// Create global instance
const globalErrorReporter = new ErrorReporter();

// Make available globally
window.errorReporter = globalErrorReporter;

// Export for module use
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ErrorReporter;
}