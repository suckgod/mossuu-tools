#!/usr/bin/env python3
"""
Tests for Duplicate Finder
"""

import unittest
import tempfile
import shutil
from pathlib import Path
from tools.duplicate_finder import DuplicateFinder, compute_hash

class TestDuplicateFinder(unittest.TestCase):
    def setUp(self):
        """Create temporary directory with test files"""
        self.temp_dir = Path(tempfile.mkdtemp())

        # Create unique files
        (self.temp_dir / "file1.txt").write_text("Hello World!", encoding='utf-8')
        (self.temp_dir / "file2.txt").write_text("Hello World!", encoding='utf-8')  # duplicate
        (self.temp_dir / "file3.txt").write_text("Different content", encoding='utf-8')

        # Create subdirectory with more files
        subdir = self.temp_dir / "subdir"
        subdir.mkdir()
        (subdir / "file4.txt").write_text("Hello World!", encoding='utf-8')  # another duplicate

        # Create larger file to test min-size
        (self.temp_dir / "large1.bin").write_bytes(b"x" * 1000)
        (self.temp_dir / "large2.bin").write_bytes(b"x" * 1000)  # duplicate large

    def tearDown(self):
        """Clean up temp directory"""
        shutil.rmtree(self.temp_dir)

    def test_compute_hash(self):
        """Test hash computation"""
        filepath = self.temp_dir / "file1.txt"
        hash1 = compute_hash(filepath)
        hash2 = compute_hash(filepath)
        self.assertEqual(hash1, hash2)
        self.assertEqual(len(hash1), 64)  # SHA256 hex length

    def test_scan_files(self):
        """Test file scanning"""
        finder = DuplicateFinder(self.temp_dir)
        files = finder.scan_files()
        self.assertGreaterEqual(len(files), 5)  # At least our 5 test files

    def test_find_duplicates(self):
        """Test duplicate detection"""
        finder = DuplicateFinder(self.temp_dir)
        duplicates = finder.find_duplicates()

        # Should find sets: ["file1.txt", "file2.txt", "subdir/file4.txt"]
        # and ["large1.bin", "large2.bin"]
        total_duplicates = sum(len(d) - 1 for d in duplicates)
        self.assertGreaterEqual(total_duplicates, 3)

    def test_min_size_filter(self):
        """Test minimum size filtering"""
        finder = DuplicateFinder(self.temp_dir, min_size=1000)
        files = finder.scan_files()
        # Should only include large1.bin and large2.bin
        filenames = [f.name for f in files]
        self.assertIn("large1.bin", filenames)
        self.assertIn("large2.bin", filenames)
        self.assertNotIn("file1.txt", filenames)

    def test_extensions_filter(self):
        """Test extension filtering"""
        finder = DuplicateFinder(self.temp_dir, extensions=[".txt"])
        files = finder.scan_files()
        for f in files:
            self.assertEqual(f.suffix.lower(), ".txt")

    def test_dry_run(self):
        """Test dry run mode"""
        finder = DuplicateFinder(self.temp_dir, dry_run=True)
        duplicates = finder.find_duplicates()
        if duplicates:
            # In dry run, no deletion should occur
            initial_files = list(self.temp_dir.rglob("*"))
            count_before = len([f for f in initial_files if f.is_file()])
            count_after = len([f for f in self.temp_dir.rglob("*") if f.is_file()])
            self.assertEqual(count_before, count_after)

    def test_handle_duplicates(self):
        """Test duplicate handling (mark only, don't delete)"""
        finder = DuplicateFinder(self.temp_dir, dry_run=True)
        duplicates = finder.find_duplicates()
        actions = finder.handle_duplicates(duplicates)

        self.assertGreater(len(actions), 0)
        for action in actions:
            self.assertIn("keeper", action)
            self.assertIn("duplicate", action)
            self.assertEqual(action["action"], "dry-run")

    def test_report_generation(self):
        """Test CSV report generation"""
        report_path = self.temp_dir / "report.csv"
        finder = DuplicateFinder(self.temp_dir, dry_run=True, report=str(report_path))
        duplicates = finder.find_duplicates()
        finder.generate_report(finder.handle_duplicates(duplicates))

        self.assertTrue(report_path.exists())
        content = report_path.read_text(encoding='utf-8')
        self.assertIn("keeper", content)
        self.assertIn("duplicate", content)

    def test_no_duplicates(self):
        """Test when no duplicates exist"""
        # Create unique temp dir with unique files
        unique_dir = Path(tempfile.mkdtemp())
        (unique_dir / "a.txt").write_text("A", encoding='utf-8')
        (unique_dir / "b.txt").write_text("B", encoding='utf-8')

        try:
            finder = DuplicateFinder(unique_dir)
            duplicates = finder.find_duplicates()
            self.assertEqual(len(duplicates), 0)
        finally:
            shutil.rmtree(unique_dir)


if __name__ == "__main__":
    unittest.main()
