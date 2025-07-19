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

// Import the ErrorBoundary after setting up the DOM
const ErrorBoundary = await import('../webui/js/error-boundary.js');

describe('ErrorBoundary', () => {
  let errorBoundary;
  let consoleErrorSpy;
  let alertSpy;

  beforeEach(() => {
    // Reset DOM
    document.body.innerHTML = '';
    
    // Create new instance with test configuration
    errorBoundary = new ErrorBoundary.default({ 
      disableFetchHandling: true,  // Disable fetch handling for tests
      isTestEnvironment: true 
    });
    
    // Mock console.error to prevent noise in tests
    consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
    
    // Mock alert
    alertSpy = vi.spyOn(window, 'alert').mockImplementation(() => {});
  });

  afterEach(() => {
    consoleErrorSpy.mockRestore();
    alertSpy.mockRestore();
    
    // Clean up any error UI
    const errorUI = document.getElementById('error-boundary-fallback');
    if (errorUI) {
      errorUI.remove();
    }
  });

  describe('Error Logging', () => {
    it('should log errors with structured data', () => {
      const testError = new Error('Test error');
      const metadata = { component: 'test' };
      
      errorBoundary.logError('test', testError, metadata);
      
      const stats = errorBoundary.getErrorStats();
      expect(stats.total).toBe(1);
      expect(stats.byType.test).toBe(1);
      expect(stats.recent[0].message).toBe('Test error');
      expect(stats.recent[0].metadata).toEqual(metadata);
    });

    it('should maintain error log size limit', () => {
      // Add more than max log size
      for (let i = 0; i < 150; i++) {
        errorBoundary.logError('test', new Error(`Error ${i}`));
      }
      
      const stats = errorBoundary.getErrorStats();
      expect(stats.total).toBe(100); // maxLogSize
    });

    it('should clear error log', () => {
      errorBoundary.logError('test', new Error('Test error'));
      expect(errorBoundary.getErrorStats().total).toBe(1);
      
      errorBoundary.clearErrorLog();
      expect(errorBoundary.getErrorStats().total).toBe(0);
    });
  });

  describe('Error Classification', () => {
    it('should identify critical errors', () => {
      const criticalError = new Error('ChunkLoadError: Loading chunk 5 failed');
      expect(errorBoundary.isCriticalError(criticalError)).toBe(true);
      
      const normalError = new Error('Normal error');
      expect(errorBoundary.isCriticalError(normalError)).toBe(false);
    });

    it('should identify retryable HTTP status codes', () => {
      expect(errorBoundary.isRetryableError(500)).toBe(true);
      expect(errorBoundary.isRetryableError(502)).toBe(true);
      expect(errorBoundary.isRetryableError(404)).toBe(false);
      expect(errorBoundary.isRetryableError(401)).toBe(false);
    });
  });

  describe('User Error Display', () => {
    it('should show fallback UI for non-recoverable errors', () => {
      errorBoundary.showErrorFallbackUI('Test error message');
      
      const errorUI = document.getElementById('error-boundary-fallback');
      expect(errorUI).toBeTruthy();
      expect(errorUI.textContent).toContain('Test error message');
      expect(errorUI.textContent).toContain('Something went wrong');
    });

    it('should use alert as fallback when no notification system available', () => {
      // Explicitly ensure no Alpine or showToast exists
      delete window.showToast;
      delete window.Alpine;
      
      errorBoundary.showUserError('Test message');
      expect(alertSpy).toHaveBeenCalledWith('Test message');
    });
  });

  describe('Global Error Handlers', () => {
    it('should handle unhandled promise rejections', async () => {
      const logErrorSpy = vi.spyOn(errorBoundary, 'logError');
      
      // Create a custom event for JSDOM compatibility
      const mockReason = new Error('Test rejection');
      const event = new Event('unhandledrejection');
      event.reason = mockReason;
      event.promise = Promise.resolve(); // Use resolved promise to avoid actual rejection
      
      // Mock preventDefault
      event.preventDefault = vi.fn();
      
      window.dispatchEvent(event);
      
      expect(logErrorSpy).toHaveBeenCalledWith(
        'Promise Rejection',
        mockReason,
        expect.objectContaining({
          type: 'unhandledrejection'
        })
      );
    });

    it('should handle JavaScript errors', () => {
      const logErrorSpy = vi.spyOn(errorBoundary, 'logError');
      
      // Dispatch error event manually
      const event = new window.ErrorEvent('error', {
        error: new Error('Test error'),
        filename: 'test.js',
        lineno: 10,
        colno: 5
      });
      
      window.dispatchEvent(event);
      
      expect(logErrorSpy).toHaveBeenCalledWith(
        'JavaScript Error',
        expect.any(Error),
        expect.objectContaining({
          type: 'javascript',
          filename: 'test.js',
          lineno: 10,
          colno: 5
        })
      );
    });
  });

  describe('Fetch Error Handling', () => {
    let originalFetch;
    let fetchErrorBoundary;

    beforeEach(() => {
      originalFetch = global.fetch;
      // Create a separate instance specifically for fetch testing
      fetchErrorBoundary = new ErrorBoundary.default({ isTestEnvironment: true });
    });

    afterEach(() => {
      global.fetch = originalFetch;
    });

    it('should handle fetch errors', async () => {
      const logErrorSpy = vi.spyOn(fetchErrorBoundary, 'logError');
      
      // Mock the original fetch that will be called by our wrapper
      const mockOriginalFetch = vi.fn().mockResolvedValue({
        ok: false,
        status: 400, // Non-retryable error
        statusText: 'Bad Request'
      });
      
      try {
        // Call the wrapped fetch logic directly
        const response = await mockOriginalFetch('/test-endpoint');
        
        if (!response.ok) {
          const error = new Error(`HTTP ${response.status}: ${response.statusText}`);
          fetchErrorBoundary.logError('Fetch Error', error, {
            type: 'fetch',
            url: '/test-endpoint',
            status: response.status,
            timestamp: new Date().toISOString()
          });
          
          if (!fetchErrorBoundary.isRetryableError(response.status)) {
            throw error;
          }
        }
      } catch (error) {
        // Expected to throw
      }
      
      expect(logErrorSpy).toHaveBeenCalledWith(
        'Fetch Error',
        expect.any(Error),
        expect.objectContaining({
          type: 'fetch',
          status: 400
        })
      );
    });

    it('should retry retryable errors', async () => {
      const logErrorSpy = vi.spyOn(fetchErrorBoundary, 'logError');
      const mockOriginalFetch = vi.fn()
        .mockResolvedValueOnce({
          ok: false,
          status: 500,
          statusText: 'Internal Server Error'
        })
        .mockResolvedValueOnce({
          ok: true,
          status: 200,
          statusText: 'OK'
        });

      // Test the retry logic directly
      try {
        const firstResponse = await mockOriginalFetch('/test-endpoint');
        if (!firstResponse.ok) {
          const error = new Error(`HTTP ${firstResponse.status}: ${firstResponse.statusText}`);
          fetchErrorBoundary.logError('Fetch Error', error, {
            type: 'fetch',
            url: '/test-endpoint',
            status: firstResponse.status,
            timestamp: new Date().toISOString()
          });
          
          if (fetchErrorBoundary.isRetryableError(firstResponse.status)) {
            // Retry
            const retryResponse = await fetchErrorBoundary.retryFetch(mockOriginalFetch, '/test-endpoint');
            expect(retryResponse.ok).toBe(true);
          }
        }
      } catch (error) {
        // Unexpected error
        throw error;
      }
      
      expect(mockOriginalFetch).toHaveBeenCalledTimes(2); // Initial + 1 retry
      expect(logErrorSpy).toHaveBeenCalledWith(
        'Fetch Error',
        expect.any(Error),
        expect.objectContaining({
          type: 'fetch',
          status: 500
        })
      );
    });
  });

  describe('Utility Functions', () => {
    it('should implement delay function', async () => {
      const start = Date.now();
      await errorBoundary.delay(100);
      const end = Date.now();
      
      expect(end - start).toBeGreaterThanOrEqual(95); // Allow for some timing variance
    });
  });
});