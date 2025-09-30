/**
 * Unified Logger Module - DRY Implementation
 * Consolidates console-logger.js and logger.js functionality
 * Provides consistent logging across all Gary-Zero web UI components
 */

class UnifiedLogger {
    constructor(options = {}) {
        this.module = options.module || 'Gary-Zero';
        this.isDevelopment = this.detectDevelopment();
        this.logLevel = options.logLevel || (this.isDevelopment ? 'debug' : 'warn');
        this.prefix = options.prefix || this.formatPrefix();
        this.enableGroups = this.hasConsoleGroup();
    }

    detectDevelopment() {
        if (typeof window === 'undefined') return false;
        
        const hostname = window.location.hostname;
        const port = window.location.port;
        
        // Development environment detection
        const isDevelopmentHost = (
            hostname === 'localhost' || 
            hostname === '127.0.0.1' ||
            hostname.startsWith('192.168.') ||
            hostname.endsWith('.local') ||
            hostname.includes('dev') ||
            hostname.includes('staging')
        );
        
        const isDevelopmentPort = port && ['3000', '3001', '5000', '5675', '8000', '8080'].includes(port);
        
        // Production environment detection
        const isProduction = (
            hostname.includes('railway.app') || 
            hostname.includes('herokuapp.com') || 
            hostname.includes('vercel.app') || 
            hostname.includes('netlify.app')
        );
        
        return !isProduction && (isDevelopmentHost || isDevelopmentPort);
    }

    formatPrefix() {
        return `[${this.module}]`;
    }

    hasConsoleGroup() {
        return typeof console.group === 'function' && typeof console.groupEnd === 'function';
    }

    shouldLog(level) {
        const levels = { debug: 0, info: 1, warn: 2, error: 3 };
        return levels[level] >= levels[this.logLevel];
    }

    formatMessage(...args) {
        return [this.prefix, ...args];
    }

    // Core logging methods
    debug(...args) {
        if (this.shouldLog('debug') && this.isDevelopment) {
            console.log(...this.formatMessage('DEBUG:', ...args));
        }
    }

    info(...args) {
        if (this.shouldLog('info')) {
            console.info(...this.formatMessage('INFO:', ...args));
        }
    }

    log(...args) {
        // Alias for info to maintain backward compatibility
        this.info(...args);
    }

    warn(...args) {
        if (this.shouldLog('warn')) {
            console.warn(...this.formatMessage('WARN:', ...args));
        }
    }

    error(...args) {
        if (this.shouldLog('error')) {
            console.error(...this.formatMessage('ERROR:', ...args));
        }
    }

    // Grouping methods for organized logging
    group(label, ...args) {
        if (this.enableGroups && this.shouldLog('info')) {
            console.group(...this.formatMessage(label, ...args));
        }
    }

    groupCollapsed(label, ...args) {
        if (this.enableGroups && this.shouldLog('info')) {
            console.groupCollapsed(...this.formatMessage(label, ...args));
        }
    }

    groupEnd() {
        if (this.enableGroups) {
            console.groupEnd();
        }
    }

    // Utility methods
    table(data, columns) {
        if (this.shouldLog('info') && typeof console.table === 'function') {
            console.table(data, columns);
        }
    }

    time(label) {
        if (this.shouldLog('debug') && typeof console.time === 'function') {
            console.time(`${this.prefix} ${label}`);
        }
    }

    timeEnd(label) {
        if (this.shouldLog('debug') && typeof console.timeEnd === 'function') {
            console.timeEnd(`${this.prefix} ${label}`);
        }
    }

    // Performance timing wrapper
    async measure(label, asyncFn) {
        if (!this.shouldLog('debug')) {
            return await asyncFn();
        }
        
        this.time(label);
        try {
            const result = await asyncFn();
            this.timeEnd(label);
            return result;
        } catch (error) {
            this.timeEnd(label);
            this.error(`Error in ${label}:`, error);
            throw error;
        }
    }
}

// Global logger factory function
function createLogger(module = 'Gary-Zero', options = {}) {
    return new UnifiedLogger({ module, ...options });
}

// Default global logger instance
const logger = createLogger();

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { UnifiedLogger, createLogger, logger };
}

// Global window object for browser usage
if (typeof window !== 'undefined') {
    window.UnifiedLogger = UnifiedLogger;
    window.createLogger = createLogger;
    window.logger = logger;
}

/**
 * Usage Examples:
 * 
 * // Use global logger
 * logger.info('Application started');
 * logger.error('Something went wrong', error);
 * 
 * // Create module-specific logger
 * const moduleLogger = createLogger('MyModule');
 * moduleLogger.debug('Debug information');
 * 
 * // Group related logs
 * logger.group('Processing data');
 * logger.info('Step 1 complete');
 * logger.info('Step 2 complete');
 * logger.groupEnd();
 * 
 * // Performance measurement
 * await logger.measure('API Call', async () => {
 *     return await fetch('/api/data');
 * });
 */