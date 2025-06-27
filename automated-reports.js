#!/usr/bin/env node

/**
 * Automated Issue Reporting Script
 * Runs comprehensive accessibility, compatibility, and security checks
 */

import { execSync } from 'node:child_process';
import fs from 'node:fs';
import process from 'node:process';

const colors = {
  green: '\x1b[32m',
  red: '\x1b[31m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  reset: '\x1b[0m',
  bold: '\x1b[1m'
};

function log(message, color = '') {
  // eslint-disable-next-line no-console
  console.log(`${color}${message}${colors.reset}`);
}

function runCommand(command, description) {
  log(`\n${colors.blue}${colors.bold}Running: ${description}${colors.reset}`);
  log(`Command: ${command}`, colors.yellow);
  
  try {
    const output = execSync(command, { 
      encoding: 'utf8', 
      stdio: 'pipe',
      cwd: process.cwd()
    });
    log(`✅ ${description} completed successfully`, colors.green);
    return { success: true, output };
  } catch (error) {
    log(`❌ ${description} failed`, colors.red);
    log(`Error: ${error.message}`, colors.red);
    return { success: false, error: error.message, output: error.stdout };
  }
}

function createReportDirectory() {
  const reportsDir = './reports';
  if (!fs.existsSync(reportsDir)) {
    fs.mkdirSync(reportsDir, { recursive: true });
    log(`📁 Created reports directory: ${reportsDir}`, colors.green);
  }
  return reportsDir;
}

async function main() {
  log(`${colors.bold}${colors.blue}🔍 Starting Automated Issue Reporting${colors.reset}`);
  log('This will check for accessibility, compatibility, and security issues\n');

  const reportsDir = createReportDirectory();
  const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
  
  const checks = [
    {
      name: 'ESLint Code Quality & Security',
      command: 'npx eslint "webui/**/*.js" --format json',
      outputFile: `${reportsDir}/eslint-report-${timestamp}.json`,
      description: 'JavaScript code quality, security, and accessibility issues'
    },
    {
      name: 'NPM Security Audit',
      command: 'npm audit --json',
      outputFile: `${reportsDir}/security-audit-${timestamp}.json`,
      description: 'Package vulnerability and security issues'
    },
    {
      name: 'HTML Validation',
      command: 'find webui -name "*.html" -exec htmlhint {} \\;',
      outputFile: `${reportsDir}/html-validation-${timestamp}.txt`,
      description: 'HTML markup validation and accessibility'
    },
    {
      name: 'CSS Quality Check',
      command: 'find webui -name "*.css" -exec stylelint {} \\;',
      outputFile: `${reportsDir}/css-quality-${timestamp}.txt`,
      description: 'CSS quality and compatibility issues'
    }
  ];

  const results = {
    timestamp: new Date().toISOString(),
    reports: []
  };

  for (const check of checks) {
    const result = runCommand(check.command, check.name);
    
    // Save individual report
    if (result.output) {
      try {
        fs.writeFileSync(check.outputFile, result.output);
        log(`📄 Report saved: ${check.outputFile}`, colors.green);
      } catch (writeError) {
        log(`❌ Failed to save report: ${writeError.message}`, colors.red);
      }
    }

    results.reports.push({
      name: check.name,
      description: check.description,
      success: result.success,
      outputFile: check.outputFile,
      hasIssues: result.output && result.output.length > 0
    });
  }

  // Generate summary report
  const summaryFile = `${reportsDir}/summary-${timestamp}.json`;
  fs.writeFileSync(summaryFile, JSON.stringify(results, null, 2));
  
  log(`\n${colors.bold}${colors.blue}📊 Report Summary${colors.reset}`);
  log(`Generated ${results.reports.length} reports`);
  
  const failedChecks = results.reports.filter(r => !r.success);
  const checksWithIssues = results.reports.filter(r => r.hasIssues);
  
  if (failedChecks.length > 0) {
    log(`❌ ${failedChecks.length} checks failed to run`, colors.red);
  }
  
  if (checksWithIssues.length > 0) {
    log(`⚠️  ${checksWithIssues.length} checks found issues`, colors.yellow);
  } else {
    log(`✅ No issues found in any checks`, colors.green);
  }
  
  log(`\n📄 Summary report: ${summaryFile}`, colors.blue);
  log(`📁 All reports saved in: ${reportsDir}`, colors.blue);
  
  // Quick fix suggestions
  log(`\n${colors.bold}Quick Fix Commands:${colors.reset}`);
  log(`• Fix JavaScript issues: ${colors.yellow}npm run lint:fix${colors.reset}`);
  log(`• Fix security issues: ${colors.yellow}npm audit fix${colors.reset}`);
  log(`• Run all fixes: ${colors.yellow}npm run fix:all${colors.reset}`);
}

// Handle CLI arguments
const args = process.argv.slice(2);
if (args.includes('--help') || args.includes('-h')) {
  log(`${colors.bold}Automated Issue Reporting Tool${colors.reset}`);
  log('Usage: node automated-reports.js [options]');
  log('\nOptions:');
  log('  --help, -h    Show this help message');
  log('  --version     Show version');
  log('\nThis tool runs comprehensive checks for:');
  log('• JavaScript code quality and security (ESLint)');
  log('• Package vulnerabilities (npm audit)');
  log('• HTML validation and accessibility (HTMLHint)');
  log('• CSS quality and compatibility (Stylelint)');
  process.exit(0);
}

if (args.includes('--version')) {
  const packageJson = JSON.parse(fs.readFileSync('./package.json', 'utf8'));
  log(`Version: ${packageJson.version}`);
  process.exit(0);
}

main().catch(error => {
  log(`❌ Unexpected error: ${error.message}`, colors.red);
  process.exit(1);
});
