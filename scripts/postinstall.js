#!/usr/bin/env node

/**
 * Post-install script for gary-zero project
 * Installs essential components like Python and ensures @vscode/test-web is properly configured
 */

import { execSync } from 'child_process';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const projectRoot = path.resolve(__dirname, '..');

console.log('🔧 Running post-install setup for gary-zero...');

function runCommand(command, description) {
    try {
        console.log(`📦 ${description}...`);
        execSync(command, { stdio: 'inherit' });
        console.log(`✅ ${description} completed successfully`);
        return true;
    } catch (error) {
        console.warn(`⚠️  ${description} failed: ${error.message}`);
        return false;
    }
}

function checkCommand(command, name) {
    try {
        execSync(`${command} --version`, { stdio: 'pipe' });
        console.log(`✅ ${name} is available`);
        return true;
    } catch (error) {
        console.log(`❌ ${name} is not available`);
        return false;
    }
}

// Check for essential tools
console.log('\n🔍 Checking for essential tools:');
const pythonAvailable = checkCommand('python3', 'Python3') || checkCommand('python', 'Python');
const npmAvailable = checkCommand('npm', 'npm');

// Ensure .vscode-test-web directory exists for @vscode/test-web
const vscodeTestDir = path.join(projectRoot, '.vscode-test-web');
if (!fs.existsSync(vscodeTestDir)) {
    console.log('📁 Creating .vscode-test-web directory...');
    fs.mkdirSync(vscodeTestDir, { recursive: true });
}

// Initialize @vscode/test-web if available
try {
    // Check if @vscode/test-web is installed
    const packageJsonPath = path.join(projectRoot, 'package.json');
    const packageJson = JSON.parse(fs.readFileSync(packageJsonPath, 'utf8'));
    
    if (packageJson.dependencies && packageJson.dependencies['@vscode/test-web']) {
        console.log('✅ @vscode/test-web is listed as dependency');
        
        // Create a basic setup file for VS Code web environment
        const setupScript = `
// VS Code Web Setup for Gary-Zero
// This file provides VS Code web environment setup

export async function setupVSCodeWeb(options = {}) {
    const defaultOptions = {
        browserType: 'chromium',
        extensionDevelopmentPath: process.cwd(),
        extensionTestsPath: './webui',
        ...options
    };
    
    console.log('Setting up VS Code web environment...');
    return defaultOptions;
}

// Export placeholder for test-web functionality
export const testWeb = {
    initialized: false,
    async init() {
        console.log('Initializing VS Code test-web...');
        this.initialized = true;
        return true;
    }
};
`;
        
        const setupPath = path.join(projectRoot, 'webui', 'vscode-setup.js');
        fs.writeFileSync(setupPath, setupScript);
        console.log('✅ VS Code web setup script created');
    }
} catch (error) {
    console.warn('⚠️  @vscode/test-web setup skipped:', error.message);
}

// Install Python dependencies if requirements.txt exists
const reqPath = path.join(projectRoot, 'requirements.txt');
if (fs.existsSync(reqPath) && pythonAvailable) {
    const pipCommand = 'pip3 install -r requirements.txt || pip install -r requirements.txt';
    runCommand(pipCommand, 'Installing Python dependencies');
}

// Create gide-coding-agent configuration
const gideConfig = {
    name: "gide-coding-agent",
    version: "1.0.0",
    description: "AI coding agent extension for gary-zero",
    main: "./webui/index.js",
    capabilities: {
        codeCompletion: true,
        codeGeneration: true,
        codeAnalysis: true,
        chatInterface: true
    },
    vscode: {
        webExtension: true,
        engines: "^1.74.0"
    }
};

const gideConfigPath = path.join(projectRoot, 'gide-agent.json');
fs.writeFileSync(gideConfigPath, JSON.stringify(gideConfig, null, 2));
console.log('✅ gide-coding-agent configuration created');

console.log('\n🎉 Post-install setup completed!');
console.log('💡 Gary-Zero is now ready with VS Code web capabilities');
