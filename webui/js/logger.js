/**
 * Logger utility for Gary-Zero web UI
 * Provides structured logging with different levels and optional production filtering
 */
(function() {
    'use strict';

    // Check if we're in production mode
    const isProduction = window.location.hostname.includes('railway.app') || 
                       window.location.hostname.includes('herokuapp.com') || 
                       window.location.hostname.includes('vercel.app') || 
                       window.location.hostname.includes('netlify.app');

    // Log levels
    const LogLevel = {
        DEBUG: 0,
        INFO: 1,
        WARN: 2,
        ERROR: 3
    };

    // Current log level (can be configured)
    const currentLogLevel = isProduction ? LogLevel.WARN : LogLevel.DEBUG;

    /**
     * Logger class
     */
    class Logger {
        constructor(module = 'Gary-Zero') {
            this.module = module;
        }

        /**
         * Log a debug message
         */
        debug(...args) {
            if (currentLogLevel <= LogLevel.DEBUG) {
                console.log(`[${this.module}] DEBUG:`, ...args);
            }
        }

        /**
         * Log an info message
         */
        info(...args) {
            if (currentLogLevel <= LogLevel.INFO) {
                console.info(`[${this.module}] INFO:`, ...args);
            }
        }

        /**
         * Log a warning
         */
        warn(...args) {
            if (currentLogLevel <= LogLevel.WARN) {
                console.warn(`[${this.module}] WARN:`, ...args);
            }
        }

        /**
         * Log an error
         */
        error(...args) {
            if (currentLogLevel <= LogLevel.ERROR) {
                console.error(`[${this.module}] ERROR:`, ...args);
            }
        }

        /**
         * Log a group of messages
         */
        group(label) {
            if (currentLogLevel <= LogLevel.DEBUG) {
                console.group(`[${this.module}] ${label}`);
            }
        }

        /**
         * End a group
         */
        groupEnd() {
            if (currentLogLevel <= LogLevel.DEBUG) {
                console.groupEnd();
            }
        }

        /**
         * Log a table
         */
        table(data) {
            if (currentLogLevel <= LogLevel.DEBUG) {
                console.table(data);
            }
        }

        /**
         * Time a section of code
         */
        time(label) {
            if (currentLogLevel <= LogLevel.DEBUG) {
                console.time(`[${this.module}] ${label}`);
            }
        }

        /**
         * End timing
         */
        timeEnd(label) {
            if (currentLogLevel <= LogLevel.DEBUG) {
                console.timeEnd(`[${this.module}] ${label}`);
            }
        }
    }

    // Export to window
    window.Logger = Logger;
    
    // Create a default logger instance
    window.logger = new Logger();
})();
