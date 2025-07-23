#!/bin/bash

# Git Status Check Script
# Ensures no uncommitted changes exist before deployment
# Part of the Git workflow improvement implementation

set -e

echo "🔍 Checking Git repository status..."

# Check if we're in a git repository
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    echo "❌ ERROR: Not in a Git repository"
    exit 1
fi

# Check for uncommitted changes
if ! git diff-index --quiet HEAD --; then
    echo "❌ ERROR: Uncommitted changes detected!"
    echo ""
    echo "📋 Modified files:"
    git diff-index --name-only HEAD --
    echo ""
    echo "🔧 Please commit your changes before proceeding:"
    echo "   git add ."
    echo "   git commit -m \"Your commit message\""
    echo "   git push origin $(git branch --show-current)"
    exit 1
fi

# Check for untracked files (excluding common ignore patterns)
UNTRACKED_FILES=$(git ls-files --others --exclude-standard)
if [ -n "$UNTRACKED_FILES" ]; then
    echo "⚠️  WARNING: Untracked files detected:"
    echo "$UNTRACKED_FILES"
    echo ""
    echo "💡 Consider adding these files to .gitignore or commit them if needed"
fi

# Check if local branch is ahead of remote
BRANCH=$(git branch --show-current)
if git rev-list --count origin/$BRANCH..$BRANCH > /dev/null 2>&1; then
    AHEAD_COUNT=$(git rev-list --count origin/$BRANCH..$BRANCH)
    if [ "$AHEAD_COUNT" -gt 0 ]; then
        echo "⚠️  WARNING: Local branch is $AHEAD_COUNT commits ahead of remote"
        echo "🔧 Consider pushing your changes:"
        echo "   git push origin $BRANCH"
    fi
fi

echo "✅ Git repository status is clean"
exit 0