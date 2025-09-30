/**
 * DOM Helper Utilities
 * Provides safe DOM element access and validation
 */

(function() {
    'use strict';
    
    // Get unified logger instance
    const logger = (typeof window !== 'undefined' && window.createLogger) ? 
        window.createLogger('DOMHelpers') : 
        (typeof window !== 'undefined' && window.logger) ? 
        window.logger :
        // Fallback if unified logger not available
        {
            warn: (...args) => console.warn('[DOMHelpers]', ...args),
            error: (...args) => console.error('[DOMHelpers]', ...args)
        };
    
    /**
     * Wait for an element to appear in the DOM
     * @param {string} selector - CSS selector for the element
     * @param {number} timeout - Timeout in milliseconds (default: 5000)
     * @returns {Promise<Element>} Promise that resolves with the found element
     */
    function waitForElement(selector, timeout = 5000) {
        return new Promise((resolve, reject) => {
            const element = document.querySelector(selector);
            if (element) return resolve(element);
            
            const observer = new MutationObserver(() => {
                const found = document.querySelector(selector);
                if (found) {
                    observer.disconnect();
                    resolve(found);
                }
            });
            
            observer.observe(document.body, { childList: true, subtree: true });
            setTimeout(() => {
                observer.disconnect();
                reject(new Error(`Element ${selector} not found within ${timeout}ms`));
            }, timeout);
        });
    }
    
    /**
     * Safely get an element by ID with validation
     * @param {string} id - Element ID
     * @returns {Element|null} The element or null if not found
     */
    function safeGetElementById(id) {
        try {
            const element = document.getElementById(id);
            if (!element) {
                logger.warn(`Element with ID '${id}' not found`);
                return null;
            }
            return element;
        } catch (error) {
            logger.warn(`Error accessing element with ID '${id}':`, error.message);
            return null;
        }
    }
    
    /**
     * Safely get element value with type checking
     * @param {Element} element - DOM element
     * @returns {string} Element value or empty string
     */
    function safeGetElementValue(element) {
        if (!element || typeof element.value !== 'string') {
            return '';
        }
        return element.value;
    }
    
    /**
     * Validate that a node is a valid DOM Element
     * @param {any} node - Node to validate
     * @returns {boolean} True if node is a valid Element
     */
    function isValidElement(node) {
        return node && node.nodeType === 1 && typeof node.querySelector === 'function';
    }
    
    // Export utilities to global scope for use by other scripts
    window.DOMHelpers = {
        waitForElement,
        safeGetElementById,
        safeGetElementValue,
        isValidElement
    };
    
})();