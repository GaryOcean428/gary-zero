import * as _modals from "./modals.js";
import * as _components from "./components.js";

// Import Alpine.js directly
import "./alpine.min.js";

// Add Alpine.js Collapse plugin support
if (typeof Alpine !== 'undefined') {
    // Register x-collapse directive manually since the plugin isn't loaded
    Alpine.directive('collapse', (el, { value, modifiers }, { effect, evaluate }) => {
        let initialUpdate = true;
        
        const closedStyles = {
            height: '0px',
            overflow: 'hidden',
            paddingTop: '0px',
            paddingBottom: '0px',
            marginTop: '0px',
            marginBottom: '0px',
        };
        
        let openStyles = {};
        
        effect(() => {
            let isOpen = evaluate(value);
            
            if (initialUpdate) {
                if (isOpen) {
                    // Store initial open styles
                    openStyles = {
                        height: el.style.height || '',
                        overflow: el.style.overflow || '',
                        paddingTop: el.style.paddingTop || '',
                        paddingBottom: el.style.paddingBottom || '',
                        marginTop: el.style.marginTop || '',
                        marginBottom: el.style.marginBottom || '',
                    };
                } else {
                    // Apply closed styles immediately on initial load if closed
                    Object.assign(el.style, closedStyles);
                }
                initialUpdate = false;
                return;
            }
            
            if (isOpen) {
                // Opening animation
                Object.assign(el.style, openStyles);
                el.style.transition = 'all 0.3s ease-in-out';
            } else {
                // Closing animation
                el.style.transition = 'all 0.3s ease-in-out';
                Object.assign(el.style, closedStyles);
            }
        });
    });
    
    console.log('✅ Alpine.js Collapse directive registered');
}

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
