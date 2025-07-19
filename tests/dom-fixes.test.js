import { describe, it, expect, beforeEach, vi } from "vitest";
import { JSDOM } from "jsdom";

// Test the DOM helper utilities and chat input fixes
describe("DOM Helpers and Chat Input Fixes", () => {
    let dom;
    let window;
    let document;

    beforeEach(() => {
        // Create a fresh DOM environment for each test
        dom = new JSDOM(`
            <!DOCTYPE html>
            <html>
                <head></head>
                <body>
                    <textarea id="chat-input" placeholder="Type your message..."></textarea>
                    <button id="send-button" disabled>Send</button>
                    <div id="char-count" style="display: none;"></div>
                </body>
            </html>
        `);
        window = dom.window;
        document = window.document;
        global.window = window;
        global.document = document;
        
        // Load DOM helpers
        const domHelpersScript = `
        (function() {
            'use strict';
            
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
                        reject(new Error(\`Element \${selector} not found within \${timeout}ms\`));
                    }, timeout);
                });
            }
            
            function safeGetElementById(id) {
                try {
                    const element = document.getElementById(id);
                    if (!element) {
                        console.warn(\`Element with ID '\${id}' not found\`);
                        return null;
                    }
                    return element;
                } catch (error) {
                    console.warn(\`Error accessing element with ID '\${id}':\`, error.message);
                    return null;
                }
            }
            
            function safeGetElementValue(element) {
                if (!element || typeof element.value !== 'string') {
                    return '';
                }
                return element.value;
            }
            
            function isValidElement(node) {
                return node && node.nodeType === 1 && typeof node.querySelector === 'function';
            }
            
            window.DOMHelpers = {
                waitForElement,
                safeGetElementById,
                safeGetElementValue,
                isValidElement
            };
        })();
        `;
        
        // Execute DOM helpers in the window context
        window.eval(domHelpersScript);
    });

    describe("DOM Helpers", () => {
        it("should safely get element by ID", () => {
            const chatInput = window.DOMHelpers.safeGetElementById('chat-input');
            expect(chatInput).toBeTruthy();
            expect(chatInput.id).toBe('chat-input');
        });

        it("should return null for non-existent element", () => {
            const nonExistent = window.DOMHelpers.safeGetElementById('non-existent');
            expect(nonExistent).toBeNull();
        });

        it("should safely get element value", () => {
            const chatInput = document.getElementById('chat-input');
            chatInput.value = 'test message';
            
            const value = window.DOMHelpers.safeGetElementValue(chatInput);
            expect(value).toBe('test message');
        });

        it("should return empty string for invalid element value", () => {
            const value = window.DOMHelpers.safeGetElementValue(null);
            expect(value).toBe('');
        });

        it("should validate DOM elements correctly", () => {
            const chatInput = document.getElementById('chat-input');
            const textNode = document.createTextNode('text');
            
            expect(window.DOMHelpers.isValidElement(chatInput)).toBe(true);
            expect(window.DOMHelpers.isValidElement(textNode)).toBe(false);
            expect(window.DOMHelpers.isValidElement(null)).toBeFalsy();
        });
    });

    describe("Chat Input Validation", () => {
        it("should handle missing chat input element gracefully", () => {
            // Remove chat input element
            document.getElementById('chat-input').remove();
            
            // Mock console.warn to check if warning is logged
            const consoleSpy = vi.spyOn(console, 'warn').mockImplementation(() => {});
            
            const updateSendButton = () => {
                const chatInput = window.DOMHelpers?.safeGetElementById('chat-input');
                const inputValue = window.DOMHelpers?.safeGetElementValue(chatInput) || '';
                if (typeof inputValue !== 'string') {
                    console.warn('Chat input value is not a string');
                    return;
                }
                // Function would continue normally
            };
            
            updateSendButton();
            expect(consoleSpy).toHaveBeenCalled();
            
            consoleSpy.mockRestore();
        });

        it("should handle undefined/null values safely", () => {
            const updateSendButton = (chatInput) => {
                const inputValue = window.DOMHelpers?.safeGetElementValue(chatInput) || '';
                if (typeof inputValue !== 'string') {
                    return false; // Error condition
                }
                const isEmpty = !inputValue.trim();
                return !isEmpty; // Return true if not empty
            };
            
            // Test with null element
            expect(updateSendButton(null)).toBe(false);
            
            // Test with valid element
            const chatInput = document.getElementById('chat-input');
            chatInput.value = 'test';
            expect(updateSendButton(chatInput)).toBe(true);
            
            // Test with empty value
            chatInput.value = '';
            expect(updateSendButton(chatInput)).toBe(false);
        });

        it("should handle MutationObserver node validation", () => {
            const isValidElement = window.DOMHelpers.isValidElement;
            
            // Mock MutationObserver callback logic
            const processNode = (node) => {
                if (!isValidElement(node)) return false;
                return true;
            };
            
            const validElement = document.createElement('div');
            const textNode = document.createTextNode('text');
            
            expect(processNode(validElement)).toBe(true);
            expect(processNode(textNode)).toBe(false);
            expect(processNode(null)).toBe(false);
            expect(processNode(undefined)).toBe(false);
        });
    });

    describe("Error Prevention", () => {
        it("should prevent trim() errors on undefined values", () => {
            const chatInput = document.getElementById('chat-input');
            
            // Simulate undefined value scenario
            Object.defineProperty(chatInput, 'value', {
                get: () => undefined,
                configurable: true
            });
            
            const safeGetValue = () => {
                const inputValue = window.DOMHelpers.safeGetElementValue(chatInput);
                return inputValue; // Should return empty string, not undefined
            };
            
            const result = safeGetValue();
            expect(result).toBe('');
            expect(() => result.trim()).not.toThrow();
        });
    });
});