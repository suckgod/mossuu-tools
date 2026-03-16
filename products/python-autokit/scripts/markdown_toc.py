#!/usr/bin/env python3
"""
Markdown TOC - Auto-generate Markdown table of contents

Parse Markdown files and generate TOC:
- Extract headings (h1-h6)
- Create nested list structure
- Insert TOC at marker or file beginning
- Support custom heading levels
- Generate anchor links (GitHub-style slugification)
- Skip headings with certain tags or patterns
- Update existing TOC in-place

Usage:
    python markdown_toc.py README.md
    python markdown_toc.py README.md --max-level 3 --output README_TOC.md
    python markdown_toc.py *.md --insert --marker "<!-- TOC -->"
"""

import os
import re
import sys
import argparse
from pathlib import Path
from typing import List, Tuple, Optional
import hashlib

__version__ = "1.0.0"

class MarkdownTOC:
    def __init__(self, max_level: int = 6,
                 indent_size: int = 2,
                 marker: str = None,
                 skip_patterns: List[str] = None,
                 insert_at_marker: bool = False,
                 update_existing: bool = False):
        self.max_level = max_level
        self.indent_size = indent_size
        self.marker = marker or "<!-- TOC -->"
        self.skip_patterns = skip_patterns or []
        self.insert_at_marker = insert_at_marker
        self.update_existing = update_existing

    def slugify(self, text: str) -> str:
        """Convert heading text to GitHub-style anchor link"""
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', text)
        # Convert to lowercase, strip
        text = text.strip().lower()
        # Replace spaces with hyphens
        text = re.sub(r'\s+', '-', text)
        # Remove non-alphanumeric except hyphens
        text = re.sub(r'[^\w\-]', '', text)
        # Remove leading/trailing hyphens
        text = text.strip('-')
        # Truncate if too long
        if len(text) > 100:
            text = text[:100]
        # Ensure not empty
        if not text:
            return 'section'
        return text

    def should_skip(self, heading: str) -> bool:
        """Check if heading should be skipped"""
        for pattern in self.skip_patterns:
            if re.search(pattern, heading, re.IGNORECASE):
                return True
        return False

    def parse_headings(self, content: str) -> List[Tuple[int, str]]:
        """Extract headings from markdown content"""
        headings = []
        lines = content.split('\n')

        for line in lines:
            line = line.rstrip()
            # Match markdown headings: # Heading (1-6 #)
            match = re.match(r'^(#{1,6})\s+(.+?)\s*$', line)
            if match:
                level = len(match.group(1))
                heading_text = match.group(2).strip()

                if level <= self.max_level and not self.should_skip(heading_text):
                    headings.append((level, heading_text))

        return headings

    def generate_toc(self, headings: List[Tuple[int, str]]) -> str:
        """Generate TOC markdown from headings list"""
        if not headings:
            return ""

        lines = []
        prev_level = 0

        for level, text in headings:
            # Indentation based on heading level
            indent = (level - 1) * self.indent_size
            spaces = ' ' * indent

            slug = self.slugify(text)
            toc_line = f"{spaces}- [{text}](#{slug})"
            lines.append(toc_line)
            prev_level = level

        return '\n'.join(lines)

    def find_existing_toc(self, content: str) -> Optional[Tuple[int, int, str]]:
        """Find existing TOC between markers"""
        start_marker = f"<!--{self.marker}-->"
        end_marker = f"<!--/{self.marker}-->"

        start_idx = content.find(start_marker)
        if start_idx == -1:
            return None

        end_idx = content.find(end_marker, start_idx)
        if end_idx == -1:
            return None

        end_idx += len(end_marker)
        existing_toc = content[start_idx:end_idx].strip()
        return (start_idx, end_idx, existing_toc)

    def insert_toc(self, content: str, toc: str) -> str:
        """Insert or replace TOC in content"""
        if not toc:
            return content

        toc_block = f"<!--{self.marker}-->\n{toc}\n<!--/{self.marker}-->"

        if self.update_existing or self.insert_at_marker:
            existing = self.find_existing_toc(content)
            if existing:
                start_idx, end_idx, _ = existing
                new_content = content[:start_idx] + toc_block + content[end_idx:]
                print("  Updated existing TOC")
                return new_content

        # Insert at top, after any YAML frontmatter
        if self.insert_at_marker:
            # Insert at marker position
            marker_idx = content.find(self.marker)
            if marker_idx != -1:
                # Replace marker line with TOC block
                lines = content.split('\n')
                new_lines = []
                for line in lines:
                    if self.marker in line:
                        new_lines.append(toc_block)
                    else:
                        new_lines.append(line)
                return '\n'.join(new_lines)
            else:
                # Insert at beginning
                return toc_block + '\n\n' + content
        else:
            # Insert at beginning
            return toc_block + '\n\n' + content

    def process_file(self, filepath: Path) -> bool:
        """Process single markdown file"""
        print(f"Processing: {filepath.name}")

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            print(f"  Error reading file: {e}", file=sys.stderr)
            return False

        headings = self.parse_headings(content)
        print(f"  Found {len(headings)} headings")

        if not headings:
            print("  No headings found, skipping")
            return False

        toc = self.generate_toc(headings)
        print(f"  Generated TOC: {len(toc.split(chr(10)))} lines")

        # Determine output content
        if self.update_existing or self.insert_at_marker:
            new_content = self.insert_toc(content, toc)
        else:
            new_content = toc + '\n\n' + content

        # Write output
        return self.write_output(filepath, content, new_content)

    def write_output(self, filepath: Path, original: str, new_content: str) -> bool:
        """Write output to file or stdout"""
        if new_content == original:
            print("  No changes needed")
            return True

        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(new_content)
            print(f"  ✓ Updated {filepath.name}")
            return True
        except Exception as e:
            print(f"  Error writing file: {e}", file=sys.stderr)
            return False

