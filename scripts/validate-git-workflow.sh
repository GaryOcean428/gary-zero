#!/bin/bash

# Git Workflow Validation Script
# Comprehensive validation of Git repository state and workflow compliance
# Prevents deployment of uncommitted changes

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
MAX_UNTRACKED_FILES=10
MAX_COMMIT_AGE_HOURS=168  # 1 week

echo -e "${BLUE}🔍 Git Workflow Validation${NC}"
echo "=================================="

# Function to print colored output
print_status() {
    local status=$1
    local message=$2
    case $status in
        "SUCCESS")
            echo -e "${GREEN}✅ $message${NC}"
            ;;
        "WARNING")
            echo -e "${YELLOW}⚠️  $message${NC}"
            ;;
        "ERROR")
            echo -e "${RED}❌ $message${NC}"
            ;;
        "INFO")
            echo -e "${BLUE}ℹ️  $message${NC}"
            ;;
    esac
}

# Check if we're in a git repository
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    print_status "ERROR" "Not in a Git repository"
    exit 1
fi

VALIDATION_ERRORS=0
VALIDATION_WARNINGS=0

# 1. Check for uncommitted changes
print_status "INFO" "Checking for uncommitted changes..."
if ! git diff-index --quiet HEAD --; then
    print_status "ERROR" "Uncommitted changes detected!"
    echo ""
    echo "📋 Modified files:"
    git diff-index --name-only HEAD --
    echo ""
    echo "🔧 Required actions:"
    echo "   git add ."
    echo "   git commit -m \"Your commit message\""
    echo "   git push origin $(git branch --show-current)"
    VALIDATION_ERRORS=$((VALIDATION_ERRORS + 1))
else
    print_status "SUCCESS" "No uncommitted changes"
fi

# 2. Check for untracked files
print_status "INFO" "Checking for untracked files..."
UNTRACKED_FILES=$(git ls-files --others --exclude-standard)
UNTRACKED_COUNT=$(echo "$UNTRACKED_FILES" | grep -c . || true)

if [ -n "$UNTRACKED_FILES" ]; then
    if [ "$UNTRACKED_COUNT" -gt "$MAX_UNTRACKED_FILES" ]; then
        print_status "WARNING" "Large number of untracked files ($UNTRACKED_COUNT)"
        VALIDATION_WARNINGS=$((VALIDATION_WARNINGS + 1))
    else
        print_status "WARNING" "Untracked files found ($UNTRACKED_COUNT):"
        echo "$UNTRACKED_FILES" | head -10
        VALIDATION_WARNINGS=$((VALIDATION_WARNINGS + 1))
    fi
    echo ""
    echo "💡 Consider adding to .gitignore or committing if needed"
else
    print_status "SUCCESS" "No untracked files"
fi

# 3. Check if local branch is ahead of remote
print_status "INFO" "Checking remote synchronization..."
BRANCH=$(git branch --show-current)

if git rev-list --count origin/$BRANCH..$BRANCH > /dev/null 2>&1; then
    AHEAD_COUNT=$(git rev-list --count origin/$BRANCH..$BRANCH 2>/dev/null || echo "0")
    if [ "$AHEAD_COUNT" -gt 0 ]; then
        print_status "WARNING" "Local branch is $AHEAD_COUNT commits ahead of remote"
        echo "🔧 Push recommended: git push origin $BRANCH"
        VALIDATION_WARNINGS=$((VALIDATION_WARNINGS + 1))
    else
        print_status "SUCCESS" "Local branch is synchronized with remote"
    fi
else
    print_status "WARNING" "Cannot compare with remote (remote branch may not exist)"
    VALIDATION_WARNINGS=$((VALIDATION_WARNINGS + 1))
fi

# 4. Check commit history and age
print_status "INFO" "Validating commit history..."
LAST_COMMIT_HASH=$(git rev-parse HEAD)
LAST_COMMIT_AGE=$(git log -1 --format="%ct")
CURRENT_TIME=$(date +%s)
AGE_HOURS=$(( (CURRENT_TIME - LAST_COMMIT_AGE) / 3600 ))

if [ $AGE_HOURS -gt $MAX_COMMIT_AGE_HOURS ]; then
    print_status "WARNING" "Last commit is $AGE_HOURS hours old (>$MAX_COMMIT_AGE_HOURS hours)"
    VALIDATION_WARNINGS=$((VALIDATION_WARNINGS + 1))
else
    print_status "SUCCESS" "Recent commit activity (${AGE_HOURS}h ago)"
fi

# 5. Show recent commits for context
print_status "INFO" "Recent commit history:"
git log --oneline -5 --color=always

# 6. Check for merge conflicts
print_status "INFO" "Checking for merge conflict markers..."
CONFLICT_FILES=$(git diff --name-only --diff-filter=U 2>/dev/null || true)
if [ -n "$CONFLICT_FILES" ]; then
    print_status "ERROR" "Unresolved merge conflicts found!"
    echo "$CONFLICT_FILES"
    VALIDATION_ERRORS=$((VALIDATION_ERRORS + 1))
else
    # Also check for conflict markers in files
    CONFLICT_MARKERS=$(git grep -l "^<<<<<<< \|^=======$\|^>>>>>>> " 2>/dev/null || true)
    if [ -n "$CONFLICT_MARKERS" ]; then
        print_status "WARNING" "Possible conflict markers found in files:"
        echo "$CONFLICT_MARKERS"
        VALIDATION_WARNINGS=$((VALIDATION_WARNINGS + 1))
    else
        print_status "SUCCESS" "No merge conflicts detected"
    fi
fi

# 7. Summary
echo ""
echo "=================================="
echo -e "${BLUE}📊 Validation Summary${NC}"
echo "=================================="

if [ $VALIDATION_ERRORS -eq 0 ] && [ $VALIDATION_WARNINGS -eq 0 ]; then
    print_status "SUCCESS" "Git workflow validation passed completely!"
    echo "🚀 Repository is ready for deployment"
    exit 0
elif [ $VALIDATION_ERRORS -eq 0 ]; then
    print_status "WARNING" "Validation passed with $VALIDATION_WARNINGS warning(s)"
    echo "⚠️  Review warnings before deployment"
    exit 0
else
    print_status "ERROR" "Validation failed with $VALIDATION_ERRORS error(s) and $VALIDATION_WARNINGS warning(s)"
    echo "🛑 Repository is NOT ready for deployment"
    echo ""
    echo "🔧 Required actions before deployment:"
    echo "   1. Commit all changes: git add . && git commit -m \"message\""
    echo "   2. Push to remote: git push origin $BRANCH"
    echo "   3. Re-run this validation script"
    exit 1
fi