// Stricter ESLint configuration for QA initiative
module.exports = {
  extends: ["./eslint.config.js"],
  rules: {
    // Console statements - allow in development, warn in production
    "no-console": process.env.NODE_ENV === "production" ? "error" : "warn",
    
    // Unused variables - error to enforce cleanup
    "no-unused-vars": ["error", { 
      "vars": "all", 
      "args": "after-used", 
      "ignoreRestSiblings": false,
      "argsIgnorePattern": "^_"
    }],
    
    // Enforce error handling
    "no-empty": ["error", { "allowEmptyCatch": false }],
    
    // Require proper type checking
    "eqeqeq": ["error", "always"],
    
    // Security rules
    "no-eval": "error",
    "no-implied-eval": "error",
    "no-new-func": "error"
  },
  env: {
    browser: true,
    es2022: true
  }
};
