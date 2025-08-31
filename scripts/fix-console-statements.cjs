#!/usr/bin/env node

/**
 * Automated Console Statement Replacement Script
 * Replaces direct console calls with proper logging utility
 */

const fs = require('fs');
const path = require('path');

const WEBUI_DIR = path.join(process.cwd(), 'webui');
const LOGGER_PATH = 'console-logger.js';

// Files to process (from linting output)
const filesToProcess = [
    'webui/components/settings/mcp/client/mcp-servers-store.js',
    'webui/index.js',
    'webui/js/components.js',
    'webui/js/csp-alpine-fix.js',
    'webui/js/enhanced-ux.js',
    'webui/js/file_browser.js',
    'webui/js/history.js',
    'webui/js/image_modal.js',
    'webui/js/initFw.js',
    'webui/js/messages.js',
    'webui/js/modal.js',
    'webui/js/modals.js',
    'webui/js/scheduler.js',
    'webui/js/settings.js',
    'webui/js/speech_browser.js',
    'webui/js/tunnel.js'
];

function injectLoggerImport(content, filePath) {
    // Skip if already has logger import
    if (content.includes('console-logger.js') || content.includes('GaryLogger')) {
        return content;
    }

    // Calculate relative path to logger
    const fileDir = path.dirname(filePath);
    const relativePath = path.relative(fileDir, path.join('webui/js', LOGGER_PATH));
    
    // Add logger import at the top
    const importStatement = `// Import enhanced logger\nimport { logger } from './${relativePath.replace(/\\/g, '/')}';\n\n`;
    
    return importStatement + content;
}

function replaceConsoleStatements(content) {
    let modified = content;
    
    // Replace console.log with logger.log
    modified = modified.replace(/console\.log\(/g, 'logger.log(');
    
    // Replace console.warn with logger.warn
    modified = modified.replace(/console\.warn\(/g, 'logger.warn(');
    
    // Replace console.error with logger.error
    modified = modified.replace(/console\.error\(/g, 'logger.error(');
    
    // Replace console.debug with logger.debug
    modified = modified.replace(/console\.debug\(/g, 'logger.debug(');
    
    // Replace console.info with logger.log
    modified = modified.replace(/console\.info\(/g, 'logger.log(');
    
    return modified;
}

function removeUnusedVariables(content) {
    // Remove lines that define but don't use variables
    const lines = content.split('\n');
    const cleanedLines = [];
    
    for (let i = 0; i < lines.length; i++) {
        const line = lines[i];
        
        // Skip lines with unused variables based on common patterns
        if (line.includes("'_e' is defined but never used") ||
            line.includes("'time' is defined but never used") ||
            line.includes("'date' is assigned a value but never used") ||
            line.includes("'toast' is assigned a value but never used")) {
            continue;
        }
        
        // Fix specific unused variable patterns
        if (line.match(/const\s+_e\s*=/)) {
            // Comment out unused error variable
            cleanedLines.push('        // ' + line.trim() + ' // Unused error variable');
            continue;
        }
        
        if (line.match(/const\s+time\s*=/)) {
            // Comment out unused time variable
            cleanedLines.push('    // ' + line.trim() + ' // Unused time variable');
            continue;
        }
        
        cleanedLines.push(line);
    }
    
    return cleanedLines.join('\n');
}

function processFile(filePath) {
    console.log(`Processing: ${filePath}`);
    
    try {
        let content = fs.readFileSync(filePath, 'utf8');
        let hasChanges = false;
        
        // Count console statements before
        const consoleCountBefore = (content.match(/console\./g) || []).length;
        
        // Apply transformations
        const originalContent = content;
        
        // Add logger import (if it's a JS module)
        if (filePath.endsWith('.js') && !content.includes('console-logger.js')) {
            content = injectLoggerImport(content, filePath);
            hasChanges = true;
        }
        
        // Replace console statements
        content = replaceConsoleStatements(content);
        hasChanges = hasChanges || (content !== originalContent);
        
        // Remove unused variables
        content = removeUnusedVariables(content);
        hasChanges = hasChanges || (content !== originalContent);
        
        // Count console statements after
        const consoleCountAfter = (content.match(/console\./g) || []).length;
        
        if (hasChanges) {
            // Create backup
            fs.writeFileSync(filePath + '.backup', originalContent);
            
            // Write updated content
            fs.writeFileSync(filePath, content);
            
            console.log(`  ✅ Updated: ${consoleCountBefore} → ${consoleCountAfter} console statements`);
        } else {
            console.log(`  ℹ️  No changes needed`);
        }
        
        return {
            file: filePath,
            consoleCountBefore,
            consoleCountAfter,
            hasChanges
        };
        
    } catch (error) {
        console.error(`  ❌ Error processing ${filePath}:`, error.message);
        return {
            file: filePath,
            error: error.message,
            hasChanges: false
        };
    }
}

function main() {
    console.log('🔧 Starting Console Statement Replacement');
    console.log('=========================================');
    
    const results = [];
    let totalConsoleStatementsBefore = 0;
    let totalConsoleStatementsAfter = 0;
    let filesProcessed = 0;
    let filesModified = 0;
    
    for (const filePath of filesToProcess) {
        if (fs.existsSync(filePath)) {
            const result = processFile(filePath);
            results.push(result);
            
            if (!result.error) {
                totalConsoleStatementsBefore += result.consoleCountBefore || 0;
                totalConsoleStatementsAfter += result.consoleCountAfter || 0;
                filesProcessed++;
                
                if (result.hasChanges) {
                    filesModified++;
                }
            }
        } else {
            console.log(`⚠️  File not found: ${filePath}`);
        }
    }
    
    console.log('\n📊 Summary Report');
    console.log('=================');
    console.log(`Files processed: ${filesProcessed}`);
    console.log(`Files modified: ${filesModified}`);
    console.log(`Console statements: ${totalConsoleStatementsBefore} → ${totalConsoleStatementsAfter}`);
    console.log(`Reduction: ${totalConsoleStatementsBefore - totalConsoleStatementsAfter} statements`);
    
    // Generate report
    const reportContent = {
        timestamp: new Date().toISOString(),
        summary: {
            filesProcessed,
            filesModified,
            consoleStatementsBefore: totalConsoleStatementsBefore,
            consoleStatementsAfter: totalConsoleStatementsAfter,
            reduction: totalConsoleStatementsBefore - totalConsoleStatementsAfter
        },
        results
    };
    
    fs.writeFileSync('console-cleanup-report.json', JSON.stringify(reportContent, null, 2));
    console.log('\n📄 Detailed report saved to: console-cleanup-report.json');
    
    console.log('\n🎉 Console statement cleanup completed!');
    console.log('💡 Remember to:');
    console.log('   1. Test the updated files');
    console.log('   2. Run linting to verify fixes');
    console.log('   3. Update imports if needed');
}

if (require.main === module) {
    main();
}

module.exports = { processFile, replaceConsoleStatements, removeUnusedVariables };