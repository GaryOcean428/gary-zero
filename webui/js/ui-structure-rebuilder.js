/**
 * UI Structure Rebuilder - Ensures all critical UI elements are properly structured
 * This module rebuilds missing UI elements if they're not found during initialization
 */

class UIStructureRebuilder {
    constructor() {
        this.criticalElements = [
            {
                id: "right-panel",
                tag: "div",
                classes: ["panel"],
                parent: ".container",
            },
            { id: "chat-history", tag: "div", classes: [], parent: "#right-panel" },
            {
                id: "chat-input",
                tag: "textarea",
                classes: [],
                parent: "#input-section",
            },
            {
                id: "send-button",
                tag: "button",
                classes: ["chat-button"],
                parent: "#chat-buttons-wrapper",
            },
            { id: "input-section", tag: "div", classes: [], parent: "#right-panel" },
        ];
    }

    /**
     * Check if all critical elements exist and are properly structured
     */
    validateStructure() {
        const missing = [];

        for (const element of this.criticalElements) {
            const el = document.getElementById(element.id);
            if (!el) {
                missing.push(element);
            } else {
                // Check if element is properly positioned
                const parent = element.parent ? document.querySelector(element.parent) : null;
                if (parent && !parent.contains(el)) {
                    missing.push({ ...element, misplaced: true });
                }
            }
        }

        return missing;
    }

    /**
     * Rebuild missing or misplaced elements
     */
    rebuildMissingElements() {
        const missing = this.validateStructure();

        if (missing.length === 0) {
            return { success: true, rebuilt: [] };
        }

        const rebuilt = [];

        for (const elementDef of missing) {
            try {
                if (elementDef.misplaced) {
                    // Move misplaced element to correct parent
                    const element = document.getElementById(elementDef.id);
                    const parent = document.querySelector(elementDef.parent);
                    if (element && parent) {
                        parent.appendChild(element);
                        rebuilt.push(`Moved ${elementDef.id} to correct parent`);
                    }
                } else {
                    // Create missing element
                    const created = this.createElement(elementDef);
                    if (created) {
                        rebuilt.push(`Created ${elementDef.id}`);
                    }
                }
            } catch {
                // Failed to rebuild element
            }
        }

        return { success: rebuilt.length > 0, rebuilt };
    }

    /**
     * Create a single element based on definition
     */
    createElement(elementDef) {
        const parent = document.querySelector(elementDef.parent);
        if (!parent) {
            return false;
        }

        const element = document.createElement(elementDef.tag);
        element.id = elementDef.id;

        if (elementDef.classes && elementDef.classes.length > 0) {
            element.classList.add(...elementDef.classes);
        }

        // Add specific attributes and content based on element type
        this.configureElement(element, elementDef.id);

        parent.appendChild(element);
        return true;
    }

    /**
     * Configure specific elements with proper attributes and content
     */
    configureElement(element, id) {
        switch (id) {
            case "chat-input":
                element.placeholder = "Type your message here...";
                element.rows = 1;
                element.style.resize = "none";
                break;
            case "send-button":
                element.innerHTML = `
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
            <path d="M25 20 L75 50 L25 80" fill="none" stroke="currentColor" stroke-width="15"></path>
          </svg>
        `;
                element.setAttribute("aria-label", "Send message");
                break;
            case "right-panel":
                element.classList.add("expanded");
                break;
        }
    }

    /**
     * Force visibility on all critical elements
     */
    ensureVisibility() {
        const elements = this.criticalElements.map((def) => document.getElementById(def.id)).filter(Boolean);

        for (const element of elements) {
            // Force display and visibility
            element.style.display = "";
            element.style.visibility = "visible";
            element.style.opacity = "1";

            // Remove any hidden classes
            element.classList.remove("hidden", "d-none");
        }

        // Special handling for right panel
        const rightPanel = document.getElementById("right-panel");
        if (rightPanel) {
            rightPanel.classList.add("expanded");
            rightPanel.style.width = "";
            rightPanel.style.flex = "1";
        }
    }
}

// Export for use in main application
window.UIStructureRebuilder = UIStructureRebuilder;
