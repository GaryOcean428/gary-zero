/**
 * Logging utility for Gary-Zero
 * Replaces direct console usage with configurable logging
 */
class Logger {
    constructor(context = 'App') {
        this.context = context;
        this.logLevel = this.getLogLevel();
        this.isDevelopment = this.isDevelopmentMode();
    }

    getLogLevel() {
        // Check for log level in localStorage or default to 'info'
        try {
            return localStorage.getItem('logLevel') || 'info';
        } catch {
            return 'info';
        }
    }

    isDevelopmentMode() {
        // Check if we're in development mode
        return window.location.hostname === 'localhost' || 
               window.location.hostname === '127.0.0.1' ||
               window.location.search.includes('debug=true');
    }

    shouldLog(level) {
        const levels = { error: 0, warn: 1, info: 2, debug: 3 };
        return levels[level] <= levels[this.logLevel];
    }

    formatMessage(level, message, ...args) {
        const timestamp = new Date().toISOString().slice(11, 23);
        const prefix = `[${timestamp}] ${level.toUpperCase()} [${this.context}]`;
        return [prefix, message, ...args];
    }

    error(message, ...args) {
        if (this.shouldLog('error')) {
            console.error(...this.formatMessage('error', message, ...args));
        }
    }

    warn(message, ...args) {
        if (this.shouldLog('warn')) {
            console.warn(...this.formatMessage('warn', message, ...args));
        }
    }

    info(message, ...args) {
        if (this.shouldLog('info') && this.isDevelopment) {
            console.info(...this.formatMessage('info', message, ...args));
        }
    }

    debug(message, ...args) {
        if (this.shouldLog('debug') && this.isDevelopment) {
            console.debug(...this.formatMessage('debug', message, ...args));
        }
    }

    log(message, ...args) {
        // Alias for info
        this.info(message, ...args);
    }
}

// Create default logger instance
const logger = new Logger();

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { Logger, logger };
} else {
    window.Logger = Logger;
    window.logger = logger;
}
