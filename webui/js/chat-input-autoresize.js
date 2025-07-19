/**
 * Chat Input Auto-Resize Enhancement
 * Provides auto-expanding textarea functionality for improved user experience
 */

(function() {
    'use strict';
    
    /**
     * Auto-resize a textarea element based on its content
     * @param {HTMLTextAreaElement} textarea - The textarea element to resize
     */
    function autoResizeTextarea(textarea) {
        if (!textarea) return;
        
        // Reset height to auto for accurate measurement
        textarea.style.height = 'auto';
        
        // Calculate new height based on scroll height with constraints
        const minHeight = 40; // Match CSS min-height
        const maxHeight = 200; // Match CSS max-height
        const newHeight = Math.min(maxHeight, Math.max(minHeight, textarea.scrollHeight));
        
        // Apply the new height
        textarea.style.height = newHeight + 'px';
        
        // Handle overflow for content exceeding max height
        if (textarea.scrollHeight > maxHeight) {
            textarea.style.overflowY = 'auto';
        } else {
            textarea.style.overflowY = 'hidden';
        }
    }
    
    /**
     * Initialize auto-resize functionality for chat inputs
     */
    function initializeChatInputAutoResize() {
        // Find all chat input elements
        const chatInputs = document.querySelectorAll('#chat-input, textarea[data-chat-input], .chat-input');
        
        chatInputs.forEach(textarea => {
            // Add input event listener for real-time resizing
            textarea.addEventListener('input', () => autoResizeTextarea(textarea));
            
            // Add paste event listener with slight delay for content processing
            textarea.addEventListener('paste', () => {
                setTimeout(() => autoResizeTextarea(textarea), 0);
            });
            
            // Handle programmatic value changes (with browser compatibility check)
            try {
                const textareaPrototype = Object.getPrototypeOf(textarea);
                const originalSetter = Object.getOwnPropertyDescriptor(textareaPrototype, 'value')?.set;
                if (originalSetter) {
                    Object.defineProperty(textarea, 'value', {
                        get() {
                            return originalSetter.call(this);
                        },
                        set(newValue) {
                            originalSetter.call(this, newValue);
                            autoResizeTextarea(this);
                        }
                    });
                }
            } catch (error) {
                // Fallback for browsers that don't support property descriptor manipulation
                console.warn('Could not enhance textarea value setter:', error.message);
            }
            
            // Initial resize on page load
            autoResizeTextarea(textarea);
        });
        
        console.log('✅ Chat input auto-resize initialized for', chatInputs.length, 'elements');
    }
    
    /**
     * Environment-based feature flag check
     * @returns {boolean} Whether auto-resize should be enabled
     */
    function shouldEnableAutoResize() {
        // Check for environment variable override (could be set by server)
        if (window.CHAT_AUTO_RESIZE_ENABLED !== undefined) {
            return window.CHAT_AUTO_RESIZE_ENABLED;
        }
        
        // Default to enabled for better UX
        return true;
    }
    
    /**
     * Production-safe initialization
     */
    function init() {
        try {
            if (!shouldEnableAutoResize()) {
                console.log('ℹ️  Chat input auto-resize disabled by configuration');
                return;
            }
            
            // Initialize when DOM is ready
            if (document.readyState === 'loading') {
                document.addEventListener('DOMContentLoaded', initializeChatInputAutoResize);
            } else {
                initializeChatInputAutoResize();
            }
            
            // Re-initialize for dynamically added elements
            const observer = new MutationObserver(mutations => {
                mutations.forEach(mutation => {
                    mutation.addedNodes.forEach(node => {
                        // Enhanced validation for DOM nodes
                        if (!node || node.nodeType !== Node.ELEMENT_NODE) return;
                        
                        // Use DOM helper for validation with fallback
                        const isValidElement = window.DOMHelpers?.isValidElement || 
                            ((n) => n && n.nodeType === 1 && typeof n.querySelector === 'function');
                        
                        if (!isValidElement(node)) return;
                        
                        const chatInputs = node.matches && node.matches('#chat-input, textarea[data-chat-input], .chat-input') 
                            ? [node] 
                            : node.querySelectorAll ? node.querySelectorAll('#chat-input, textarea[data-chat-input], .chat-input') 
                            : [];
                        
                        chatInputs.forEach(textarea => {
                            if (!textarea || !textarea.addEventListener) return; // Validate textarea element
                            textarea.addEventListener('input', () => autoResizeTextarea(textarea));
                            textarea.addEventListener('paste', () => {
                                setTimeout(() => autoResizeTextarea(textarea), 0);
                            });
                            autoResizeTextarea(textarea);
                        });
                    });
                });
            });
            
            // Ensure document.body is available before observing
            if (document.body) {
                observer.observe(document.body, {
                    childList: true,
                    subtree: true
                });
            } else {
                // Wait for document.body to be available
                const bodyCheckInterval = setInterval(() => {
                    if (document.body) {
                        clearInterval(bodyCheckInterval);
                        observer.observe(document.body, {
                            childList: true,
                            subtree: true
                        });
                    }
                }, 10);
            }
            
        } catch (error) {
            console.warn('⚠️  Chat input auto-resize initialization failed:', error.message);
        }
    }
    
    // Export for manual initialization if needed
    window.initChatInputAutoResize = initializeChatInputAutoResize;
    window.autoResizeTextarea = autoResizeTextarea;
    
    // Auto-initialize
    init();
    
})();