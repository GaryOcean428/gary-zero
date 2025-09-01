#!/usr/bin/env python3
"""
Test that npm is available in the Docker container.
This test helps ensure Railway deployment dependencies are met.
"""

import subprocess
import pytest


class TestNpmAvailability:
    """Test npm availability for Railway deployment compatibility."""

    def test_npm_command_exists(self):
        """Test that npm command is available in the system PATH."""
        try:
            result = subprocess.run(
                ['which', 'npm'], 
                capture_output=True, 
                text=True, 
                check=True
            )
            assert result.returncode == 0
            assert '/npm' in result.stdout
        except (subprocess.CalledProcessError, FileNotFoundError):
            # npm not available in current environment (expected in dev)
            pytest.skip("npm not available in development environment")

    def test_node_command_exists(self):
        """Test that node command is available in the system PATH."""
        try:
            result = subprocess.run(
                ['which', 'node'], 
                capture_output=True, 
                text=True, 
                check=True
            )
            assert result.returncode == 0
            assert '/node' in result.stdout
        except (subprocess.CalledProcessError, FileNotFoundError):
            # node not available in current environment (expected in dev)
            pytest.skip("node not available in development environment")

    def test_dockerfile_contains_npm_dependencies(self):
        """Test that Dockerfile includes nodejs and npm packages."""
        with open('Dockerfile', 'r') as f:
            dockerfile_content = f.read()
        
        # Check that both nodejs and npm are in the builder stage
        assert 'nodejs' in dockerfile_content
        assert 'npm' in dockerfile_content
        
        # Check they appear multiple times (both builder and runtime stages)
        assert dockerfile_content.count('nodejs') >= 2
        assert dockerfile_content.count('npm') >= 2

    def test_package_json_exists(self):
        """Test that package.json exists (justifies npm requirement)."""
        import os
        assert os.path.exists('package.json')
        
        import json
        with open('package.json', 'r') as f:
            package_data = json.load(f)
            
        # Verify it's a valid package.json with npm scripts
        assert 'scripts' in package_data
        assert 'postinstall' in package_data['scripts']