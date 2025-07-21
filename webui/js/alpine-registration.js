/**
 * Alpine.js Component Registration Manager
 * 
 * Provides centralized, idempotent component registration with proper timing control
 * and duplicate prevention to resolve Alpine.js initialization issues.
 * 
 * Fixes:
 * - Timing issues with components registering before Alpine.js is ready
 * - Duplicate component registrations
 * - Race conditions in component initialization
 * - Lack of dependency resolution for component loading
 */

class AlpineComponentManager {
    constructor() {
        this.registeredComponents = new Set();
        this.pendingComponents = [];
        this.isAlpineReady = false;
        this.initPromise = null;
        this.retryCount = 0;
        this.maxRetries = 10;
        this.retryDelay = 100;
    }

    /**
     * Initialize the Alpine Component Manager
     * Sets up event listeners and processes any pending components
     */
    init() {
        // Prevent multiple initialization
        if (this.initPromise) {
            return this.initPromise;
        }

        this.initPromise = new Promise((resolve) => {
            const checkAlpineReady = () => {
                if (window.Alpine && typeof window.Alpine.data === 'function') {
                    this.isAlpineReady = true;
                    this.processPendingComponents();
                    console.log('✅ Alpine Component Manager initialized');
                    resolve();
                } else if (this.retryCount < this.maxRetries) {
                    this.retryCount++;
                    setTimeout(checkAlpineReady, this.retryDelay);
                } else {
                    console.error('❌ Alpine.js not available after max retries, some components may not function');
                    resolve(); // Resolve anyway to prevent hanging
                }
            };

            // Check if Alpine is already available
            if (window.Alpine && typeof window.Alpine.data === 'function') {
                this.isAlpineReady = true;
                this.processPendingComponents();
                console.log('✅ Alpine Component Manager initialized (Alpine already ready)');
                resolve();
            } else {
                // Listen for Alpine initialization
                document.addEventListener('alpine:init', () => {
                    this.isAlpineReady = true;
                    this.processPendingComponents();
                    console.log('✅ Alpine Component Manager initialized on alpine:init');
                    resolve();
                });

                // Also poll for Alpine availability as a fallback
                checkAlpineReady();
            }
        });

        return this.initPromise;
    }

    /**
     * Register an Alpine.js component with duplicate prevention
     * @param {string} name - Component name
     * @param {Function} definition - Component definition factory function
     * @param {Object} options - Optional registration options
     */
    registerComponent(name, definition, options = {}) {
        if (!name || typeof name !== 'string') {
            console.error('❌ Component name must be a non-empty string');
            return;
        }

        if (typeof definition !== 'function') {
            console.error('❌ Component definition must be a function');
            return;
        }

        // Check for duplicate registration
        if (this.registeredComponents.has(name)) {
            if (!options.allowOverride) {
                console.warn(`⚠️ Component ${name} already registered, skipping`);
                return;
            } else {
                console.warn(`⚠️ Component ${name} already registered, overriding`);
                this.registeredComponents.delete(name);
            }
        }

        const component = { 
            name, 
            definition, 
            options: { ...options },
            timestamp: Date.now()
        };
        
        if (this.isAlpineReady) {
            this.doRegisterComponent(component);
        } else {
            this.pendingComponents.push(component);
            console.log(`📋 Component ${name} queued for registration`);
            
            // Initialize manager if not already done
            this.init();
        }
    }

    /**
     * Actually register the component with Alpine.js
     * @param {Object} component - Component object with name, definition, and options
     */
    doRegisterComponent({ name, definition, options }) {
        try {
            // Ensure Alpine is available
            if (!window.Alpine || typeof window.Alpine.data !== 'function') {
                throw new Error('Alpine.js not available');
            }

            // Create the component with error boundary
            const safeDefinition = () => {
                try {
                    const result = definition();
                    
                    // Validate the result is an object
                    if (!result || typeof result !== 'object') {
                        throw new Error(`Component ${name} factory must return an object`);
                    }
                    
                    return result;
                } catch (error) {
                    console.error(`❌ Component ${name} factory failed:`, error);
                    
                    // Return fallback component state
                    return {
                        // Fallback component state
                        init() {
                            console.warn(`⚠️ Using fallback for component: ${name}`);
                        },
                        error: error.message,
                        fallback: true
                    };
                }
            };

            // Register with Alpine
            Alpine.data(name, safeDefinition);
            this.registeredComponents.add(name);
            
            console.log(`✅ Alpine component '${name}' registered successfully`);
            
            // Emit custom event for component registration
            document.dispatchEvent(new CustomEvent('alpine:component:registered', {
                detail: { name, options }
            }));
            
        } catch (error) {
            console.error(`❌ Failed to register Alpine component '${name}':`, error);
            
            // Emit error event
            document.dispatchEvent(new CustomEvent('alpine:component:error', {
                detail: { name, error: error.message }
            }));
        }
    }

    /**
     * Process all pending components in registration queue
     */
    processPendingComponents() {
        if (!this.isAlpineReady) {
            console.warn('⚠️ Cannot process pending components: Alpine not ready');
            return;
        }

        console.log(`📋 Processing ${this.pendingComponents.length} pending components`);
        
        while (this.pendingComponents.length > 0) {
            const component = this.pendingComponents.shift();
            this.doRegisterComponent(component);
        }
        
        console.log('✅ All pending components processed');
    }

    /**
     * Check if a component is registered
     * @param {string} name - Component name
     * @returns {boolean} - True if component is registered
     */
    isComponentRegistered(name) {
        return this.registeredComponents.has(name);
    }

    /**
     * Get list of registered component names
     * @returns {Array<string>} - Array of registered component names
     */
    getRegisteredComponents() {
        return Array.from(this.registeredComponents);
    }

    /**
     * Get number of pending components
     * @returns {number} - Number of components waiting to be registered
     */
    getPendingCount() {
        return this.pendingComponents.length;
    }

    /**
     * Get manager status for debugging
     * @returns {Object} - Manager status information
     */
    getStatus() {
        return {
            isAlpineReady: this.isAlpineReady,
            registeredCount: this.registeredComponents.size,
            pendingCount: this.pendingComponents.length,
            registeredComponents: this.getRegisteredComponents(),
            isInitialized: !!this.initPromise
        };
    }

    /**
     * Reset the manager (useful for testing)
     */
    reset() {
        this.registeredComponents.clear();
        this.pendingComponents = [];
        this.isAlpineReady = false;
        this.initPromise = null;
        this.retryCount = 0;
    }
}

/**
 * Enhanced component registration function with error boundaries
 * @param {string} name - Component name
 * @param {Function} factory - Component factory function
 * @param {Object} options - Registration options
 */
function safeRegisterAlpineComponent(name, factory, options = {}) {
    if (!window.alpineManager) {
        console.error('❌ Alpine Component Manager not available');
        return;
    }
    
    window.alpineManager.registerComponent(name, factory, options);
}

// Create and expose global component manager instance
if (!window.alpineManager) {
    window.alpineManager = new AlpineComponentManager();
    
    // Auto-initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => {
            window.alpineManager.init();
        });
    } else {
        // DOM already loaded
        window.alpineManager.init();
    }
    
    console.log('🚀 Alpine Component Manager created and initializing');
}

// Expose utilities globally
window.safeRegisterAlpineComponent = safeRegisterAlpineComponent;

// Export for module usage
export { AlpineComponentManager, safeRegisterAlpineComponent };
export default window.alpineManager;