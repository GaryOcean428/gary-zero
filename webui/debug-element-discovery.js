// Comprehensive Element Discovery Debugging Tool
// This will reveal WHY elements aren't being found

window.debugElementDiscovery = function() {
    console.log('🔍 COMPREHENSIVE ELEMENT DISCOVERY ANALYSIS');
    console.log('═══════════════════════════════════════════');
    
    // 1. Basic DOM State
    console.log('📊 DOM READINESS:');
    console.log('- Document ready state:', document.readyState);
    console.log('- Alpine.js available:', typeof Alpine !== 'undefined');
    console.log('- Alpine version:', typeof Alpine !== 'undefined' ? Alpine.version : 'N/A');
    
    // 2. Alpine.js State Analysis
    console.log('\n🎯 ALPINE.JS COMPONENT STATE:');
    const alpineElements = document.querySelectorAll('[x-data]');
    console.log('- Elements with x-data:', alpineElements.length);
    alpineElements.forEach((el, i) => {
        const xData = el.getAttribute('x-data');
        const alpineData = el._x_dataStack ? el._x_dataStack[0] : 'Not initialized';
        console.log(`  [${i}] ${el.tagName}#${el.id || 'no-id'} - x-data: ${xData}`);
        console.log(`      Alpine data:`, alpineData);
    });
    
    // 3. Target Element Analysis
    console.log('\n🎯 TARGET ELEMENT DISCOVERY:');
    const targetElements = [
        'right-panel', 'chat-input', 'send-button', 
        'chat-history', 'input-section', 'progress-bar'
    ];
    
    targetElements.forEach(id => {
        const element = document.getElementById(id);
        console.log(`\n📍 ${id}:`);
        
        if (element) {
            const styles = window.getComputedStyle(element);
            console.log('  ✅ EXISTS');
            console.log('  - Display:', styles.display);
            console.log('  - Visibility:', styles.visibility);
            console.log('  - Opacity:', styles.opacity);
            console.log('  - Position:', styles.position);
            console.log('  - Z-index:', styles.zIndex);
            console.log('  - Dimensions:', `${element.offsetWidth}x${element.offsetHeight}`);
            console.log('  - Parent:', element.parentElement?.tagName + '#' + (element.parentElement?.id || 'no-id'));
            
            // Check for Alpine.js directives
            const xShow = element.getAttribute('x-show');
            const xIf = element.getAttribute('x-if');
            if (xShow) console.log('  - x-show:', xShow);
            if (xIf) console.log('  - x-if:', xIf);
            
        } else {
            console.log('  ❌ NOT FOUND');
            
            // Try alternative selectors
            const altSelectors = [
                `[id="${id}"]`,
                `[data-element="${id}"]`,
                `[data-id="${id}"]`,
                `.${id}`,
                `#${id.replace('-', '_')}`,
                `#${id.replace('-', '')}`
            ];
            
            altSelectors.forEach(selector => {
                const altElement = document.querySelector(selector);
                if (altElement) {
                    console.log(`  🔄 FOUND WITH ALTERNATIVE: ${selector}`);
                }
            });
        }
    });
    
    // 4. Content-Based Discovery
    console.log('\n🔍 CONTENT-BASED DISCOVERY:');
    const contentSearches = [
        { name: 'Chat Input', query: 'textarea[placeholder*="message"], input[placeholder*="message"]' },
        { name: 'Send Button', query: 'button[aria-label*="Send"], button[title*="Send"], button:has(svg path[d*="M25 20"])' },
        { name: 'Chat History', query: '.chat-history, .messages, .conversation, #messages' },
        { name: 'Right Panel', query: '.right-panel, .main-panel, main, .chat-panel' }
    ];
    
    contentSearches.forEach(search => {
        const elements = document.querySelectorAll(search.query);
        console.log(`${search.name}: Found ${elements.length} matches`);
        elements.forEach((el, i) => {
            console.log(`  [${i}] ${el.tagName}#${el.id || 'no-id'}.${el.className || 'no-class'}`);
        });
    });
    
    // 5. All IDs in Document
    console.log('\n📋 ALL ELEMENTS WITH IDs:');
    const allIds = Array.from(document.querySelectorAll('[id]')).map(el => el.id);
    console.log('Total elements with IDs:', allIds.length);
    console.log('IDs:', allIds.sort());
    
    // 6. DOM Tree Analysis
    console.log('\n🌳 DOM TREE ANALYSIS:');
    const container = document.querySelector('.container');
    if (container) {
        console.log('Container structure:');
        const analyzeElement = (el, depth = 0) => {
            const indent = '  '.repeat(depth);
            const className = el.className && typeof el.className === 'string' ? '.' + el.className.split(' ').join('.') : '';
            const info = `${el.tagName}${el.id ? '#' + el.id : ''}${className}`;
            console.log(`${indent}${info}`);
            if (depth < 3) { // Limit depth to avoid spam
                Array.from(el.children).forEach(child => analyzeElement(child, depth + 1));
            }
        };
        analyzeElement(container);
    }
    
    return {
        alpineElements: alpineElements.length,
        foundElements: targetElements.filter(id => document.getElementById(id)).length,
        totalElements: targetElements.length,
        allIds: allIds
    };
};

