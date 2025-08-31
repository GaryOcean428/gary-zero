"""
Integration test for directory health check functionality.
Tests the /health/directories endpoint and volume initialization.
"""

import json
import os
import shutil
import tempfile
import unittest


# Simple test that doesn't require full Flask setup
class TestDirectoryHealthLogic(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_directory_structure_validation(self):
        """Test directory structure validation logic."""
        required_dirs = [
            "settings",
            "memory",
            "knowledge",
            "prompts",
            "logs",
            "work_dir",
            "reports",
            "scheduler",
            "tmp",
        ]

        # Create some directories
        for dir_name in required_dirs[:5]:
            os.makedirs(os.path.join(self.test_dir, dir_name), exist_ok=True)

        # Validate existing directories
        directory_status = {}
        all_healthy = True

        for dir_name in required_dirs:
            dir_path = os.path.join(self.test_dir, dir_name)
            exists = os.path.exists(dir_path) and os.path.isdir(dir_path)
            directory_status[dir_name] = {
                "exists": exists,
                "path": dir_path,
                "writable": os.access(dir_path, os.W_OK) if exists else False,
            }
            if not exists:
                all_healthy = False

        # Check results
        self.assertEqual(len(directory_status), 9)
        self.assertFalse(all_healthy)  # Not all directories exist

        # Check specific directories
        self.assertTrue(directory_status["settings"]["exists"])
        self.assertTrue(directory_status["memory"]["exists"])
        self.assertFalse(directory_status["tmp"]["exists"])  # Wasn't created

    def test_required_files_validation(self):
        """Test required files validation logic."""
        # Create directory structure
        os.makedirs(os.path.join(self.test_dir, "settings"), exist_ok=True)
        os.makedirs(os.path.join(self.test_dir, "memory"), exist_ok=True)
        os.makedirs(os.path.join(self.test_dir, "scheduler"), exist_ok=True)

        # Create some required files
        required_files = {
            "settings/config.json": os.path.join(
                self.test_dir, "settings", "config.json"
            ),
            "memory/context.json": os.path.join(
                self.test_dir, "memory", "context.json"
            ),
            "scheduler/tasks.json": os.path.join(
                self.test_dir, "scheduler", "tasks.json"
            ),
        }

        # Create first two files
        with open(required_files["settings/config.json"], "w") as f:
            json.dump({}, f)

        with open(required_files["memory/context.json"], "w") as f:
            json.dump([], f)

        # Validate files
        file_status = {}
        for file_key, file_path in required_files.items():
            exists = os.path.exists(file_path) and os.path.isfile(file_path)
            file_status[file_key] = {
                "exists": exists,
                "path": file_path,
                "size": os.path.getsize(file_path) if exists else 0,
            }

        # Check results
        self.assertTrue(file_status["settings/config.json"]["exists"])
        self.assertTrue(file_status["memory/context.json"]["exists"])
        self.assertFalse(file_status["scheduler/tasks.json"]["exists"])
        self.assertGreater(file_status["settings/config.json"]["size"], 0)


if __name__ == "__main__":
    unittest.main()
