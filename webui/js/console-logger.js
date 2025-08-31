/**
 * Enhanced Console Logger Utility
 * Replaces direct console statements with configurable logging
 */

class Logger {
    constructor(options = {}) {
        this.isDevelopment = options.isDevelopment || this.detectDevelopment();
        this.logLevel = options.logLevel || 'info';
        this.prefix = options.prefix || '';
        this.enableGroups = this.hasConsoleGroup();
    }

    detectDevelopment() {
        return (
            typeof window !== 'undefined' && 
            (window.location.hostname === 'localhost' || 
             window.location.hostname === '127.0.0.1' ||
             window.location.hostname.startsWith('192.168.') ||
             process?.env?.NODE_ENV === 'development')
        );
    }

    hasConsoleGroup() {
        return typeof console !== 'undefined' && typeof console.group === 'function';
    }

    shouldLog(level) {
        const levels = { error: 0, warn: 1, info: 2, debug: 3 };
        return levels[level] <= levels[this.logLevel];
    }

    formatMessage(message, context = {}) {
        const timestamp = new Date().toISOString();
        const prefixStr = this.prefix ? `[${this.prefix}] ` : '';
        return {
            message: `${prefixStr}${message}`,
            timestamp,
            context
        };
    }

    log(message, context = {}) {
        if (!this.isDevelopment || !this.shouldLog('info')) return;
        
        const formatted = this.formatMessage(message, context);
        console.log(formatted.message, context);
    }

    warn(message, context = {}) {
        if (!this.shouldLog('warn')) return;
        
        const formatted = this.formatMessage(message, context);
        console.warn(formatted.message, context);
    }

    error(message, context = {}) {
        if (!this.shouldLog('error')) return;
        
        const formatted = this.formatMessage(message, context);
        console.error(formatted.message, context);
    }

    debug(message, context = {}) {
        if (!this.isDevelopment || !this.shouldLog('debug')) return;
        
        const formatted = this.formatMessage(message, context);
        console.log('[DEBUG]', formatted.message, context);
    }

    group(label, callback) {
        if (!this.isDevelopment) return;

        if (this.enableGroups) {
            console.group(label);
            if (callback) {
                try {
                    callback();
                } finally {
                    console.groupEnd();
                }
            }
        } else {
            // Fallback for environments without console.group
            this.log(`--- ${label} ---`);
            if (callback) {
                callback();
            }
            this.log(`--- End ${label} ---`);
        }
    }

    groupEnd() {
        if (this.enableGroups && this.isDevelopment) {
            console.groupEnd();
        }
    }

    // Utility methods for common patterns
    apiCall(method, url, data = null) {
        this.debug(`API Call: ${method} ${url}`, { data });
    }

    componentLoad(componentName, status = 'loading') {
        this.debug(`Component ${componentName}: ${status}`);
    }

    userAction(action, details = {}) {
        this.debug(`User Action: ${action}`, details);
    }
}

// Create singleton instance
const logger = new Logger({
    prefix: 'Gary-Zero',
    logLevel: 'debug'
});

// Export for use in modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { Logger, logger };
} else if (typeof window !== 'undefined') {
    window.GaryLogger = logger;
}

// For backwards compatibility, provide console replacement
const consoleFallback = {
    log: (...args) => logger.log(args[0], { extra: args.slice(1) }),
    warn: (...args) => logger.warn(args[0], { extra: args.slice(1) }),
    error: (...args) => logger.error(args[0], { extra: args.slice(1) }),
    debug: (...args) => logger.debug(args[0], { extra: args.slice(1) }),
    group: (label) => logger.group(label),
    groupEnd: () => logger.groupEnd()
};

if (typeof window !== 'undefined') {
    window.devLogger = consoleFallback;
}