// State-Aware Element Discovery System
window.stateAwareElementDiscovery = function() {
    console.log('🚀 STATE-AWARE ELEMENT DISCOVERY');
    console.log('═══════════════════════════════════════');
    
    const results = {
        found: {},
        strategies: {},
        triggers: []
    };
    
    const targetElements = [
        'right-panel', 'chat-input', 'send-button', 
        'chat-history', 'input-section', 'progress-bar'
    ];
    
    // Strategy 1: Force Alpine.js Re-evaluation
    console.log('\n📊 Strategy 1: Alpine.js State Manipulation');
    if (typeof Alpine !== 'undefined') {
        try {
            // Force Alpine to re-scan the DOM
            Alpine.initTree(document.body);
            console.log('✅ Triggered Alpine.js re-initialization');
            results.triggers.push('alpine-reinit');
        } catch (e) {
            console.log('❌ Alpine re-init failed:', e.message);
        }
    }
    
    // Strategy 2: CSS Override Forcing
    console.log('\n🎨 Strategy 2: CSS Override Forcing');
    const forceVisibleCSS = `
        #right-panel, #chat-input, #send-button, #chat-history, #input-section {
            display: block !important;
            visibility: visible !important;
            opacity: 1 !important;
        }
    `;
    
    const styleElement = document.createElement('style');
    styleElement.textContent = forceVisibleCSS;
    document.head.appendChild(styleElement);
    console.log('✅ Applied force-visible CSS');
    results.triggers.push('css-override');
    
    // Strategy 3: Dynamic Content Triggering
    console.log('\n⚡ Strategy 3: Dynamic Content Triggering');
    
    // Simulate authentication/initialization
    const authEvents = ['DOMContentLoaded', 'alpine:init', 'alpine:initialized'];
    authEvents.forEach(eventName => {
        document.dispatchEvent(new Event(eventName));
        console.log(`✅ Dispatched ${eventName} event`);
    });
    results.triggers.push('auth-events');
    
    // Strategy 4: Wait and Re-check
    console.log('\n⏱️ Strategy 4: State-Change Detection');
    
    return new Promise((resolve) => {
        let attempts = 0;
        const maxAttempts = 10;
        
        const checkElements = () => {
            attempts++;
            console.log(`\n🔍 Check attempt ${attempts}:`);
            
            let foundCount = 0;
            targetElements.forEach(id => {
                const element = document.getElementById(id);
                results.found[id] = !!element;
                
                if (element) {
                    foundCount++;
                    console.log(`  ✅ ${id}: FOUND`);
                    
                    // Analyze why it's now visible
                    const styles = window.getComputedStyle(element);
                    results.strategies[id] = {
                        display: styles.display,
                        visibility: styles.visibility,
                        opacity: styles.opacity,
                        found_on_attempt: attempts
                    };
                } else {
                    console.log(`  ❌ ${id}: Still missing`);
                }
            });
            
            console.log(`📊 Found ${foundCount}/${targetElements.length} elements`);
            
            if (foundCount === targetElements.length || attempts >= maxAttempts) {
                console.log('\n🎯 DISCOVERY COMPLETE');
                console.log('Results:', results);
                
                // Clean up force CSS
                styleElement.remove();
                
                resolve(results);
            } else {
                setTimeout(checkElements, 100);
            }
        };
        
        // Start checking immediately, then every 100ms
        setTimeout(checkElements, 50);
    });
};

// Quick Fix Implementation
window.implementQuickFix = function(discoveryResults) {
    console.log('🔧 IMPLEMENTING QUICK FIX');
    console.log('═══════════════════════════');
    
    const fixes = [];
    
    // Fix 1: Create missing elements if they don't exist but should
    Object.entries(discoveryResults.found).forEach(([id, found]) => {
        if (!found) {
            console.log(`🏗️ Creating fallback element: ${id}`);
            
            let element;
            const container = document.getElementById('right-panel') || document.querySelector('.container');
            
            switch (id) {
                case 'right-panel':
                    element = document.createElement('div');
                    element.id = 'right-panel';
                    element.className = 'panel';
                    document.querySelector('.container')?.appendChild(element);
                    break;
                    
                case 'chat-history':
                    element = document.createElement('div');
                    element.id = 'chat-history';
                    element.className = 'chat-history';
                    container?.appendChild(element);
                    break;
                    
                case 'chat-input':
                    element = document.createElement('textarea');
                    element.id = 'chat-input';
                    element.placeholder = 'Type your message here...';
                    element.rows = 1;
                    container?.appendChild(element);
                    break;
                    
                case 'send-button':
                    element = document.createElement('button');
                    element.id = 'send-button';
                    element.className = 'chat-button';
                    element.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><path d="M25 20 L75 50 L25 80" fill="none" stroke="currentColor" stroke-width="15"></path></svg>';
                    container?.appendChild(element);
                    break;
                    
                case 'input-section':
                    element = document.createElement('div');
                    element.id = 'input-section';
                    element.className = 'input-section';
                    container?.appendChild(element);
                    break;
                    
                case 'progress-bar':
                    element = document.createElement('div');
                    element.id = 'progress-bar';
                    element.className = 'progress-bar';
                    container?.appendChild(element);
                    break;
            }
            
            if (element) {
                fixes.push(`Created ${id}`);
                console.log(`✅ Created ${id}`);
            }
        }
    });
    
    return fixes;
};

// Auto-run diagnostics when script loads
console.log('🚀 Element Discovery Debugger Loaded');
console.log('Run debugElementDiscovery() for analysis');
console.log('Run stateAwareElementDiscovery() for smart discovery');
