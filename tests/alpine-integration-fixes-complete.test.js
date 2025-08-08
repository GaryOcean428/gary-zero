/**
 * Integration Test for Alpine.js Fixes - Simple Validation
 * Tests the complete fix for "Cannot read properties of undefined (reading 'bind')" error
 */

import { describe, it, expect } from 'vitest';

describe('Alpine.js Integration Fixes - File Validation', () => {

    it('should validate settings.js has the binding fix', () => {
        const fs = require('fs');
        const path = require('path');
        const settingsPath = path.join(__dirname, '..', 'webui', 'js', 'settings.js');
        const content = fs.readFileSync(settingsPath, 'utf8');
        
        // Should contain the fixed initialization pattern
        expect(content).toContain('this._actualSaveSettings = async function()');
        expect(content).toContain('.bind(this)');
        expect(content).toContain('_setupDebouncedSave()');
        
        // Should NOT contain the old broken pattern
        expect(content).not.toContain('this._actualSaveSettings.bind(this)') || 
               expect(content).toMatch(/this\._actualSaveSettings\s*=.*\.bind\(this\)/);
    });

    it('should validate error-boundary.js has fetchCurrentModel improvements', () => {
        const fs = require('fs');
        const path = require('path');
        const errorBoundaryPath = path.join(__dirname, '..', 'webui', 'js', 'error-boundary.js');
        const content = fs.readFileSync(errorBoundaryPath, 'utf8');
        
        // Should contain the improved race condition handling
        expect(content).toContain('fetchModelQueue');
        expect(content).toContain('registerFetchCurrentModel');
        expect(content).toContain('new Promise((resolve, reject)');
        expect(content).toContain('while (fetchModelQueue.length > 0)');
    });

    it('should validate iframe security improvements', () => {
        const fs = require('fs');
        const path = require('path');
        const indexPath = path.join(__dirname, '..', 'webui', 'index.html');
        const content = fs.readFileSync(indexPath, 'utf8');
        
        // Should have improved security attributes
        expect(content).toContain('sandbox="allow-scripts"');
        expect(content).toContain('referrerpolicy="strict-origin-when-cross-origin"');
        
        // Should not have the old insecure attributes
        expect(content).not.toContain('allow-same-origin');
        expect(content).not.toContain('allow-forms');
        expect(content).not.toContain('allow-popups');
        expect(content).not.toContain('allow-modals');
    });

    it('should validate new component files exist', () => {
        const fs = require('fs');
        const path = require('path');
        
        // Check init-orchestrator.js
        const orchestratorPath = path.join(__dirname, '..', 'webui', 'js', 'init-orchestrator.js');
        expect(fs.existsSync(orchestratorPath)).toBe(true);
        
        const orchestratorContent = fs.readFileSync(orchestratorPath, 'utf8');
        expect(orchestratorContent).toContain('class InitOrchestrator');
        expect(orchestratorContent).toContain('register(name, initFn, deps');
        
        // Check alpine-error-recovery.js
        const recoveryPath = path.join(__dirname, '..', 'webui', 'js', 'alpine-error-recovery.js');
        expect(fs.existsSync(recoveryPath)).toBe(true);
        
        const recoveryContent = fs.readFileSync(recoveryPath, 'utf8');
        expect(recoveryContent).toContain('handleBindingError');
        expect(recoveryContent).toContain('safeRegisterAlpineComponent');
    });

    it('should validate debounce function is syntactically correct', () => {
        const fs = require('fs');
        const path = require('path');
        const settingsPath = path.join(__dirname, '..', 'webui', 'js', 'settings.js');
        const content = fs.readFileSync(settingsPath, 'utf8');
        
        // Extract debounce function
        const debounceMatch = content.match(/function debounce\([^}]+\}[\s\S]*?return debounced;[\s\S]*?\}/);
        expect(debounceMatch).toBeTruthy();
        
        // Should be able to create the function without syntax errors
        expect(() => {
            new Function('return ' + debounceMatch[0])();
        }).not.toThrow();
    });

    it('should validate component binding logic is correct', () => {
        const fs = require('fs');
        const path = require('path');
        const settingsPath = path.join(__dirname, '..', 'webui', 'js', 'settings.js');
        const content = fs.readFileSync(settingsPath, 'utf8');
        
        // Extract the init method from settingsModalProxy
        const proxyInitMatch = content.match(/init\(\)\s*\{[\s\S]*?this\._debouncedSaveSettings[\s\S]*?\}/);
        expect(proxyInitMatch).toBeTruthy();
        
        // Should define _actualSaveSettings before using it
        const initContent = proxyInitMatch[0];
        const actualSavePos = initContent.indexOf('this._actualSaveSettings = async function');
        const bindPos = initContent.indexOf('this._actualSaveSettings, 1000');
        
        // _actualSaveSettings should be defined before being used
        expect(actualSavePos).toBeLessThan(bindPos);
        expect(actualSavePos).toBeGreaterThan(-1);
        expect(bindPos).toBeGreaterThan(-1);
    });
});