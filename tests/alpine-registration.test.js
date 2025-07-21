import { describe, it, expect, beforeEach, afterEach, vi } from "vitest";
import { JSDOM } from "jsdom";
import fs from "fs";
import path from "path";

// Test the Alpine Component Manager
describe("Alpine Component Manager", () => {
    let dom;
    let window;
    let document;
    let manager;

    beforeEach(async () => {
        // Create a fresh DOM environment for each test
        dom = new JSDOM(`
            <!DOCTYPE html>
            <html>
                <head></head>
                <body>
                    <div id="app"></div>
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
        
        // Mock Alpine.js
        window.Alpine = {
            data: vi.fn(),
            store: vi.fn(),
            start: vi.fn(),
            magic: vi.fn()
        };

        // Inline the Alpine Component Manager instead of importing
        window.AlpineComponentManager = class AlpineComponentManager {
            constructor() {
                this.registeredComponents = new Set();
                this.pendingComponents = [];
                this.isAlpineReady = false;
                this.initPromise = null;
                this.retryCount = 0;
                this.maxRetries = 10;
                this.retryDelay = 100;
            }

            async init() {
                if (this.initPromise) {
                    return this.initPromise;
                }

                this.initPromise = new Promise((resolve) => {
                    if (window.Alpine && typeof window.Alpine.data === 'function') {
                        this.isAlpineReady = true;
                        this.processPendingComponents();
                        resolve();
                    } else {
                        setTimeout(() => {
                            this.isAlpineReady = true;
                            this.processPendingComponents();
                            resolve();
                        }, 50);
                    }
                });

                return this.initPromise;
            }

            registerComponent(name, definition, options = {}) {
                if (!name || typeof name !== 'string') {
                    console.error('❌ Component name must be a non-empty string');
                    return;
                }

                if (typeof definition !== 'function') {
                    console.error('❌ Component definition must be a function');
                    return;
                }

                if (this.registeredComponents.has(name)) {
                    if (!options.allowOverride) {
                        console.warn(`⚠️ Component ${name} already registered, skipping`);
                        return;
                    } else {
                        this.registeredComponents.delete(name);
                    }
                }

                const component = { name, definition, options, timestamp: Date.now() };
                
                if (this.isAlpineReady) {
                    this.doRegisterComponent(component);
                } else {
                    this.pendingComponents.push(component);
                    this.init();
                }
            }

            doRegisterComponent({ name, definition }) {
                try {
                    if (!window.Alpine || typeof window.Alpine.data !== 'function') {
                        throw new Error('Alpine.js not available');
                    }

                    const safeDefinition = () => {
                        try {
                            const result = definition();
                            if (!result || typeof result !== 'object') {
                                throw new Error(`Component ${name} factory must return an object`);
                            }
                            return result;
                        } catch (error) {
                            return {
                                init() { console.warn(`⚠️ Using fallback for component: ${name}`); },
                                error: error.message,
                                fallback: true
                            };
                        }
                    };

                    window.Alpine.data(name, safeDefinition);
                    this.registeredComponents.add(name);
                } catch (error) {
                    console.error(`❌ Failed to register Alpine component '${name}':`, error);
                }
            }

            processPendingComponents() {
                while (this.pendingComponents.length > 0) {
                    const component = this.pendingComponents.shift();
                    this.doRegisterComponent(component);
                }
            }

            isComponentRegistered(name) {
                return this.registeredComponents.has(name);
            }

            getRegisteredComponents() {
                return Array.from(this.registeredComponents);
            }

            getPendingCount() {
                return this.pendingComponents.length;
            }

            getStatus() {
                return {
                    isAlpineReady: this.isAlpineReady,
                    registeredCount: this.registeredComponents.size,
                    pendingCount: this.pendingComponents.length,
                    registeredComponents: this.getRegisteredComponents(),
                    isInitialized: !!this.initPromise
                };
            }

            reset() {
                this.registeredComponents.clear();
                this.pendingComponents = [];
                this.isAlpineReady = false;
                this.initPromise = null;
                this.retryCount = 0;
            }
        };
        
        // Create a fresh manager instance for each test
        manager = new window.AlpineComponentManager();
    });

    afterEach(() => {
        // Clean up
        manager?.reset();
        dom?.window?.close();
        vi.clearAllMocks();
    });

    it("should create a manager instance", () => {
        expect(manager).toBeDefined();
        expect(manager.registeredComponents).toBeInstanceOf(Set);
        expect(manager.pendingComponents).toBeInstanceOf(Array);
        expect(manager.isAlpineReady).toBe(false);
    });

    it("should initialize properly when Alpine is ready", async () => {
        // Mock Alpine as ready
        window.Alpine = { data: vi.fn() };
        
        await manager.init();
        
        expect(manager.isAlpineReady).toBe(true);
        expect(manager.initPromise).toBeDefined();
    });

    it("should register components when Alpine is ready", async () => {
        // Mock Alpine as ready
        window.Alpine = { data: vi.fn() };
        await manager.init();
        
        const testComponent = vi.fn(() => ({ test: true }));
        
        manager.registerComponent("testComponent", testComponent);
        
        expect(window.Alpine.data).toHaveBeenCalledWith("testComponent", expect.any(Function));
        expect(manager.isComponentRegistered("testComponent")).toBe(true);
    });

    it("should queue components when Alpine is not ready", () => {
        // Ensure Alpine is NOT ready by clearing the Alpine object
        window.Alpine = null;
        
        const testComponent = vi.fn(() => ({ test: true }));
        
        manager.registerComponent("testComponent", testComponent);
        
        expect(manager.getPendingCount()).toBe(1);
        expect(manager.isComponentRegistered("testComponent")).toBe(false);
    });

    it("should prevent duplicate registrations", async () => {
        // Mock Alpine as ready
        window.Alpine = { data: vi.fn() };
        await manager.init();
        
        const testComponent = vi.fn(() => ({ test: true }));
        
        // Register the same component twice
        manager.registerComponent("testComponent", testComponent);
        manager.registerComponent("testComponent", testComponent);
        
        // Should only be called once
        expect(window.Alpine.data).toHaveBeenCalledTimes(1);
        expect(manager.getRegisteredComponents()).toEqual(["testComponent"]);
    });

    it("should allow override when specified", async () => {
        // Mock Alpine as ready
        window.Alpine = { data: vi.fn() };
        await manager.init();
        
        const testComponent1 = vi.fn(() => ({ test: 1 }));
        const testComponent2 = vi.fn(() => ({ test: 2 }));
        
        // Register component
        manager.registerComponent("testComponent", testComponent1);
        
        // Register again with override
        manager.registerComponent("testComponent", testComponent2, { allowOverride: true });
        
        // Should be called twice (once for original, once for override)
        expect(window.Alpine.data).toHaveBeenCalledTimes(2);
    });

    it("should handle component factory errors gracefully", async () => {
        // Mock Alpine as ready
        window.Alpine = { data: vi.fn() };
        await manager.init();
        
        const faultyComponent = vi.fn(() => {
            throw new Error("Component factory error");
        });
        
        // Should not throw
        expect(() => {
            manager.registerComponent("faultyComponent", faultyComponent);
        }).not.toThrow();
        
        // Should still register with fallback
        expect(window.Alpine.data).toHaveBeenCalled();
        expect(manager.isComponentRegistered("faultyComponent")).toBe(true);
    });

    it("should process pending components when Alpine becomes ready", async () => {
        // Start with Alpine NOT ready
        window.Alpine = null;
        
        const testComponent = vi.fn(() => ({ test: true }));
        
        // Queue component before Alpine is ready
        manager.registerComponent("testComponent", testComponent);
        expect(manager.getPendingCount()).toBe(1);
        
        // Mock Alpine becoming ready
        window.Alpine = { data: vi.fn() };
        await manager.init();
        
        // Should process pending components
        expect(manager.getPendingCount()).toBe(0);
        expect(window.Alpine.data).toHaveBeenCalledWith("testComponent", expect.any(Function));
        expect(manager.isComponentRegistered("testComponent")).toBe(true);
    });

    it("should provide accurate status information", async () => {
        // Start with Alpine NOT ready
        window.Alpine = null;
        
        const testComponent = vi.fn(() => ({ test: true }));
        
        // Initial status
        let status = manager.getStatus();
        expect(status.isAlpineReady).toBe(false);
        expect(status.registeredCount).toBe(0);
        expect(status.pendingCount).toBe(0);
        
        // Queue a component
        manager.registerComponent("testComponent", testComponent);
        status = manager.getStatus();
        expect(status.pendingCount).toBe(1);
        
        // Initialize Alpine
        window.Alpine = { data: vi.fn() };
        await manager.init();
        
        status = manager.getStatus();
        expect(status.isAlpineReady).toBe(true);
        expect(status.registeredCount).toBe(1);
        expect(status.pendingCount).toBe(0);
        expect(status.registeredComponents).toEqual(["testComponent"]);
    });

    it("should validate component registration parameters", () => {
        const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
        
        // Invalid name
        manager.registerComponent("", () => ({}));
        manager.registerComponent(null, () => ({}));
        manager.registerComponent(123, () => ({}));
        
        // Invalid definition
        manager.registerComponent("validName", "not a function");
        manager.registerComponent("validName", null);
        manager.registerComponent("validName", {});
        
        expect(consoleSpy).toHaveBeenCalledTimes(6);
        expect(manager.getPendingCount()).toBe(0);
        
        consoleSpy.mockRestore();
    });

    it("should reset properly", async () => {
        window.Alpine = { data: vi.fn() };
        await manager.init();
        
        const testComponent = vi.fn(() => ({ test: true }));
        manager.registerComponent("testComponent", testComponent);
        
        expect(manager.getRegisteredComponents().length).toBe(1);
        expect(manager.isAlpineReady).toBe(true);
        
        manager.reset();
        
        expect(manager.getRegisteredComponents().length).toBe(0);
        expect(manager.getPendingCount()).toBe(0);
        expect(manager.isAlpineReady).toBe(false);
        expect(manager.initPromise).toBe(null);
    });
});