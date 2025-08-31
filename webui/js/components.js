// Import enhanced logger
import { logger } from './console-logger.js';

// Import a component into a target element
// Import a component and recursively load its nested components
// Returns the parsed document for additional processing

// cache object to store loaded components
const componentCache = {};

// Fallback components for critical functionality
const fallbackComponents = {
    'settings/mcp/client/mcp-servers.html': () => `
        <div class="fallback-component">
            <h3>MCP Servers Configuration</h3>
            <p>Loading configuration interface...</p>
            <div class="error-message">Component temporarily unavailable. Please refresh the page.</div>
        </div>
    `,
    'settings/scheduler/scheduler.html': () => `
        <div class="fallback-component">
            <h3>Task Scheduler</h3>
            <p>Scheduler interface loading...</p>
            <div class="error-message">Component temporarily unavailable. Please refresh the page.</div>
        </div>
    `,
    'settings/tunnel/tunnel.html': () => `
        <div class="fallback-component">
            <h3>Tunnel Configuration</h3>
            <p>Tunnel settings loading...</p>
            <div class="error-message">Component temporarily unavailable. Please refresh the page.</div>
        </div>
    `
};

// Get fallback component content
function getFallbackComponent(path) {
    if (fallbackComponents[path]) {
        return fallbackComponents[path]();
    }
    
    // Generic fallback
    return `
        <div class="fallback-component">
            <h3>Component Loading</h3>
            <p>Loading ${path}...</p>
            <div class="error-message">Component temporarily unavailable. Please try refreshing the page.</div>
            <button onclick="location.reload()" class="btn btn-primary" style="margin-top: 10px;">Refresh Page</button>
        </div>
    `;
}

// Retry mechanism with exponential backoff
async function retryOperation(operation, maxRetries = 3, baseDelay = 1000) {
    let lastError = null;
    
    for (let attempt = 0; attempt < maxRetries; attempt++) {
        try {
            return await operation();
        } catch (error) {
            lastError = error;
            
            if (attempt < maxRetries - 1) {
                const delay = baseDelay * Math.pow(2, attempt);
                logger.warn(`Retry attempt ${attempt + 1} failed, retrying in ${delay}ms:`, error.message);
                await new Promise(resolve => setTimeout(resolve, delay));
            }
        }
    }
    
    throw lastError;
}

