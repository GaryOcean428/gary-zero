/**
 * Alpine.js Error Recovery System
 * Provides global error handling and recovery mechanisms for Alpine.js components
 */

// Global Alpine error handler
if (typeof window !== 'undefined') {
    // Handle Alpine.js initialization errors
    window.addEventListener('alpine:init', () => {
        // Setup global Alpine error handlers if Alpine is available
        if (window.Alpine) {
            // Override Alpine's error handler
            const originalError = window.Alpine.onError;
            window.Alpine.onError = (error) => {
                console.error('Alpine component error:', error);
                
                // Attempt recovery for binding errors
                if (error.message && error.message.includes('Cannot read properties')) {
                    handleBindingError(error);
                }
                
                // Call original error handler if it exists
                if (originalError && typeof originalError === 'function') {
                    return originalError(error);
                }
                
                // Prevent error propagation by default
                return true;
            };
        }
    });

    // Handle Alpine errors that bubble up to the window
    window.addEventListener('alpine:error', (event) => {
        console.error('Alpine error event:', event.detail);
        
        // Attempt recovery for binding errors
        if (event.detail && event.detail.message && event.detail.message.includes('Cannot read properties')) {
            handleBindingError(event.detail, event.detail.el);
        }
    });

    // Generic error handler for uncaught Alpine errors
    window.addEventListener('error', (event) => {
        const error = event.error;
        if (error && error.stack && error.stack.includes('Alpine')) {
            console.error('Uncaught Alpine error:', error);
            
            // Try to recover from Alpine binding errors
            if (error.message && error.message.includes('Cannot read properties')) {
                handleBindingError(error);
                event.preventDefault(); // Prevent default browser error handling
            }
        }
    });
}

/**
 * Handle binding errors in Alpine components
 * @param {Error} error - The error object
 * @param {Element} element - The DOM element if available
 */
function handleBindingError(error, element = null) {
    console.warn('Attempting to recover from Alpine binding error:', error.message);
    
    try {
        // If we have an element, try to re-initialize it
        if (element && element._x_dataStack) {
            const component = element._x_dataStack[0];
            if (component && !component._recovered) {
                component._recovered = true;
                
                // Mark component for recovery
                console.log('Marking component for recovery...');
                
                // Re-initialize component after a short delay
                setTimeout(() => {
                    try {
                        if (window.Alpine && typeof window.Alpine.initTree === 'function') {
                            console.log('Re-initializing Alpine component...');
                            window.Alpine.initTree(element);
                        }
                    } catch (recoveryError) {
                        console.error('Component recovery failed:', recoveryError);
                    }
                }, 100);
            }
        } else {
            // Try to find and recover settings modal specifically
            recoverSettingsModal();
        }
    } catch (recoveryError) {
        console.error('Error recovery attempt failed:', recoveryError);
    }
}

/**
 * Attempt to recover the settings modal component specifically
 */
function recoverSettingsModal() {
    const modalElement = document.getElementById('settingsModal');
    if (modalElement) {
        console.log('Attempting to recover settings modal...');
        
        try {
            // Try to get the Alpine data
            if (window.Alpine && typeof window.Alpine.$data === 'function') {
                const modalData = window.Alpine.$data(modalElement);
                if (modalData) {
                    // Check if the problematic method is missing
                    if (!modalData._actualSaveSettings && typeof modalData._setupDebouncedSave === 'function') {
                        console.log('Re-initializing settings modal debounced save...');
                        modalData._setupDebouncedSave();
                    }
                }
            }
        } catch (modalRecoveryError) {
            console.error('Settings modal recovery failed:', modalRecoveryError);
        }
    }
}

/**
 * Safe Alpine component registration with error handling
 * @param {string} name - Component name
 * @param {Function} factory - Component factory function
 */
function safeRegisterAlpineComponent(name, factory) {
    if (!window.Alpine) {
        console.warn(`Cannot register ${name}: Alpine.js not available`);
        return false;
    }

    try {
        // Wrap the factory with error handling
        const safeFactory = () => {
            try {
                const component = factory();
                
                // Add recovery methods to component
                if (component && typeof component === 'object') {
                    // Add error recovery flag
                    component._errorRecovery = true;
                    
                    // Wrap init method with error handling
                    if (typeof component.init === 'function') {
                        const originalInit = component.init;
                        component.init = async function() {
                            try {
                                await originalInit.call(this);
                            } catch (initError) {
                                console.error(`Error initializing ${name}:`, initError);
                                // Try recovery
                                if (typeof this._setupDebouncedSave === 'function') {
                                    try {
                                        this._setupDebouncedSave();
                                    } catch (setupError) {
                                        console.error('Setup recovery failed:', setupError);
                                    }
                                }
                            }
                        };
                    }
                }
                
                return component;
            } catch (factoryError) {
                console.error(`Error creating ${name} component:`, factoryError);
                // Return minimal fallback component
                return {
                    _errorFallback: true,
                    init() {
                        console.log(`${name} running in error fallback mode`);
                    }
                };
            }
        };
        
        window.Alpine.data(name, safeFactory);
        console.log(`✅ Safely registered Alpine component: ${name}`);
        return true;
    } catch (registrationError) {
        console.error(`Failed to register Alpine component ${name}:`, registrationError);
        return false;
    }
}

/**
 * Alpine component health checker
 * Periodically checks component health and attempts recovery
 */
class AlpineHealthChecker {
    constructor() {
        this.checkInterval = null;
        this.healthChecks = new Map();
    }

    /**
     * Start health monitoring for Alpine components
     */
    startMonitoring() {
        if (this.checkInterval) {
            return; // Already monitoring
        }

        this.checkInterval = setInterval(() => {
            this.performHealthCheck();
        }, 30000); // Check every 30 seconds

        console.log('🏥 Alpine health monitoring started');
    }

    /**
     * Stop health monitoring
     */
    stopMonitoring() {
        if (this.checkInterval) {
            clearInterval(this.checkInterval);
            this.checkInterval = null;
        }
    }

    /**
     * Perform health check on Alpine components
     */
    performHealthCheck() {
        try {
            // Check settings modal specifically
            const settingsModal = document.getElementById('settingsModal');
            if (settingsModal && window.Alpine) {
                try {
                    const modalData = window.Alpine.$data(settingsModal);
                    if (modalData && !modalData._debouncedSaveSettings) {
                        console.warn('Settings modal health check failed - missing debounced save');
                        if (typeof modalData._setupDebouncedSave === 'function') {
                            modalData._setupDebouncedSave();
                            console.log('Settings modal auto-recovered');
                        }
                    }
                } catch (healthError) {
                    console.error('Health check failed for settings modal:', healthError);
                }
            }
        } catch (globalHealthError) {
            console.error('Global health check failed:', globalHealthError);
        }
    }
}

// Create and export health checker
const alpineHealthChecker = new AlpineHealthChecker();

// Auto-start health monitoring when Alpine is ready
if (typeof window !== 'undefined') {
    window.addEventListener('alpine:init', () => {
        // Start health monitoring after a short delay
        setTimeout(() => {
            alpineHealthChecker.startMonitoring();
        }, 5000);
    });

    // Make functions globally available
    window.safeRegisterAlpineComponent = safeRegisterAlpineComponent;
    window.alpineHealthChecker = alpineHealthChecker;
    window.recoverSettingsModal = recoverSettingsModal;
}

// Export for module environments
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        safeRegisterAlpineComponent,
        AlpineHealthChecker,
        recoverSettingsModal
    };
}