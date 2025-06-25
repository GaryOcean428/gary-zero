import js from '@eslint/js';
import jsxA11y from 'eslint-plugin-jsx-a11y';
import compat from 'eslint-plugin-compat';

export default [
  js.configs.recommended,
  {
    files: ['**/*.js', '**/*.mjs', '**/*.jsx'],
    languageOptions: {
      ecmaVersion: 2024,
      sourceType: 'module',
      globals: {
        window: 'readonly',
        document: 'readonly',
        console: 'readonly',
        fetch: 'readonly',
        URLSearchParams: 'readonly',
        FormData: 'readonly',
        localStorage: 'readonly',
        sessionStorage: 'readonly',
        setTimeout: 'readonly',
        setInterval: 'readonly',
        clearTimeout: 'readonly',
        clearInterval: 'readonly',
        WebSocket: 'readonly',
        navigator: 'readonly',
        location: 'readonly',
        history: 'readonly',
        alert: 'readonly',
        confirm: 'readonly',
        prompt: 'readonly'
      }
    },
    plugins: {
      'jsx-a11y': jsxA11y,
      compat: compat
    },
    rules: {
      // Accessibility rules
      'jsx-a11y/alt-text': 'error',
      'jsx-a11y/aria-props': 'error',
      'jsx-a11y/aria-proptypes': 'error',
      'jsx-a11y/aria-unsupported-elements': 'error',
      'jsx-a11y/heading-has-content': 'error',
      'jsx-a11y/html-has-lang': 'error',
      'jsx-a11y/img-redundant-alt': 'error',
      'jsx-a11y/interactive-supports-focus': 'error',
      'jsx-a11y/label-has-associated-control': 'error',
      'jsx-a11y/no-access-key': 'error',
      'jsx-a11y/no-autofocus': 'warn',
      'jsx-a11y/no-distracting-elements': 'error',
      'jsx-a11y/no-redundant-roles': 'error',
      'jsx-a11y/role-has-required-aria-props': 'error',
      'jsx-a11y/role-supports-aria-props': 'error',
      'jsx-a11y/tabindex-no-positive': 'error',
      
      // Browser compatibility rules
      'compat/compat': 'error',
      
      // Security rules
      'no-eval': 'error',
      'no-implied-eval': 'error',
      'no-new-func': 'error',
      'no-script-url': 'error',
      'no-unsafe-finally': 'error',
      'no-unsafe-negation': 'error',
      
      // Code quality rules
      'no-unused-vars': 'error',
      'no-undef': 'error',
      'no-console': 'warn',
      'prefer-const': 'error',
      'no-var': 'error'
    },
    settings: {
      polyfills: [
        'fetch',
        'URLSearchParams',
        'FormData',
        'Promise',
        'Map',
        'Set',
        'Symbol',
        'Object.assign',
        'Array.from',
        'Array.includes'
      ]
    }
  }
];
