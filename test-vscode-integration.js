#!/usr/bin/env node

/**
 * Test script to verify @vscode/test-web integration
 */

import fs from 'fs';
import path from 'path';

console.log('🧪 Testing VS Code Web Integration...\n');

// Test 1: Check if @vscode/test-web is installed
try {
    const packageJsonPath = path.join(process.cwd(), 'package.json');
    const packageJson = JSON.parse(fs.readFileSync(packageJsonPath, 'utf8'));
    
    if (packageJson.dependencies && packageJson.dependencies['@vscode/test-web']) {
        console.log('✅ @vscode/test-web is correctly listed as dependency');
        console.log(`   Version: ${packageJson.dependencies['@vscode/test-web']}`);
    } else {
        console.log('❌ @vscode/test-web not found in dependencies');
    }
} catch (error) {
    console.log('❌ Error reading package.json:', error.message);
}

// Test 2: Check if @vscode/test-web module exists
try {
    const vscodeModulePath = path.join(process.cwd(), 'node_modules', '@vscode', 'test-web');
    if (fs.existsSync(vscodeModulePath)) {
        console.log('✅ @vscode/test-web module is installed');
        
        // Check for main files
        const packageJsonPath = path.join(vscodeModulePath, 'package.json');
        if (fs.existsSync(packageJsonPath)) {
            const modulePackageJson = JSON.parse(fs.readFileSync(packageJsonPath, 'utf8'));
            console.log(`   Module version: ${modulePackageJson.version}`);
        }
    } else {
        console.log('❌ @vscode/test-web module not found');
    }
} catch (error) {
    console.log('❌ Error checking @vscode/test-web module:', error.message);
}

// Test 3: Check if VS Code setup files exist
const vscodeSetupPath = path.join(process.cwd(), 'webui', 'vscode-setup.js');
if (fs.existsSync(vscodeSetupPath)) {
    console.log('✅ VS Code setup script exists');
} else {
    console.log('❌ VS Code setup script not found');
}

// Test 4: Check if VS Code integration script exists
const vscodeIntegrationPath = path.join(process.cwd(), 'webui', 'js', 'vscode-integration.js');
if (fs.existsSync(vscodeIntegrationPath)) {
    console.log('✅ VS Code integration script exists');
} else {
    console.log('❌ VS Code integration script not found');
}

// Test 5: Check if gide-coding-agent configuration exists
const gideConfigPath = path.join(process.cwd(), 'gide-agent.json');
if (fs.existsSync(gideConfigPath)) {
    console.log('✅ gide-coding-agent configuration exists');
    try {
        const gideConfig = JSON.parse(fs.readFileSync(gideConfigPath, 'utf8'));
        console.log(`   Agent name: ${gideConfig.name}`);
        console.log(`   Agent version: ${gideConfig.version}`);
        console.log(`   Capabilities: ${Object.keys(gideConfig.capabilities).join(', ')}`);
    } catch (error) {
        console.log('⚠️  Error reading gide configuration:', error.message);
    }
} else {
    console.log('❌ gide-coding-agent configuration not found');
}

// Test 6: Check Railway configuration
const railwayTomlPath = path.join(process.cwd(), 'railway.toml');
if (fs.existsSync(railwayTomlPath)) {
    const railwayConfig = fs.readFileSync(railwayTomlPath, 'utf8');
    if (railwayConfig.includes('RAILPACK_PRUNE_DEPS = "false"')) {
        console.log('✅ Railway configured to prevent dependency pruning');
    } else {
        console.log('⚠️  Railway may prune dependencies (RAILPACK_PRUNE_DEPS not set to false)');
    }
} else {
    console.log('⚠️  Railway configuration not found');
}

// Test 7: Check if .vscode-test-web directory exists
const vscodeTestWebDir = path.join(process.cwd(), '.vscode-test-web');
if (fs.existsSync(vscodeTestWebDir)) {
    console.log('✅ .vscode-test-web directory exists');
} else {
    console.log('❌ .vscode-test-web directory not found');
}

console.log('\n🏁 VS Code Web Integration Test Complete!');
console.log('\n💡 To deploy to Railway:');
console.log('   1. Commit these changes');
console.log('   2. Push to Railway');
console.log('   3. Railway will skip pruning devDependencies due to RAILPACK_PRUNE_DEPS=false');
console.log('   4. @vscode/test-web will be available at runtime');