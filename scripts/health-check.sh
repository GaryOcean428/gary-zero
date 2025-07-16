#!/bin/bash
# Weekly health check script for Gary-Zero QA Initiative
# Monitors code quality, security, performance, and dependencies

set -e

echo "=== Gary-Zero Health Check ==="
echo "$(date): Starting comprehensive health check..."

# Create reports directory if it doesn't exist
mkdir -p ./reports

echo ""
echo "📦 Checking Dependencies..."
echo "----------------------------------------"

# Check for security vulnerabilities in dependencies
echo "🔍 Security audit..."
if command -v npm &> /dev/null; then
    npm audit --level moderate 2>&1 | tee ./reports/security-audit.log
else
    echo "⚠️  npm not available, skipping security audit"
fi

# Check for outdated dependencies
echo "📅 Checking for outdated packages..."
if command -v npm &> /dev/null; then
    npm outdated 2>&1 | tee ./reports/outdated-packages.log || true
else
    echo "⚠️  npm not available, skipping outdated check"
fi

echo ""
echo "🧹 Code Quality Checks..."
echo "----------------------------------------"

# TypeScript compilation check
echo "🔧 TypeScript compilation check..."
if command -v npx &> /dev/null && [ -f tsconfig.json ]; then
    npx tsc --noEmit 2>&1 | tee ./reports/typescript-check.log || true
else
    echo "⚠️  TypeScript not available or no tsconfig.json found"
fi

# Linting
echo "📝 Running linter..."
if command -v npm &> /dev/null; then
    npm run lint --silent 2>&1 | tee ./reports/lint-results.log || true
else
    echo "⚠️  npm not available, skipping lint"
fi

echo ""
echo "🧪 Testing & Coverage..."
echo "----------------------------------------"

# Run tests with coverage
echo "🎯 Running tests with coverage..."
if command -v npm &> /dev/null; then
    npm run test:coverage --silent 2>&1 | tee ./reports/test-coverage.log || true
else
    echo "⚠️  npm not available, skipping tests"
fi

echo ""
echo "📊 Bundle Analysis..."
echo "----------------------------------------"

# Bundle size check (if bundlesize is configured)
echo "📦 Checking bundle size..."
if command -v npx &> /dev/null && npm list bundlesize &> /dev/null; then
    npx bundlesize 2>&1 | tee ./reports/bundle-size.log || true
else
    echo "⚠️  bundlesize not configured, skipping bundle analysis"
fi

echo ""
echo "🏗️  Build Check..."
echo "----------------------------------------"

# Build check
echo "🔨 Running build check..."
if command -v npm &> /dev/null && npm run build --silent &> /dev/null; then
    echo "✅ Build successful"
    echo "$(date): Build successful" >> ./reports/build-status.log
else
    echo "❌ Build failed"
    echo "$(date): Build failed" >> ./reports/build-status.log
fi

echo ""
echo "📈 Performance Metrics..."
echo "----------------------------------------"

# File count and size analysis
echo "📁 Analyzing project structure..."
total_files=$(find . -type f -name "*.js" -o -name "*.ts" -o -name "*.tsx" -o -name "*.jsx" | grep -v node_modules | wc -l)
total_lines=$(find . -type f -name "*.js" -o -name "*.ts" -o -name "*.tsx" -o -name "*.jsx" | grep -v node_modules | xargs wc -l | tail -1 | awk '{print $1}')

echo "📊 Project Statistics:" | tee ./reports/project-stats.log
echo "  - Total source files: $total_files" | tee -a ./reports/project-stats.log
echo "  - Total lines of code: $total_lines" | tee -a ./reports/project-stats.log

# Check for duplicate files
echo "🔍 Checking for duplicate files..."
find . -type f -name "*.ts" -o -name "*.tsx" -o -name "*.js" -o -name "*.jsx" | \
  grep -v node_modules | \
  xargs md5sum | sort | uniq -d -w32 > ./reports/duplicate-files.log 2>/dev/null || true

duplicate_count=$(wc -l < ./reports/duplicate-files.log)
if [ "$duplicate_count" -gt 0 ]; then
    echo "⚠️  Found $duplicate_count duplicate files (see reports/duplicate-files.log)"
else
    echo "✅ No duplicate files found"
fi

echo ""
echo "🎯 Health Check Summary..."
echo "----------------------------------------"

# Generate health score
health_score=100

# Deduct points for issues
if [ -s ./reports/security-audit.log ] && grep -q "vulnerabilities" ./reports/security-audit.log; then
    health_score=$((health_score - 20))
    echo "❌ Security vulnerabilities found (-20 points)"
fi

if [ -s ./reports/lint-results.log ] && [ "$(wc -l < ./reports/lint-results.log)" -gt 1 ]; then
    health_score=$((health_score - 15))
    echo "⚠️  Linting issues found (-15 points)"
fi

if [ -s ./reports/typescript-check.log ] && grep -q "error" ./reports/typescript-check.log; then
    health_score=$((health_score - 15))
    echo "❌ TypeScript compilation errors (-15 points)"
fi

if grep -q "Build failed" ./reports/build-status.log 2>/dev/null; then
    health_score=$((health_score - 25))
    echo "❌ Build failure (-25 points)"
fi

if [ "$duplicate_count" -gt 0 ]; then
    health_score=$((health_score - 10))
    echo "⚠️  Duplicate files found (-10 points)"
fi

echo ""
echo "🏆 Overall Health Score: $health_score/100"

if [ "$health_score" -ge 90 ]; then
    echo "🎉 Excellent! Project is in great health."
elif [ "$health_score" -ge 75 ]; then
    echo "👍 Good! Minor issues to address."
elif [ "$health_score" -ge 60 ]; then
    echo "⚠️  Fair. Several issues need attention."
else
    echo "🚨 Poor. Immediate attention required!"
fi

echo ""
echo "📁 Reports generated in ./reports/"
echo "$(date): Health check completed with score: $health_score/100" >> ./reports/health-history.log

echo "=== Health Check Complete ==="