// Global test setup
import { afterEach, beforeEach } from "vitest";

// Mock global objects that might be needed in tests
global.fetch = global.fetch || (() => Promise.resolve({ ok: true, json: () => Promise.resolve({}) }));

// Clean up after each test
afterEach(() => {
    // Clear any mocks or reset state as needed
    document.body.innerHTML = "";
});

// Setup DOM environment
beforeEach(() => {
    // Reset DOM state before each test
    document.head.innerHTML = "";
    document.body.innerHTML = "";
});
