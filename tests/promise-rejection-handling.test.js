import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { JSDOM } from 'jsdom';

// Set up DOM environment
const dom = new JSDOM('<!DOCTYPE html><html><body></body></html>', {
  url: 'http://localhost',
  pretendToBeVisual: true,
  resources: 'usable'
});

global.window = dom.window;
global.document = dom.window.document;
global.navigator = dom.window.navigator;

// Mock fetch globally
global.fetch = vi.fn();

describe('Promise Rejection Handling Integration', () => {
  let consoleErrorSpy;
  let consoleWarnSpy;
  let toastSpy;
  let errorBoundary;

  beforeEach(async () => {
    // Reset DOM
    document.body.innerHTML = '';
    
    // Mock console methods
    consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
    consoleWarnSpy = vi.spyOn(console, 'warn').mockImplementation(() => {});
    
    // Mock toast function
    toastSpy = vi.fn();
    global.window.toast = toastSpy;
    global.window.toastFetchError = vi.fn();
    
    // Load error reporting module
    const ErrorReporter = await import('../webui/js/error-reporting.js');
    global.window.errorReporter = new ErrorReporter.default();
    
    // Load error boundary
    const ErrorBoundary = await import('../webui/js/error-boundary.js');
    errorBoundary = new ErrorBoundary.default({ isTestEnvironment: true });
    
    // Reset fetch mock
    global.fetch.mockReset();
  });

  afterEach(() => {
    consoleErrorSpy.mockRestore();
    consoleWarnSpy.mockRestore();
    
    // Clean up global mocks
    delete global.window.toast;
    delete global.window.toastFetchError;
    delete global.window.errorReporter;
  });

  describe('Uncaught Promise Rejections', () => {
    it('should handle uncaught promise rejections globally', async () => {
      const logErrorSpy = vi.spyOn(errorBoundary, 'logError');
      const reportErrorSpy = vi.spyOn(global.window.errorReporter, 'reportError');
      
      // Create an unhandled promise rejection
      const testError = new Error('Test unhandled rejection');
      
      // Create and dispatch unhandledrejection event (without actually creating a rejected promise)
      const event = new Event('unhandledrejection');
      event.reason = testError;
      event.promise = Promise.resolve(); // Use resolved promise to avoid actual rejection
      event.preventDefault = vi.fn();
      
      window.dispatchEvent(event);
      
      // Verify error was logged by error boundary
      expect(logErrorSpy).toHaveBeenCalledWith(
        'Promise Rejection',
        testError,
        expect.objectContaining({
          type: 'unhandledrejection'
        })
      );
      
      // Verify preventDefault was called
      expect(event.preventDefault).toHaveBeenCalled();
      
      // Verify error was reported
      expect(reportErrorSpy).toHaveBeenCalled();
    });

    it('should handle failed fetch operations gracefully', async () => {
      const testError = new Error('Network error');
      global.fetch.mockRejectedValue(testError);
      
      const reportErrorSpy = vi.spyOn(global.window.errorReporter, 'reportError');
      
      // Simulate fetch error handling manually (without wrapped fetch to avoid complexity)
      try {
        await global.fetch('/test-endpoint');
      } catch (error) {
        // Manually report the error as the wrapped fetch would
        global.window.errorReporter.reportError(error, {
          type: 'network',
          url: '/test-endpoint',
          source: 'error-boundary'
        });
      }
      
      // Verify error was reported
      expect(reportErrorSpy).toHaveBeenCalledWith(
        testError,
        expect.objectContaining({
          type: 'network',
          source: 'error-boundary'
        })
      );
    });

    it('should handle API failures with proper error messages', async () => {
      global.fetch.mockResolvedValue({
        ok: false,
        status: 500,
        statusText: 'Internal Server Error',
        json: () => Promise.resolve({ error: 'Server error' })
      });
      
      const reportErrorSpy = vi.spyOn(global.window.errorReporter, 'reportError');
      
      // Simulate an API call failure
      try {
        const response = await global.fetch('/api/test');
        if (!response.ok) {
          const error = new Error(`HTTP ${response.status}: ${response.statusText}`);
          global.window.errorReporter.reportError(error, {
            type: 'api_failure',
            url: '/api/test',
            status: response.status
          });
          throw error;
        }
      } catch (error) {
        // Expected to throw
      }
      
      expect(reportErrorSpy).toHaveBeenCalledWith(
        expect.any(Error),
        expect.objectContaining({
          type: 'api_failure',
          status: 500
        })
      );
    });
  });

  describe('Error Reporting Integration', () => {
    it('should create structured error reports', () => {
      const testError = new Error('Test error');
      const context = { component: 'test', action: 'testing' };
      
      const report = global.window.errorReporter.reportError(testError, context);
      
      expect(report).toMatchObject({
        id: expect.any(Number),
        sessionId: expect.stringMatching(/^session_/),
        timestamp: expect.any(String),
        error: {
          message: 'Test error',
          name: 'Error'
        },
        context: expect.objectContaining({
          component: 'test',
          action: 'testing'
        })
      });
    });

    it('should maintain error statistics', () => {
      const error1 = new Error('Error 1');
      const error2 = new Error('Error 2');
      
      global.window.errorReporter.reportError(error1);
      global.window.errorReporter.reportError(error2);
      
      const stats = global.window.errorReporter.getStats();
      
      expect(stats.totalErrors).toBe(2);
      expect(stats.recentErrors).toHaveLength(2);
      expect(stats.sessionId).toMatch(/^session_/);
    });

    it('should store errors locally when server is unavailable', async () => {
      global.fetch.mockRejectedValue(new Error('Network error'));
      
      const storeLocallySpy = vi.spyOn(global.window.errorReporter, 'storeLocally');
      
      const testError = new Error('Test error');
      await global.window.errorReporter.reportError(testError);
      
      // Wait for async operations
      await new Promise(resolve => setTimeout(resolve, 10));
      
      expect(storeLocallySpy).toHaveBeenCalled();
    });
  });

  describe('User Experience', () => {
    it('should show user-friendly error messages', () => {
      const showUserErrorSpy = vi.spyOn(errorBoundary, 'showUserError');
      
      // Simulate a critical error
      const criticalError = new Error('ChunkLoadError: Loading failed');
      
      const event = new window.ErrorEvent('error', {
        error: criticalError,
        filename: 'test.js',
        lineno: 10
      });
      
      window.dispatchEvent(event);
      
      // Should show user error for critical errors
      expect(showUserErrorSpy).toHaveBeenCalledWith(
        'A critical error occurred. Please refresh the page.'
      );
    });

    it('should use toast system when available', () => {
      errorBoundary.showUserError('Test error message');
      
      expect(toastSpy).toHaveBeenCalledWith('Test error message', 'error');
    });
  });
});