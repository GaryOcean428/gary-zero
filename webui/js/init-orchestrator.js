/**
 * Component Initialization Orchestrator
 * Handles Alpine.js and other component initialization in the correct order
 * Prevents race conditions and binding errors
 */

// Import unified logger
const logger = (typeof window !== 'undefined' && window.createLogger) ? 
    window.createLogger('InitOrchestrator') : 
    (typeof window !== 'undefined' && window.logger) ? 
    window.logger :
    // Fallback for when unified logger isn't loaded yet
    {
        debug: (...args) => console.log('[InitOrchestrator] DEBUG:', ...args),
        info: (...args) => console.info('[InitOrchestrator] INFO:', ...args),
        warn: (...args) => console.warn('[InitOrchestrator] WARN:', ...args),
        error: (...args) => console.error('[InitOrchestrator] ERROR:', ...args)
    };

class InitOrchestrator {
    constructor() {
        this.pendingInits = new Map();
        this.initialized = new Set();
        this.dependencies = new Map();
        this.initPromises = new Map();
        
        // Track component states for debugging
        this.states = new Map();
    }
    
    /**
     * Register a component for controlled initialization
     * @param {string} name - Component name
     * @param {Function} initFn - Initialization function
     * @param {Array} deps - Array of dependency component names
     */
    register(name, initFn, deps = []) {
        logger.debug(`Registering component: ${name} with dependencies: [${deps.join(', ')}]`);
        
        this.pendingInits.set(name, { fn: initFn, deps });
        this.dependencies.set(name, deps);
        this.states.set(name, 'registered');
        
        // Try to initialize immediately if dependencies are met
        this.tryInitialize(name);
    }
    
    /**
     * Try to initialize a component if its dependencies are ready
     * @param {string} name - Component name
     */
    async tryInitialize(name) {
        const component = this.pendingInits.get(name);
        if (!component || this.initialized.has(name) || this.initPromises.has(name)) {
            return;
        }
        
        // Check all dependencies are initialized
        const depsReady = component.deps.every(dep => this.initialized.has(dep));
        if (!depsReady) {
            logger.debug(`Component ${name} waiting for dependencies: [${component.deps.filter(dep => !this.initialized.has(dep)).join(', ')}]`);
            this.states.set(name, 'waiting');
            return;
        }
        
        // Initialize component
        this.states.set(name, 'initializing');
        const initPromise = this.initializeComponent(name, component);
        this.initPromises.set(name, initPromise);
        
        try {
            await initPromise;
        } catch (error) {
            logger.error(`Failed to initialize ${name}:`, error);
            this.states.set(name, 'failed');
            this.initPromises.delete(name);
        }
    }
    
    /**
     * Initialize a single component
     * @param {string} name - Component name
     * @param {Object} component - Component configuration
     */
    async initializeComponent(name, component) {
        try {
            logger.debug(`Initializing component: ${name}`);
            await component.fn();
            
            this.initialized.add(name);
            this.pendingInits.delete(name);
            this.initPromises.delete(name);
            this.states.set(name, 'initialized');
            
            logger.info(`✅ Initialized: ${name}`);
            
            // Try to initialize components waiting for this one
            for (const [pending, config] of this.pendingInits) {
                if (config.deps.includes(name)) {
                    await this.tryInitialize(pending);
                }
            }
        } catch (error) {
            logger.error(`❌ Failed to initialize ${name}:`, error);
            this.states.set(name, 'failed');
            throw error;
        }
    }
    
    /**
     * Mark a component as initialized externally
     * @param {string} name - Component name
     */
    markInitialized(name) {
        logger.debug(`Marking ${name} as externally initialized`);
        this.initialized.add(name);
        this.pendingInits.delete(name);
        this.states.set(name, 'initialized');
        
        // Try to initialize dependent components
        for (const [pending, config] of this.pendingInits) {
            if (config.deps.includes(name)) {
                this.tryInitialize(pending);
            }
        }
    }
    
    /**
     * Wait for a component to be initialized
     * @param {string} name - Component name
     * @returns {Promise} - Resolves when component is ready
     */
    waitFor(name) {
        if (this.initialized.has(name)) {
            return Promise.resolve();
        }
        
        if (this.initPromises.has(name)) {
            return this.initPromises.get(name);
        }
        
        // Return a promise that resolves when the component is initialized
        return new Promise((resolve, reject) => {
            const checkInitialized = () => {
                if (this.initialized.has(name)) {
                    resolve();
                } else if (this.states.get(name) === 'failed') {
                    reject(new Error(`Component ${name} failed to initialize`));
                } else {
                    setTimeout(checkInitialized, 50);
                }
            };
            checkInitialized();
        });
    }
    
    /**
     * Get initialization status report
     * @returns {Object} Status report
     */
    getStatus() {
        const report = {
            initialized: Array.from(this.initialized),
            pending: Array.from(this.pendingInits.keys()),
            states: Object.fromEntries(this.states),
            totalRegistered: this.initialized.size + this.pendingInits.size
        };
        
        return report;
    }
    
    /**
     * Force initialization of all pending components (use with caution)
     */
    async forceInitializeAll() {
        logger.warn('Force initializing all pending components...');
        
        const promises = [];
        for (const [name, component] of this.pendingInits) {
            promises.push(this.initializeComponent(name, component));
        }
        
        try {
            await Promise.allSettled(promises);
            logger.info('Force initialization completed');
        } catch (error) {
            logger.error('Force initialization failed:', error);
        }
    }
}

// Create global orchestrator instance
if (typeof window !== 'undefined') {
    window.initOrchestrator = new InitOrchestrator();
    
    // Debug helper
    window.getInitStatus = () => {
        return window.initOrchestrator.getStatus();
    };
}

// Export for module environments
if (typeof module !== 'undefined' && module.exports) {
    module.exports = InitOrchestrator;
} else if (typeof window !== 'undefined') {
    window.InitOrchestrator = InitOrchestrator;
}