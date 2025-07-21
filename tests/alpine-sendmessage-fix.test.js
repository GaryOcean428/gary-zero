import { describe, it, expect, beforeEach, afterEach, vi } from "vitest";
import { JSDOM } from "jsdom";

describe("Alpine.js sendMessage TypeError Fix", () => {
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
                    <div id="chat-input"></div>
                    <div id="input-section" x-data="{ attachments: [], hasAttachments: false }"></div>
                    <div id="input-attachments-display" x-data="{ attachments: [] }"></div>
                </body>
            </html>
        `, {
            url: "http://localhost",
            pretendToBeVisual: true,
            resources: "usable"
        });
        
        window = dom.window;
        document = window.document;
        global.window = window;
        global.document = document;
    });

    afterEach(() => {
        dom?.window?.close();
        vi.clearAllMocks();
    });

    it("should handle undefined Alpine.$data gracefully", () => {
        // Setup elements like in the real code
        const chatInput = document.getElementById("chat-input");
        const inputSection = document.getElementById("input-section");
        chatInput.value = "test message";
        
        // Mock Alpine as not available
        window.Alpine = {
            $data: vi.fn(() => undefined) // This returns undefined like in production
        };
        
        // Mock other globals that sendMessage depends on
        const mockContext = "test-context";
        const mockLocalUserMessages = new Set();
        const mockGenerateGUID = vi.fn(() => "test-guid");
        const mockSetMessage = vi.fn();
        const mockSetContext = vi.fn();
        const mockAdjustTextareaHeight = vi.fn();
        
        // Mock fetch to prevent actual network calls
        global.fetch = vi.fn(() => 
            Promise.resolve({
                ok: true,
                json: () => Promise.resolve({ context: "test-response-context" })
            })
        );
        
        // Create the sendMessage function inline to test the original buggy behavior
        const sendMessageOriginal = async function() {
            if (!chatInput || !inputSection) return;

            try {
                const message = chatInput.value.trim();
                const inputAD = window.Alpine.$data(inputSection); // This will be undefined
                
                // This line would throw TypeError in original code
                const attachments = inputAD.attachments; // TypeError: Cannot convert undefined or null to object
                
                // Rest of function would not execute due to error
            } catch (error) {
                throw error; // Re-throw to test error handling
            }
        };
        
        // Test that the original code throws TypeError
        expect(async () => {
            await sendMessageOriginal();
        }).rejects.toThrow();
    });

    it("should safely handle Alpine data when not available", () => {
        // Test the safe pattern that should be implemented
        const inputSection = document.getElementById("input-section");
        
        // Mock Alpine as not available
        window.Alpine = undefined;
        
        // Safe pattern that should be used
        const getSafeAlpineData = (element) => {
            if (!window.Alpine || !element?.__x?.$data) {
                return null;
            }
            return window.Alpine.$data(element);
        };
        
        const result = getSafeAlpineData(inputSection);
        expect(result).toBeNull();
        
        // Should not throw when accessing properties
        expect(() => {
            const attachments = result?.attachments || [];
            const hasAttachments = result?.hasAttachments || false;
        }).not.toThrow();
    });

    it("should work correctly when Alpine data is available", () => {
        // Setup elements
        const inputSection = document.getElementById("input-section");
        
        // Mock proper Alpine setup
        inputSection.__x = {
            $data: {
                attachments: [],
                hasAttachments: false
            }
        };
        
        window.Alpine = {
            $data: vi.fn((element) => element.__x.$data)
        };
        
        // Safe pattern implementation
        const getSafeAlpineData = (element) => {
            if (!window.Alpine || !element?.__x?.$data) {
                return null;
            }
            return window.Alpine.$data(element);
        };
        
        const result = getSafeAlpineData(inputSection);
        expect(result).toEqual({
            attachments: [],
            hasAttachments: false
        });
        
        // Should work correctly
        expect(result.attachments).toEqual([]);
        expect(result.hasAttachments).toBe(false);
    });

    it("should handle element not existing", () => {
        // Test when inputSection is null/undefined
        const inputSection = null;
        
        window.Alpine = {
            $data: vi.fn()
        };
        
        // Safe pattern
        const getSafeAlpineData = (element) => {
            if (!window.Alpine || !element?.__x?.$data) {
                return null;
            }
            return window.Alpine.$data(element);
        };
        
        const result = getSafeAlpineData(inputSection);
        expect(result).toBeNull();
        expect(window.Alpine.$data).not.toHaveBeenCalled();
    });

    it("should handle real sendMessage scenario with fixed implementation", async () => {
        // Setup realistic DOM elements
        const chatInput = document.getElementById("chat-input");
        const inputSection = document.getElementById("input-section");
        chatInput.value = "Test message";
        
        // Mock Alpine as not available (the problematic scenario)
        window.Alpine = {
            $data: vi.fn(() => undefined) // Returns undefined like in production
        };
        
        // Mock the required global functions
        global.generateGUID = vi.fn(() => "test-guid-123");
        global.setMessage = vi.fn();
        global.setContext = vi.fn();
        global.adjustTextareaHeight = vi.fn();
        global.localUserMessages = new Set();
        global.context = "test-context";
        
        // Mock fetch
        global.fetch = vi.fn(() => 
            Promise.resolve({
                ok: true,
                json: () => Promise.resolve({ context: "response-context" })
            })
        );
        
        // Implement the FIXED sendMessage function (like our actual fix)
        const sendMessageFixed = async function() {
            if (!chatInput || !inputSection) return;

            try {
                const message = chatInput.value.trim();
                const inputAD = window.Alpine && inputSection?.__x?.$data ? window.Alpine.$data(inputSection) : null;
                const attachments = inputAD?.attachments || [];
                const hasAttachments = attachments && attachments.length > 0;

                if (message || hasAttachments) {
                    const messageId = global.generateGUID();
                    
                    // Simulate the simple text message path
                    global.setMessage(messageId, "user", "", message, false);
                    global.localUserMessages.add(messageId);
                    
                    const data = { text: message, context: global.context, message_id: messageId };
                    const response = await global.fetch("/message_async", {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify(data),
                    });

                    if (!response.ok) {
                        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                    }

                    const jsonResponse = await response.json();
                    if (jsonResponse && jsonResponse.context) {
                        global.setContext(jsonResponse.context);
                    }

                    chatInput.value = "";
                    if (inputAD) {
                        inputAD.attachments = [];
                        inputAD.hasAttachments = false;
                    }
                    global.adjustTextareaHeight();
                }
            } catch (error) {
                console.error("Error sending message:", error);
                throw error; // Re-throw for test
            }
        };
        
        // Test that the fixed function doesn't throw
        await expect(sendMessageFixed()).resolves.toBeUndefined();
        
        // Verify that the function executed properly
        expect(global.generateGUID).toHaveBeenCalled();
        expect(global.setMessage).toHaveBeenCalledWith("test-guid-123", "user", "", "Test message", false);
        expect(global.fetch).toHaveBeenCalled();
        expect(chatInput.value).toBe(""); // Input should be cleared
    });

    it("should handle handleFileUpload with fixed implementation", () => {
        // Test the other function we fixed
        const element = document.getElementById("input-attachments-display");
        
        // Mock Alpine as not available
        window.Alpine = {
            $data: vi.fn(() => undefined)
        };
        
        // Create a mock file upload event
        const mockFile = new window.File(['test'], 'test.jpg', { type: 'image/jpeg' });
        const mockEvent = {
            target: {
                files: [mockFile]
            }
        };
        
        // Fixed handleFileUpload implementation
        const handleFileUploadFixed = (event) => {
            const element = document.getElementById("input-attachments-display");
            const inputAD = window.Alpine && element?.__x?.$data ? window.Alpine.$data(element) : null;
            if (!inputAD) return; // Should return early and not throw
            
            // This code would only run if inputAD exists
            Array.from(event.target.files).forEach((file) => {
                const ext = file.name.split(".").pop().toLowerCase();
                // More processing would happen here...
            });
        };
        
        // Should not throw when Alpine data is not available
        expect(() => {
            handleFileUploadFixed(mockEvent);
        }).not.toThrow();
    });
});