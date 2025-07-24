#!/bin/bash

# Markdown Helper Script
# Provides quick commands for common markdown linting operations

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PROJECT_ROOT"

show_help() {
    echo "Markdown Helper Script"
    echo ""
    echo "Usage: $0 [command] [options]"
    echo ""
    echo "Commands:"
    echo "  check           Check all markdown files for issues"
    echo "  fix            Auto-fix all fixable markdown issues"
    echo "  count          Count the number of markdown issues"
    echo "  check-file     Check a specific file (provide filename as argument)"
    echo "  fix-file       Fix a specific file (provide filename as argument)"
    echo "  summary        Show a summary of issue types"
    echo ""
    echo "Examples:"
    echo "  $0 check                              # Check all files"
    echo "  $0 fix                                # Fix all auto-fixable issues"
    echo "  $0 count                              # Show issue count"
    echo "  $0 check-file README.md               # Check specific file"
    echo "  $0 fix-file docs/installation.md      # Fix specific file"
    echo "  $0 summary                            # Show issue summary"
}

count_issues() {
    echo "Counting markdown issues..."
    local count=$(npm run markdown:check 2>&1 | grep -E "^[^>].*:.*MD" | wc -l)
    echo "Total markdown issues: $count"
}

check_all() {
    echo "Checking all markdown files..."
    npm run markdown:check
}

fix_all() {
    echo "Auto-fixing all markdown files..."
    npm run markdown:fix
    echo ""
    echo "✅ Auto-fix complete!"
    count_issues
}

check_file() {
    if [ -z "$1" ]; then
        echo "❌ Error: Please provide a filename"
        echo "Usage: $0 check-file <filename>"
        exit 1
    fi

    echo "Checking file: $1"
    ./node_modules/.bin/markdownlint-cli2 "$1"
}

fix_file() {
    if [ -z "$1" ]; then
        echo "❌ Error: Please provide a filename"
        echo "Usage: $0 fix-file <filename>"
        exit 1
    fi

    echo "Fixing file: $1"
    ./node_modules/.bin/markdownlint-cli2 --fix "$1"
    echo "✅ Fixed: $1"
}

show_summary() {
    echo "Markdown Issues Summary:"
    echo "========================"

    # Get all issues and count by rule
    npm run markdown:check 2>&1 | grep -E "^[^>].*:.*MD" | \
    sed 's/.*\(MD[0-9][0-9][0-9]\).*/\1/' | \
    sort | uniq -c | sort -nr | head -10

    echo ""
    echo "Top 10 most common markdown issues shown above."
    echo "Use 'npm run markdown:fix' to auto-fix many of these."
}

# Main command handling
case "${1:-}" in
    "check")
        check_all
        ;;
    "fix")
        fix_all
        ;;
    "count")
        count_issues
        ;;
    "check-file")
        check_file "$2"
        ;;
    "fix-file")
        fix_file "$2"
        ;;
    "summary")
        show_summary
        ;;
    "help"|"--help"|"-h"|"")
        show_help
        ;;
    *)
        echo "❌ Unknown command: $1"
        echo ""
        show_help
        exit 1
        ;;
esac
