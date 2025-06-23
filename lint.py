#!/usr/bin/env python3
"""
Linting script for the zero project.
Provides convenient commands to run various linters and formatters.
"""

import argparse
import subprocess
import sys


def run_command(cmd: list[str], description: str) -> int:
    """Run a command and return its exit code."""
    print(f"\n🔧 {description}")
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=False, check=False)
    if result.returncode == 0:
        print(f"✅ {description} completed successfully")
    else:
        print(f"❌ {description} failed with exit code {result.returncode}")
    return result.returncode


def main():
    parser = argparse.ArgumentParser(description="Run linters and formatters")
    parser.add_argument(
        "action",
        choices=[
            "format",
            "check",
            "fix",
            "stats",
            "all",
            "black",
            "ruff",
            "mypy",
            "pylint",
            "frontend",
            "markdown",
            "css",
            "html",
        ],
        help="Action to perform",
    )
    parser.add_argument("--path", default="zero/", help="Path to lint (default: python/)")

    args = parser.parse_args()

    exit_codes = []

    if args.action == "format" or args.action == "all":
        # Format code with Black
        exit_codes.append(run_command(["black", args.path], "Formatting code with Black"))

        # Fix issues with Ruff
        exit_codes.append(
            run_command(
                ["ruff", "check", args.path, "--fix", "--unsafe-fixes"],
                "Auto-fixing issues with Ruff",
            )
        )

    elif args.action == "check" or args.action == "all":
        # Check with Ruff
        exit_codes.append(run_command(["ruff", "check", args.path], "Checking code with Ruff"))

        # Check with MyPy
        exit_codes.append(run_command(["mypy", args.path], "Type checking with MyPy"))

    elif args.action == "fix":
        # Auto-fix what we can
        exit_codes.append(
            run_command(
                ["ruff", "check", args.path, "--fix", "--unsafe-fixes"],
                "Auto-fixing issues with Ruff",
            )
        )

        exit_codes.append(run_command(["black", args.path], "Formatting code with Black"))

    elif args.action == "stats":
        # Show statistics
        exit_codes.append(
            run_command(
                ["ruff", "check", args.path, "--statistics"],
                "Showing linting statistics",
            )
        )

    elif args.action == "black":
        exit_codes.append(run_command(["black", args.path], "Formatting with Black"))

    elif args.action == "ruff":
        exit_codes.append(run_command(["ruff", "check", args.path], "Checking with Ruff"))

    elif args.action == "mypy":
        exit_codes.append(run_command(["mypy", args.path], "Type checking with MyPy"))

    elif args.action == "pylint":
        exit_codes.append(run_command(["pylint", args.path], "Checking with Pylint"))

    elif args.action == "frontend" or args.action == "all":
        # Frontend linting
        exit_codes.append(run_command(["markdownlint", "docs/", "*.md"], "Checking Markdown files"))
        exit_codes.append(run_command(["stylelint", "webui/**/*.css"], "Checking CSS files"))
        exit_codes.append(run_command(["htmlhint", "webui/**/*.html"], "Checking HTML files"))

    elif args.action == "markdown":
        exit_codes.append(run_command(["markdownlint", "docs/", "*.md"], "Checking Markdown files"))

    elif args.action == "css":
        exit_codes.append(run_command(["stylelint", "webui/**/*.css"], "Checking CSS files"))

    elif args.action == "html":
        exit_codes.append(run_command(["htmlhint", "webui/**/*.html"], "Checking HTML files"))

    # Summary
    failed_count = sum(1 for code in exit_codes if code != 0)
    total_count = len(exit_codes)

    print(f"\n📊 Summary: {total_count - failed_count}/{total_count} tasks completed successfully")

    if failed_count > 0:
        print(f"⚠️  {failed_count} task(s) had issues")
        sys.exit(1)
    else:
        print("🎉 All tasks completed successfully!")


if __name__ == "__main__":
    main()
