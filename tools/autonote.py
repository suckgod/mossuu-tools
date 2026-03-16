#!/usr/bin/env python3
"""
AutoNote - Smart note organizer
"""

import os
import sys
import re
import json
from datetime import datetime
from pathlib import Path

# Ensure UTF-8 output
if sys.version_info[0] < 3:
    reload(sys)
    sys.setdefaultencoding('utf-8')

class NoteOrganizer:
    def __init__(self, notes_dir):
        self.notes_dir = Path(notes_dir)
        self.index_file = self.notes_dir / "INDEX.md"
        self.categories = {
            "ideas": "#ideas",
            "tasks": "#tasks",
            "projects": "#projects",
            "reference": "#reference",
            "daily": "#daily"
        }

    def scan_notes(self):
        """扫描所有笔记文件"""
        notes = []
        for file in self.notes_dir.glob("*.md"):
            content = file.read_text(encoding='utf-8')
            notes.append({
                "file": file.name,
                "path": str(file),
                "content": content,
                "size": len(content),
                "modified": file.stat().st_mtime
            })
        return notes

    def categorize_note(self, content):
        """根据内容分类笔记"""
        content_lower = content.lower()
        if "idea" in content_lower or "concept" in content_lower:
            return "ideas"
        elif "todo" in content_lower or "- [ ]" in content_lower:
            return "tasks"
        elif "project" in content_lower:
            return "projects"
        elif any(x in content_lower for x in ["ref:", "see:", "link:"]):
            return "reference"
        else:
            return "daily"

    def remove_duplicates(self, notes):
        """去重：基于内容相似度"""
        seen_content = set()
        unique = []
        for note in notes:
            # 简单去重：取前100字符作为指纹
            fingerprint = note["content"][:100].strip()
            if fingerprint and fingerprint not in seen_content:
                seen_content.add(fingerprint)
                unique.append(note)
        return unique

    def generate_index(self, notes):
        """生成索引文件"""
        categorized = {cat: [] for cat in self.categories.keys()}

        for note in notes:
            cat = self.categorize_note(note["content"])
            categorized[cat].append(note)

        with open(self.index_file, "w", encoding='utf-8') as f:
            f.write("# Notes Index\n\n")
            f.write(f"Generated: {datetime.now()}\n\n")

            for cat, cat_notes in categorized.items():
                if cat_notes:
                    f.write(f"## {cat.title()}\n\n")
                    for note in cat_notes:
                        f.write(f"- [{note['file']}]({note['file']}) - {note['size']} chars\n")
                    f.write("\n")

    def run(self):
        """执行整理流程"""
        print(f"Scanning: {self.notes_dir}")
        notes = self.scan_notes()
        print(f"Found {len(notes)} notes")

        notes = self.remove_duplicates(notes)
        print(f"After dedup: {len(notes)}")

        self.generate_index(notes)
        print(f"Index generated: {self.index_file}")

        # 可选：自动移动文件到分类文件夹
        # self.move_to_folders(notes)

if __name__ == "__main__":
    import sys
    notes_path = sys.argv[1] if len(sys.argv) > 1 else "./notes"
    organizer = NoteOrganizer(notes_path)
    organizer.run()