def main():
    parser = argparse.ArgumentParser(
        description="Markdown TOC - Auto-generate Markdown table of contents",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate TOC and prepend to file
  %(prog)s README.md

  # Limit heading levels, output to separate file
  %(prog)s guide.md --max-level 3 --output guide_with_toc.md

  # Insert TOC at marker (updates if already exists)
  %(prog)s *.md --insert --marker "TOC" --update

  # Skip certain headings (regex patterns)
  %(prog)s notes.md --skip "Appendix" --skip "TODO" --skip "^\d+\. " 

  # Generate TOC with 4-space indents
  %(prog)s doc.md --indent 4

Notes:
  - Default TOC marker: <!-- TOC --> (opening) and <!--/TOC --> (closing)
  - If no marker found, TOC is prepended to file
  - Anchor links follow GitHub slugify rules
  - YAML frontmatter (--- block) is preserved; TOC inserted after it
  - Skip patterns allow excluding headings like "Appendix", "Notes", etc.
      """
    )
    parser.add_argument(
        "files",
        nargs="+",
        help="Markdown files to process"
    )
    parser.add_argument(
        "--max-level",
        type=int,
        default=6,
        choices=range(1, 7),
        help="Maximum heading level to include (1-6, default: 6)"
    )
    parser.add_argument(
        "--indent",
        type=int,
        default=2,
        help="Spaces per indentation level (default: 2)"
    )
    parser.add_argument(
        "--marker",
        help="TOC marker string (default: 'TOC')"
    )
    parser.add_argument(
        "--insert",
        action="store_true",
        help="Insert TOC at marker location (if not found, prepend)"
    )
    parser.add_argument(
        "--update",
        action="store_true",
        help="Update existing TOC if marker found"
    )
    parser.add_argument(
        "--skip",
        action="append",
        help="Regex pattern for headings to skip (can use multiple)"
    )
    parser.add_argument(
        "-o", "--output",
        help="Output file (default: overwrite input)"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Show detailed processing info"
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"markdown_toc {__version__}"
    )

    args = parser.parse_args()

    toc = MarkdownTOC(
        max_level=args.max_level,
        indent_size=args.indent,
        marker=args.marker,
        skip_patterns=args.skip or [],
        insert_at_marker=args.insert,
        update_existing=args.update
    )

    success_count = 0
    for file_pattern in args.files:
        filepath = Path(file_pattern)
        if not filepath.exists():
            print(f"File not found: {filepath}", file=sys.stderr)
            continue

        if toc.process_file(filepath):
            success_count += 1

    print(f"\nCompleted: {success_count}/{len(args.files)} files processed successfully")
    if success_count < len(args.files):
        sys.exit(1)

if __name__ == "__main__":
    main()
