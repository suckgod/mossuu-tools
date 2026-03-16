#!/usr/bin/env python3
"""
Smoke tests for Python AutoKit scripts
Tests: basic import, argument parsing, help output
"""

import unittest
import subprocess
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).parent.parent / "products" / "python-autokit" / "scripts"

class TestAutoKitScripts(unittest.TestCase):
    """Test that all AutoKit scripts are syntactically correct and have proper argument parsing"""

    scripts = [
        'backup_rotator.py',
        'csv_analyzer.py',
        'disk_alerter.py',
        'duplicate_finder.py',
        'excel_formatter.py',
        'json_merger.py',
        'log_watcher.py',
        'markdown_toc.py',
        'smart_rename.py',
        'blog_auto.py',
        'transcript_cleaner.py'
    ]

    def test_scripts_exist(self):
        """All listed scripts should exist"""
        for script in self.scripts:
            path = SCRIPTS_DIR / script
            self.assertTrue(path.exists(), f"Missing script: {script}")

    def test_scripts_importable(self):
        """All scripts should compile without syntax errors"""
        for script in self.scripts:
            path = SCRIPTS_DIR / script
            result = subprocess.run(
                [sys.executable, '-m', 'py_compile', str(path)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True
            )
            self.assertEqual(result.returncode, 0,
                f"Script {script} failed to compile: {result.stderr}")

    def test_help_output(self):
        """All scripts should respond to --help without error"""
        for script in self.scripts:
            path = SCRIPTS_DIR / script
            result = subprocess.run(
                [sys.executable, str(path), '--help'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True
            )
            self.assertEqual(result.returncode, 0,
                f"Script {script} failed --help: {result.stderr}")
            self.assertIn('usage:', result.stdout.lower(),
                f"Script {script} missing usage line")

    def test_version_flag(self):
        """All scripts should support --version"""
        for script in self.scripts:
            path = SCRIPTS_DIR / script
            result = subprocess.run(
                [sys.executable, str(path), '--version'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True
            )
            self.assertEqual(result.returncode, 0,
                f"Script {script} failed --version: {result.stderr}")

if __name__ == '__main__':
    unittest.main()
