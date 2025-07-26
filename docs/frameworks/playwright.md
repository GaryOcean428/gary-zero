# Playwright End-to-End Testing

## Overview

Playwright is a powerful framework for web testing and automation.

## Key Resources

- [Playwright Docs](https://playwright.dev/docs/intro) - Getting started guide
- [API Reference](https://playwright.dev/docs/api/class-playwright) - Complete API documentation
- [Best Practices](https://playwright.dev/docs/best-practices) - Testing best practices

## Installation

```bash
npm install -D @playwright/test
npx playwright install
```

## Basic Test Example

```javascript
import { test, expect } from '@playwright/test';

test('basic test', async ({ page }) => {
  await page.goto('http://localhost:8080');
  await expect(page).toHaveTitle(/Zero/);
});
```

## Running Tests

```bash
# Run all tests
npx playwright test

# Run tests in headed mode
npx playwright test --headed

# Run specific test file
npx playwright test tests/example.spec.js
```

## Configuration

Create `playwright.config.js` for project-specific settings including browsers, timeouts, and test directories.

## Common Patterns

- Page Object Model for maintainable tests
- Use data-testid attributes for reliable selectors
- Handle async operations with proper waits
- Test across multiple browsers and devices
