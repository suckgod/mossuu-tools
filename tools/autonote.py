#!/usr/bin/env python3
"""
AutoNote - Smart note organizer

Usage:
    python autonote.py [notes_dir] [--dry-run] [--move] [--verbose]

Options:
    notes_dir    Directory containing markdown notes (default: ./notes)
    --dry-run    Show what would be done without making changes
    --move       Move files to categorized folders (default: False, just generate index)
    --verbose    Print detailed logs
    --version    Show version info
"""
import os
import sys
import re
import json
import argparse
from datetime import datetime
from pathlib import Path

__version__ = "1.1.0"

# Ensure UTF-8 output
if sys.version_info[0] < 3:
    reload(sys)
    sys.setdefaultencoding('utf-8')

class NoteOrganizer:
    def __init__(self, notes_dir, dry_run=False, move_files=False, verbose=False):
        self.notes_dir = Path(notes_dir)
        self.index_file = self.notes_dir / "INDEX.md"
        self.dry_run = dry_run
        self.move_files = move_files
        self.verbose = verbose
        self.categories = {
            "ideas": "#ideas",
            "tasks": "#tasks",
            "projects": "#projects",
            "reference": "#reference",
            "daily": "#daily"
        }

    def log(self, msg):
        """Print message if verbose"""
        if self.verbose:
            print(msg)

    def scan_notes(self):
        """扫描所有笔记文件"""
        notes = []
        files = list(self.notes_dir.glob("*.md"))
        self.log(f"Scanning {len(files)} markdown files...")

        for file in files:
            try:
                content = file.read_text(encoding='utf-8')
                notes.append({
                    "file": file.name,
                    "path": str(file),
                    "content": content,
                    "size": len(content),
                    "modified": file.stat().st_mtime
                })
            except Exception as e:
                self.log(f"Warning: Could not read {file}: {e}")

        self.log(f"Scanned {len(notes)} notes successfully")
        return notes

    def categorize_note(self, content):
        """根据内容分类笔记（不区分大小写）"""
        content_lower = content.lower()
        if "idea" in content_lower or "concept" in content_lower:
            return "ideas"
        elif "todo" in content_lower or "- [ ]" in content_lower:
            return "tasks"
        elif "project" in content_lower:
            return "projects"
        elif any(x in content_lower for x in ["ref:", "reference:", "see:", "link:", "url:"]):
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

        if self.dry_run:
            self.log("[DRY RUN] Would generate index at: " + str(self.index_file))
            for cat, cat_notes in categorized.items():
                if cat_notes:
                    self.log(f"  - Category '{cat}': {len(cat_notes)} notes")
            return

        with open(self.index_file, "w", encoding='utf-8') as f:
            f.write("# Notes Index\n\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

            total = 0
            for cat, cat_notes in categorized.items():
                if cat_notes:
                    f.write(f"## {cat.title()}\n\n")
                    for note in sorted(cat_notes, key=lambda x: x['file']):
                        f.write(f"- [{note['file']}]({note['file']}) - {note['size']} chars\n")
                    f.write("\n")
                    total += len(cat_notes)

            f.write(f"**Total:** {total} notes across {len([c for c in categorized.values() if c])} categories\n")

        self.log(f"Index generated: {self.index_file} ({total} notes)")

    def move_to_folders(self, notes):
        """移动文件到对应分类文件夹（可选功能）"""
        moved = 0
        for note in notes:
            cat = self.categorize_note(note["content"])
            cat_dir = self.notes_dir / cat
            cat_dir.mkdir(exist_ok=True)

            src = Path(note["path"])
            dst = cat_dir / src.name

            if src.parent != cat_dir:
                if self.dry_run:
                    self.log(f"[DRY RUN] Would move {src.name} -> {cat}/")
                else:
                    try:
                        src.rename(dst)
                        self.log(f"Moved {src.name} -> {cat}/")
                        moved += 1
                    except Exception as e:
                        self.log(f"Error moving {src.name}: {e}")

        if moved > 0:
            self.log(f"Moved {moved} files to category folders")
        return moved

    def run(self):
        """执行整理流程"""
        self.log(f"Scanning: {self.notes_dir}")

        notes = self.scan_notes()
        self.log(f"Found {len(notes)} notes")

        notes = self.remove_duplicates(notes)
        self.log(f"After dedup: {len(notes)} unique notes")

        self.generate_index(notes)

        if self.move_files:
            moved = self.move_to_folders(notes)
            if moved > 0:
                print(f"Moved {moved} files to category folders")

        print(f"✅ Done! Index: {self.index_file}")

def main():
    parser = argparse.ArgumentParser(
        description="AutoNote - Smart note organizer with categorization and deduplication",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                    # Scan ./notes directory
  %(prog)s /path/to/notes     # Scan custom directory
  %(prog)s --dry-run          # Preview changes without modifying files
  %(prog)s --move             # Move files to category folders
  %(prog)s --move --dry-run   # See where files would be moved
        """
    )
    parser.add_argument(
        "notes_dir",
        nargs="?",
        default="./notes",
        help="Directory containing markdown notes (default: ./notes)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without making changes"
    )
    parser.add_argument(
        "--move",
        action="store_true",
        help="Move files to categorized folders (default: only generate index)"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print detailed logs"
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"autonote {__version__}",
        help="Show version information"
    )

    args = parser.parse_args()

    try:
        organizer = NoteOrganizer(
            notes_dir=args.notes_dir,
            dry_run=args.dry_run,
            move_files=args.move,
            verbose=args.verbose
        )
        organizer.run()
    except FileNotFoundError:
        print(f"Error: Directory '{args.notes_dir}' not found", file=sys.stderr)
        sys.exit(1)
    except PermissionError as e:
        print(f"Error: Permission denied - {e}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nInterrupted.", file=sys.stderr)
        sys.exit(130)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
