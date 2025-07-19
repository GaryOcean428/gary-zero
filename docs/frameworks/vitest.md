# Vitest Testing Framework

## Overview
Vitest is a fast unit testing framework powered by Vite.

## Key Resources
- [Vitest Guide](https://vitest.dev/guide/) - Getting started with Vitest
- [API Reference](https://vitest.dev/api/) - Testing APIs and utilities
- [Configuration](https://vitest.dev/config/) - Vitest configuration options

## Project Setup
Tests are configured in `vitest.config.js` and located in the `tests/` directory.

## Running Tests
```bash
# Run all tests
npm run test

# Run tests with UI
npm run test:ui

# Run tests with coverage
npm run test:coverage
```

## Writing Tests
```javascript
import { describe, it, expect } from 'vitest'

describe('Component', () => {
  it('should work correctly', () => {
    expect(true).toBe(true)
  })
})
```

## Best Practices
- Keep tests close to source code
- Use descriptive test names
- Mock external dependencies
- Test both happy path and edge cases