import * as _modals from "./modals.js";
import * as _components from "./components.js";

// Import Alpine.js directly
import "./alpine.min.js";

// Wait for Alpine to be available
if (typeof Alpine !== 'undefined') {
    // add x-destroy directive
    Alpine.directive(
      "destroy",
      (el, { expression }, { evaluateLater, cleanup }) => {
        const onDestroy = evaluateLater(expression);
        cleanup(() => onDestroy());
      }
    );
} else {
    console.error('Alpine.js not loaded properly');
}
