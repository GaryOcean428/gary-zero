#!/usr/bin/env python3
"""
Regenerate requirements.txt from requirements.in using uv
This ensures all dependencies are properly synchronized
"""

import os
import subprocess
import sys


def regenerate_requirements():
    """Regenerate requirements.txt from requirements.in using uv."""

    # Check if uv is installed
    try:
        subprocess.run(['uv', '--version'], check=True, capture_output=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("Error: 'uv' is not installed. Installing now...")
        subprocess.run([sys.executable, '-m', 'pip', 'install', 'uv'], check=True)

    # Check if requirements.in exists
    if not os.path.exists('requirements.in'):
        print("Error: requirements.in not found!")
        sys.exit(1)

    print("Regenerating requirements.txt from requirements.in...")

    try:
        # Use uv to compile requirements
        result = subprocess.run(
            ['uv', 'pip', 'compile', 'requirements.in', '-o', 'requirements.txt'],
            check=True,
            capture_output=True,
            text=True
        )
        print("Successfully regenerated requirements.txt")
        print(f"Output: {result.stdout}")

        # Verify FastAPI is included
        with open('requirements.txt') as f:
            content = f.read()
            if 'fastapi' not in content.lower():
                print("WARNING: FastAPI not found in regenerated requirements.txt!")
                print("This may indicate an issue with dependency resolution.")
            else:
                print("✅ FastAPI dependencies successfully included")

    except subprocess.CalledProcessError as e:
        print(f"Error regenerating requirements: {e}")
        print(f"stderr: {e.stderr}")
        sys.exit(1)

if __name__ == "__main__":
    regenerate_requirements()
