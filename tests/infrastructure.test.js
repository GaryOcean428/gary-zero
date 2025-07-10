import { describe, it, expect } from 'vitest';

describe('Infrastructure Tests', () => {
  it('should have a working test environment', () => {
    expect(true).toBe(true);
  });

  it('should have access to DOM', () => {
    const div = document.createElement('div');
    div.textContent = 'test';
    expect(div.textContent).toBe('test');
  });

  it('should have fetch available', () => {
    expect(typeof fetch).toBe('function');
  });
});

describe('Environment Configuration Tests', () => {
  it('should validate Node.js version requirement', () => {
    // This test ensures our package.json engines requirement is being checked
    const nodeVersion = process.version;
    const majorVersion = parseInt(nodeVersion.slice(1).split('.')[0]);
    expect(majorVersion).toBeGreaterThanOrEqual(20); // Current environment
  });
});