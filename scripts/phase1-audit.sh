#!/bin/bash
# Phase 1: Code Quality & Deduplication Audit Tools
# File system analysis and code quality metrics

set -e

echo "=== Phase 1: Code Quality & Deduplication Audit ==="
echo "$(date): Starting comprehensive code analysis..."

# Create reports directory
mkdir -p ./reports/phase1

echo ""
echo "📁 File System Analysis..."
echo "----------------------------------------"

# Component structure analysis
echo "🧩 Analyzing component structure..."
if [ -d "./webui/components" ]; then
    find ./webui/components -name "*.js" -o -name "*.tsx" -o -name "*.jsx" | while read file; do
        lines=$(wc -l < "$file")
        echo "$lines $file"
    done | sort -nr > ./reports/phase1/component-sizes.log
    
    echo "📊 Component Analysis Results:" | tee ./reports/phase1/component-analysis.log
    echo "  - Total components: $(find ./webui/components -name "*.js" -o -name "*.tsx" -o -name "*.jsx" | wc -l)" | tee -a ./reports/phase1/component-analysis.log
    echo "  - Largest components (>100 lines):" | tee -a ./reports/phase1/component-analysis.log
    awk '$1 > 100 {print "    " $1 " lines: " $2}' ./reports/phase1/component-sizes.log | tee -a ./reports/phase1/component-analysis.log
else
    echo "⚠️  No components directory found at ./webui/components"
fi

# Route analysis
echo "🛣️  Analyzing route structure..."
echo "📊 Route Analysis:" > ./reports/phase1/route-analysis.log
find . -name "*.js" -o -name "*.ts" -o -name "*.tsx" -o -name "*.jsx" | \
    grep -v node_modules | \
    xargs grep -l "useNavigate\|Navigate\|Link\|router\|route" | \
    wc -l > ./reports/phase1/route-file-count.log

route_files=$(cat ./reports/phase1/route-file-count.log)
echo "  - Files with routing logic: $route_files" | tee -a ./reports/phase1/route-analysis.log

# State management analysis  
echo "🔄 Analyzing state management patterns..."
echo "📊 State Management Analysis:" > ./reports/phase1/state-analysis.log

useState_count=$(find . -name "*.js" -o -name "*.ts" -o -name "*.tsx" -o -name "*.jsx" | \
    grep -v node_modules | \
    xargs grep -c "useState" | \
    awk -F: '{sum += $2} END {print sum}' || echo "0")

useReducer_count=$(find . -name "*.js" -o -name "*.ts" -o -name "*.tsx" -o -name "*.jsx" | \
    grep -v node_modules | \
    xargs grep -c "useReducer" | \
    awk -F: '{sum += $2} END {print sum}' || echo "0")

useContext_count=$(find . -name "*.js" -o -name "*.ts" -o -name "*.tsx" -o -name "*.jsx" | \
    grep -v node_modules | \
    xargs grep -c "useContext" | \
    awk -F: '{sum += $2} END {print sum}' || echo "0")

echo "  - useState usage: $useState_count" | tee -a ./reports/phase1/state-analysis.log
echo "  - useReducer usage: $useReducer_count" | tee -a ./reports/phase1/state-analysis.log  
echo "  - useContext usage: $useContext_count" | tee -a ./reports/phase1/state-analysis.log

# Find state management files
find . -name "*context*" -o -name "*store*" -o -name "*state*" | \
    grep -v node_modules > ./reports/phase1/state-files.log
state_file_count=$(wc -l < ./reports/phase1/state-files.log)
echo "  - State management files: $state_file_count" | tee -a ./reports/phase1/state-analysis.log

echo ""
echo "🔍 Dependency Analysis..."
echo "----------------------------------------"

# Check for unused dependencies
echo "📦 Checking for unused dependencies..."
if command -v npx &> /dev/null; then
    # Check if unimported is available
    if npm list unimported &> /dev/null; then
        npx unimported 2>&1 | tee ./reports/phase1/unused-dependencies.log || true
    else
        echo "⚠️  unimported not installed, skipping unused dependency check"
        echo "To add this check, run: npm install --save-dev unimported"
    fi
    
    # Check if ts-unused-exports is available  
    if npm list ts-unused-exports &> /dev/null && [ -f tsconfig.json ]; then
        npx ts-unused-exports tsconfig.json --excludePathsFromReport=node_modules 2>&1 | tee ./reports/phase1/unused-exports.log || true
    else
        echo "⚠️  ts-unused-exports not installed or no tsconfig.json found"
        echo "To add this check, run: npm install --save-dev ts-unused-exports"
    fi
else
    echo "⚠️  npm not available, skipping dependency analysis"
fi

echo ""
echo "🎯 Duplication Detection..."
echo "----------------------------------------"

# Check if jscpd is available
if command -v npx &> /dev/null && npm list jscpd &> /dev/null; then
    echo "🔍 Running code duplication analysis..."
    npx jscpd --min-lines 10 --min-tokens 50 --formats javascript,typescript \
        --output ./reports/phase1/duplication 2>&1 | tee ./reports/phase1/duplication.log || true