export async function importComponent(path, targetElement) {
    try {
        if (!targetElement) {
            logger.warn("Target element is required for component import");
            return null;
        }

        // Show loading indicator
        targetElement.innerHTML = '<div class="loading"></div>';

        // full component url
        const componentUrl = "components/" + path;

        // get html from cache or fetch it with retry mechanism
        let html;
        if (componentCache[componentUrl]) {
            html = componentCache[componentUrl];
        } else {
            try {
                html = await retryOperation(async () => {
                    const response = await fetch(componentUrl);
                    if (!response.ok) {
                        throw new Error(`Error loading component ${path}: ${response.statusText}`);
                    }
                    return await response.text();
                }, 2, 500); // 2 retries with 500ms base delay
                
                // store in cache only if successful
                componentCache[componentUrl] = html;
            } catch (fetchError) {
                logger.warn(`Failed to load component ${path}, using fallback:`, fetchError);
                
                // Show toast notification if available
                if (window.toast) {
                    window.toast.warning(`Component ${path} failed to load, using fallback`, 5000);
                }
                
                // Use fallback component
                html = getFallbackComponent(path);
                targetElement.innerHTML = html;
                return null; // Return early with fallback
            }
        }
        const parser = new DOMParser();
        const doc = parser.parseFromString(html, "text/html");

        const allNodes = [...doc.querySelectorAll("style"), ...doc.querySelectorAll("script"), ...doc.body.childNodes];

        const loadPromises = [];
        let blobCounter = 0;

        for (const node of allNodes) {
            if (node.nodeName === "SCRIPT") {
                const isModule = node.type === "module" || node.getAttribute("type") === "module";

                if (isModule) {
                    if (node.src) {
                        // For <script type="module" src="..." use dynamic import with retry
                        const resolvedUrl = new URL(node.src, globalThis.location.origin).toString();

                        // Check if module is already in cache
                        if (!componentCache[resolvedUrl]) {
                            try {
                                const modulePromise = retryOperation(
                                    () => import(resolvedUrl),
                                    2, // 2 retries
                                    1000 // 1 second base delay
                                );
                                componentCache[resolvedUrl] = modulePromise;
                                loadPromises.push(modulePromise);
                            } catch (moduleError) {
                                logger.warn(`Failed to load external module ${resolvedUrl}:`, moduleError);
                                // Don't add to loadPromises, continue without this module
                            }
                        }
                    } else {
                        const virtualUrl = `${componentUrl.replaceAll("/", "_")}.${++blobCounter}.js`;

                        // For inline module scripts, use cache or create blob with enhanced error handling
                        if (!componentCache[virtualUrl]) {
                            try {
                                // Transform relative import paths to absolute URLs
                                let content = node.textContent.replace(
                                    /import\s+([^'"]+)\s+from\s+["']([^"']+)["']/g,
                                    (match, bindings, importPath) => {
                                        // Convert relative OR root-based (e.g. /src/...) to absolute URLs
                                        if (!/^https?:\/\//.test(importPath)) {
                                            const absoluteUrl = new URL(importPath, globalThis.location.origin).href;
                                            return `import ${bindings} from "${absoluteUrl}"`;
                                        }
                                        return match;
                                    }
                                );

                                // Add sourceURL to the content
                                content += `\n//# sourceURL=${virtualUrl}`;

                                // Create a Blob from the rewritten content
                                const blob = new Blob([content], {
                                    type: "text/javascript",
                                });
                                const blobUrl = URL.createObjectURL(blob);

                                const modulePromise = retryOperation(
                                    () => import(blobUrl),
                                    2, // 2 retries for blob imports
                                    500 // 500ms base delay
                                )
                                .catch((err) => {
                                    logger.warn(`Failed to load inline module for ${path}:`, err.message);
                                    
                                    // Show toast notification if available
                                    if (window.toast) {
                                        window.toast.warning(`Inline script in ${path} failed to load`, 3000);
                                    }
                                    
                                    throw err;
                                })
                                .finally(() => {
                                    // Always clean up blob URL
                                    URL.revokeObjectURL(blobUrl);
                                });

                                componentCache[virtualUrl] = modulePromise;
                                loadPromises.push(modulePromise);
                            } catch (blobError) {
                                logger.warn(`Failed to create blob module for ${path}:`, blobError);
                                // Continue without this inline script
                            }
                        }
                    }
                } else {
                    // Non-module script
                    const script = document.createElement("script");
                    Array.from(node.attributes || []).forEach((attr) => {
                        script.setAttribute(attr.name, attr.value);
                    });
                    script.textContent = node.textContent;

                    if (script.src) {
                        const promise = new Promise((resolve, reject) => {
                            script.onload = resolve;
                            script.onerror = reject;
                        });
                        loadPromises.push(promise);
                    }

                    targetElement.appendChild(script);
                }
            } else if (node.nodeName === "STYLE" || (node.nodeName === "LINK" && node.rel === "stylesheet")) {
                const clone = node.cloneNode(true);

                if (clone.tagName === "LINK" && clone.rel === "stylesheet") {
                    const promise = new Promise((resolve, reject) => {
                        clone.onload = resolve;
                        clone.onerror = reject;
                    });
                    loadPromises.push(promise);
                }

                targetElement.appendChild(clone);
            } else {
                const clone = node.cloneNode(true);
                targetElement.appendChild(clone);
            }
        }

        // Wait for all tracked external scripts/styles to finish loading with enhanced error handling
        try {
            await Promise.allSettled(loadPromises).then(results => {
                const failures = results.filter(result => result.status === 'rejected');
                if (failures.length > 0) {
                    logger.warn(`${failures.length} module(s) failed to load for component ${path}:`, 
                        failures.map(f => f.reason?.message || f.reason));
                    
                    // Show toast notification for multiple failures
                    if (failures.length > 1 && window.toast) {
                        window.toast.warning(`${failures.length} scripts failed to load in ${path}`, 4000);
                    }
                }
            });
        } catch (promiseError) {
            logger.warn(`Error waiting for module promises in ${path}:`, promiseError);
        }

        // Remove loading indicator
        const loadingEl = targetElement.querySelector(".loading");
        if (loadingEl) {
            targetElement.removeChild(loadingEl);
        }

        // // Load any nested components
        // await loadComponents([targetElement]);

        // Return parsed document
        return doc;
    } catch (error) {
        logger.error("Error importing component:", error);
        
        // Show fallback content on any critical error
        if (targetElement) {
            const fallbackHtml = getFallbackComponent(path);
            targetElement.innerHTML = fallbackHtml;
            
            // Show toast notification if available
            if (window.toast) {
                window.toast.error(`Component ${path} failed to load: ${error.message}`, 8000);
            }
        }
        
        // Don't re-throw the error, return null to indicate fallback was used
        return null;
    }
}

// Load all x-component tags starting from root elements
export async function loadComponents(roots = [document.documentElement]) {
    try {
        // Convert single root to array if needed
        const rootElements = Array.isArray(roots) ? roots : [roots];

        // Find all top-level components and load them in parallel
        const components = rootElements.flatMap((root) => Array.from(root.querySelectorAll("x-component")));

        if (components.length === 0) return;

        // Use Promise.allSettled to handle individual component failures gracefully
        const results = await Promise.allSettled(
            components.map(async (component) => {
                const path = component.getAttribute("path");
                if (!path) {
                    logger.error("x-component missing path attribute:", component);
                    return Promise.reject(new Error("Missing path attribute"));
                }
                return await importComponent(path, component);
            })
        );

        // Log any failures but don't throw
        const failures = results.filter(result => result.status === 'rejected');
        if (failures.length > 0) {
            logger.warn(`${failures.length} component(s) failed to load:`, 
                failures.map(f => f.reason?.message || f.reason));
            
            // Show consolidated toast notification if available
            if (window.toast) {
                window.toast.warning(`${failures.length} component(s) failed to load, using fallbacks`, 5000);
            }
        }
        
        return results;
    } catch (error) {
        logger.error("Error loading components:", error);
        
        // Show toast notification if available
        if (window.toast) {
            window.toast.error("Failed to load page components, some features may not work correctly", 8000);
        }
        
        // Don't throw, allow page to continue functioning
        return [];
    }
}

// Function to traverse parents and collect x-component attributes
export function getParentAttributes(el) {
    let element = el;
    const attrs = {};

    while (element) {
        if (element.tagName.toLowerCase() === "x-component") {
            // Get all attributes
            for (const attr of element.attributes) {
                try {
                    // Try to parse as JSON first
                    attrs[attr.name] = JSON.parse(attr.value);
                } catch (_e) {
                    // If not JSON, use raw value
                    attrs[attr.name] = attr.value;
                }
            }
        }
        element = element.parentElement;
    }
    return attrs;
}
// expose as global for x-components in Alpine
globalThis.xAttrs = getParentAttributes;

// Initialize when DOM is ready
if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", () => loadComponents());
} else {
    loadComponents();
}

// Watch for DOM changes to dynamically load x-components
const observer = new MutationObserver((mutations) => {
    for (const mutation of mutations) {
        for (const node of mutation.addedNodes) {
            if (node.nodeType === 1) {
                // ELEMENT_NODE
                // Check if this node or its descendants contain x-component(s)
                if (node.matches?.("x-component")) {
                    const path = node.getAttribute("path");
                    if (path) {
                        importComponent(path, node).catch(error => {
                            logger.warn(`Failed to dynamically load component ${path}:`, error);
                        });
                    }
                } else if (node.querySelectorAll) {
                    loadComponents([node]).catch(error => {
                        logger.warn("Failed to load nested components:", error);
                    });
                }
            }
        }
    }
});
observer.observe(document.body, { childList: true, subtree: true });
