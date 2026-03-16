#!/usr/bin/env python3
"""
Tests for AutoNote
"""

import unittest
import tempfile
import shutil
from pathlib import Path
from tools.autonote import NoteOrganizer

class TestAutoNote(unittest.TestCase):
    def setUp(self):
        """Create temporary directory with test notes"""
        self.temp_dir = Path(tempfile.mkdtemp())
        # Create test notes
        (self.temp_dir / "note1.md").write_text(
            "# Idea\nThis is a great idea for a new project.\n", encoding='utf-8'
        )
        (self.temp_dir / "note2.md").write_text(
            "- [ ] Complete the report\n- [ ] Send email\n", encoding='utf-8'
        )
        (self.temp_dir / "note3.md").write_text(
            "Working on the mossuu-tools project.\n", encoding='utf-8'
        )
        (self.temp_dir / "note4.md").write_text(
            "Reference: see the documentation at example.com\n", encoding='utf-8'
        )
        (self.temp_dir / "daily.md").write_text(
            "Today I learned about AI assistants.\n", encoding='utf-8'
        )

    def tearDown(self):
        """Clean up temp directory"""
        shutil.rmtree(self.temp_dir)

    def test_scan_notes(self):
        """Test note scanning"""
        organizer = NoteOrganizer(self.temp_dir)
        notes = organizer.scan_notes()
        self.assertEqual(len(notes), 5)
        self.assertTrue(all('content' in n for n in notes))

    def test_categorize_note(self):
        """Test note categorization"""
        organizer = NoteOrganizer(self.temp_dir)

        idea_note = "I have a new idea for automation."
        self.assertEqual(organizer.categorize_note(idea_note), "ideas")

        task_note = "- [ ] Do something important"
        self.assertEqual(organizer.categorize_note(task_note), "tasks")

        project_note = "This project is going well."
        self.assertEqual(organizer.categorize_note(project_note), "projects")

        ref_note = "Reference: check this link"
        self.assertEqual(organizer.categorize_note(ref_note), "reference")

        daily_note = "Just a regular daily note."
        self.assertEqual(organizer.categorize_note(daily_note), "daily")

    def test_remove_duplicates(self):
        """Test duplicate removal"""
        organizer = NoteOrganizer(self.temp_dir)
        notes = [
            {"content": "Same content here", "size": 100},
            {"content": "Same content here", "size": 100},
            {"content": "Different content", "size": 50},
        ]
        unique = organizer.remove_duplicates(notes)
        self.assertEqual(len(unique), 2)

    def test_generate_index(self):
        """Test index generation"""
        organizer = NoteOrganizer(self.temp_dir, dry_run=False)
        notes = organizer.scan_notes()
        organizer.generate_index(notes)

        self.assertTrue(organizer.index_file.exists())
        content = organizer.index_file.read_text(encoding='utf-8')
        self.assertIn("# Notes Index", content)
        self.assertIn("Total:", content)

    def test_dry_run(self):
        """Test dry run mode doesn't create files"""
        organizer = NoteOrganizer(self.temp_dir, dry_run=True)
        notes = organizer.scan_notes()
        organizer.generate_index(notes)

        self.assertFalse(organizer.index_file.exists())

    def test_move_files(self):
        """Test moving files to category folders"""
        organizer = NoteOrganizer(self.temp_dir, move_files=True, dry_run=False)
        notes = organizer.scan_notes()
        organizer.generate_index(notes)  # Generate index first
        moved = organizer.move_to_folders(notes)

        # Check category directories were created
        self.assertTrue((self.temp_dir / "ideas").exists())
        self.assertTrue((self.temp_dir / "tasks").exists())
        self.assertTrue((self.temp_dir / "projects").exists())
        self.assertTrue((self.temp_dir / "reference").exists())
        self.assertTrue((self.temp_dir / "daily").exists())

        # Files should be moved (5 original files)
        moved_files = list(self.temp_dir.glob("*/*.md"))
        self.assertEqual(len(moved_files), 5)


if __name__ == "__main__":
    unittest.main()