else
    echo "⚠️  jscpd not installed, skipping duplication analysis"
    echo "To add this check, run: npm install --save-dev jscpd"
    
    # Basic duplication check using md5sum
    echo "🔍 Running basic file duplication check..."
    find . -type f \( -name "*.js" -o -name "*.ts" -o -name "*.tsx" -o -name "*.jsx" \) | \
        grep -v node_modules | \
        xargs md5sum | sort | uniq -d -w32 > ./reports/phase1/duplicate-files-basic.log 2>/dev/null || true
    
    duplicate_count=$(wc -l < ./reports/phase1/duplicate-files-basic.log)
    if [ "$duplicate_count" -gt 0 ]; then
        echo "⚠️  Found $duplicate_count potentially duplicate files"
        echo "Duplicate files:" | tee ./reports/phase1/duplication-summary.log
        cat ./reports/phase1/duplicate-files-basic.log | tee -a ./reports/phase1/duplication-summary.log
    else
        echo "✅ No exact duplicate files found"
    fi
fi

echo ""
echo "📊 Import/Export Analysis..."
echo "----------------------------------------"

# Analyze import patterns
echo "🔗 Analyzing import patterns..."
echo "📊 Import Analysis:" > ./reports/phase1/import-analysis.log

# Count import types
es6_imports=$(find . -name "*.js" -o -name "*.ts" -o -name "*.tsx" -o -name "*.jsx" | \
    grep -v node_modules | \
    xargs grep -c "^import " | \
    awk -F: '{sum += $2} END {print sum}' || echo "0")

require_imports=$(find . -name "*.js" -o -name "*.ts" -o -name "*.tsx" -o -name "*.jsx" | \
    grep -v node_modules | \
    xargs grep -c "require(" | \
    awk -F: '{sum += $2} END {print sum}' || echo "0")

dynamic_imports=$(find . -name "*.js" -o -name "*.ts" -o -name "*.tsx" -o -name "*.jsx" | \
    grep -v node_modules | \
    xargs grep -c "import(" | \
    awk -F: '{sum += $2} END {print sum}' || echo "0")

echo "  - ES6 imports: $es6_imports" | tee -a ./reports/phase1/import-analysis.log
echo "  - CommonJS requires: $require_imports" | tee -a ./reports/phase1/import-analysis.log
echo "  - Dynamic imports: $dynamic_imports" | tee -a ./reports/phase1/import-analysis.log

# Find relative imports that could be optimized
echo "🔍 Finding potentially problematic imports..."
find . -name "*.js" -o -name "*.ts" -o -name "*.tsx" -o -name "*.jsx" | \
    grep -v node_modules | \
    xargs grep -n "import.*\.\./\.\./\.\." > ./reports/phase1/deep-relative-imports.log 2>/dev/null || true

deep_import_count=$(wc -l < ./reports/phase1/deep-relative-imports.log)
if [ "$deep_import_count" -gt 0 ]; then
    echo "⚠️  Found $deep_import_count deep relative imports (../../../)" | tee -a ./reports/phase1/import-analysis.log
    echo "  Consider using absolute imports or path aliases" | tee -a ./reports/phase1/import-analysis.log
else
    echo "✅ No problematic deep relative imports found" | tee -a ./reports/phase1/import-analysis.log
fi

echo ""
echo "📈 Code Complexity Metrics..."
echo "----------------------------------------"

# Calculate average file size
echo "📏 Calculating code metrics..."
total_files=$(find . -type f -name "*.js" -o -name "*.ts" -o -name "*.tsx" -o -name "*.jsx" | grep -v node_modules | wc -l)
total_lines=$(find . -type f -name "*.js" -o -name "*.ts" -o -name "*.tsx" -o -name "*.jsx" | grep -v node_modules | xargs wc -l | tail -1 | awk '{print $1}' || echo "0")

if [ "$total_files" -gt 0 ]; then
    avg_file_size=$((total_lines / total_files))
else
    avg_file_size=0
fi

echo "📊 Code Complexity Metrics:" | tee ./reports/phase1/complexity-metrics.log
echo "  - Total source files: $total_files" | tee -a ./reports/phase1/complexity-metrics.log
echo "  - Total lines of code: $total_lines" | tee -a ./reports/phase1/complexity-metrics.log
echo "  - Average file size: $avg_file_size lines" | tee -a ./reports/phase1/complexity-metrics.log

# Find largest files
echo "  - Largest files (>200 lines):" | tee -a ./reports/phase1/complexity-metrics.log
find . -type f -name "*.js" -o -name "*.ts" -o -name "*.tsx" -o -name "*.jsx" | \
    grep -v node_modules | \
    xargs wc -l | \
    awk '$1 > 200 {print "    " $1 " lines: " $2}' | \
    sort -nr | tee -a ./reports/phase1/complexity-metrics.log

echo ""
echo "🎯 Phase 1 Summary..."
echo "----------------------------------------"

echo "📋 Analysis Complete!" | tee ./reports/phase1/summary.log
echo "$(date): Phase 1 analysis completed" | tee -a ./reports/phase1/summary.log
echo "" | tee -a ./reports/phase1/summary.log
echo "Key Findings:" | tee -a ./reports/phase1/summary.log
echo "  - Total source files analyzed: $total_files" | tee -a ./reports/phase1/summary.log
echo "  - Average file size: $avg_file_size lines" | tee -a ./reports/phase1/summary.log
echo "  - Files with routing logic: $route_files" | tee -a ./reports/phase1/summary.log
echo "  - State management instances: $((useState_count + useReducer_count + useContext_count))" | tee -a ./reports/phase1/summary.log
echo "  - Deep relative imports: $deep_import_count" | tee -a ./reports/phase1/summary.log
echo "" | tee -a ./reports/phase1/summary.log
echo "📁 Detailed reports available in ./reports/phase1/" | tee -a ./reports/phase1/summary.log

echo "=== Phase 1 Analysis Complete ==="