import js from '@eslint/js';
import compat from 'eslint-plugin-compat';
import jsxA11y from 'eslint-plugin-jsx-a11y';

export default [
  js.configs.recommended,
  {
    files: ['**/*.js', '**/*.mjs', '**/*.jsx'],
    ignores: [
      '**/node_modules/**',
      '**/lib/**',
      '**/libs/**',
      '**/vendor/**',
      '**/dist/**',
      '**/build/**',
      '**/*.min.js',
      '**/bundle*.js',
      '**/webui/js/lib/**',
      '**/webui/js/libs/**',
      '**/webui/js/transformers@*.js',
      '**/webui/js/alpine*.js',
      '**/*.debug.js'  // Debug files with intentional console statements
    ],
    languageOptions: {
      ecmaVersion: 2024,
      sourceType: 'module',
      globals: {
        // Browser globals
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
        prompt: 'readonly',
        URL: 'readonly',
        Response: 'readonly',
        Request: 'readonly',
        Headers: 'readonly',
        AbortController: 'readonly',
        TextDecoder: 'readonly',
        TextEncoder: 'readonly',
        Blob: 'readonly',
        File: 'readonly',
        FileReader: 'readonly',
        Event: 'readonly',
        CustomEvent: 'readonly',
        EventSource: 'readonly',
        
        // Web Worker globals
        self: 'readonly',
        importScripts: 'readonly',
        postMessage: 'readonly',
        onmessage: 'writable',
        onerror: 'writable',
        
        // Framework-specific (Alpine.js, etc.)
        Alpine: 'readonly',
        ace: 'readonly',
        
        // Service Worker
        caches: 'readonly',
        clients: 'readonly',
        registration: 'readonly',
        
        // Node.js/bundler globals
        process: 'readonly',
        Buffer: 'readonly',
        global: 'readonly',
        
        // Additional browser APIs
        AudioContext: 'readonly',
        webkitAudioContext: 'readonly',
        ReadableStream: 'readonly',
        WritableStream: 'readonly',
        TransformStream: 'readonly',
        structuredClone: 'readonly',
        
        // App-specific globals
        settingsModalProxy: 'readonly',
        openModal: 'readonly'
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
      
      // Code quality rules (relaxed for better user experience)
      'no-unused-vars': 'warn',
      'no-undef': 'error',
      'no-console': 'warn',
      'prefer-const': 'warn',
      'no-var': 'warn'
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
        'Array.includes',
        'URL',
        'Response',
        'Request'
      ]
    }
  }
];
