#!/usr/bin/env python3
"""
Smart Rename - Batch file renaming with patterns

A robust tool for renaming multiple files with:
- Sequential numbering
- Date/timestamp prefixes
- Regex pattern replacements
- Case conversion
- Extension changes

Usage examples:
    python smart_rename.py "photo_{:03d}.jpg" *.jpg
    python smart_rename.py "IMG_*.jpg" --regex "IMG_(\\d+)" "photo_\\1"
    python smart_rename.py --add-date --format "{date}_{name}"
"""

import os
import re
import sys
import argparse
from datetime import datetime
from pathlib import Path

__version__ = "1.0.0"

class SmartRename:
    def __init__(self, pattern, files, regex=None, replace=None,
                 add_date=False, add_time=False, case=None,
                 dry_run=False, verbose=False):
        self.pattern = pattern
        self.files = [Path(f) for f in files if Path(f).is_file()]
        self.regex = regex
        self.replace = replace
        self.add_date = add_date
        self.add_time = add_time
        self.case = case  # 'upper', 'lower', 'title'
        self.dry_run = dry_run
        self.verbose = verbose
        self.renamed = []

    def log(self, msg):
        if self.verbose:
            print(msg)

    def generate_new_name(self, old_path, index):
        """Generate new filename based on pattern and options"""
        old_name = old_path.stem
        ext = old_path.suffix

        # Apply regex substitution first
        if self.regex and self.replace:
            new_stem = re.sub(self.regex, self.replace, old_name)
        else:
            new_stem = self.pattern.format(i=index+1, n=old_name, name=old_name)

        # Add date/time prefix
        prefix = ""
        if self.add_date:
            prefix += datetime.now().strftime("%Y-%m-%d_")
        if self.add_time:
            prefix += datetime.now().strftime("%H%M%S_")
        new_stem = prefix + new_stem

        # Case conversion
        if self.case == 'upper':
            new_stem = new_stem.upper()
        elif self.case == 'lower':
            new_stem = new_stem.lower()
        elif self.case == 'title':
            new_stem = new_stem.title()

        # Avoid empty names
        if not new_stem:
            new_stem = f"file_{index+1}"

        return new_stem + ext

    def validate_new_name(self, new_path, existing_files):
        """Check if new filename is valid and doesn't conflict"""
        if new_path.exists():
            return False, f"Target already exists: {new_path.name}"
        if '/' in new_path.name or '\\' in new_path.name:
            return False, "Filename contains path separators"
        if len(new_path.name) > 255:
            return False, "Filename too long"
        # Check for duplicates among planned renames
        if new_path.name in existing_files:
            return False, f"Duplicate target: {new_path.name}"
        return True, "OK"

    def run(self):
        """Main execution"""
        if not self.files:
            print("Error: No files to rename", file=sys.stderr)
            return []

        print(f"Processing {len(self.files)} files...")
        planned_renames = []

        for idx, old_path in enumerate(self.files):
            try:
                new_stem = self.generate_new_name(old_path, idx)
                new_path = old_path.parent / new_stem

                valid, msg = self.validate_new_name(new_path, [p[1].name for p in planned_renames])
                if not valid:
                    print(f"  Skipping {old_path.name}: {msg}")
                    continue

                planned_renames.append((old_path, new_path))
            except Exception as e:
                print(f"  Error processing {old_path.name}: {e}")

        # Show preview
        print("\n" + "="*60)
        print("PREVIEW")
        print("="*60)
        for old, new in planned_renames:
            print(f"  {old.name:40} -> {new.name}")

        if self.dry_run:
            print(f"\n[Dry run] Would rename {len(planned_renames)} files")
            return []

        # Confirm
        if planned_renames:
            response = input(f"\nRename {len(planned_renames)} files? (y/N): ").lower().strip()
            if response != 'y':
                print("Cancelled.")
                return []

        # Execute
        for old, new in planned_renames:
            try:
                old.rename(new)
                self.renamed.append((old, new))
                self.log(f"Renamed: {old.name} -> {new.name}")
            except Exception as e:
                print(f"  Failed: {old.name} -> {new.name}: {e}")

        print(f"\n✅ Renamed {len(self.renamed)} files successfully")
        return self.renamed


def parse_args():
    parser = argparse.ArgumentParser(
        description="Smart Rename - Batch rename files with flexible patterns",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Sequential numbering
  %(prog)s "photo_{:03d}.jpg" *.jpg

  # Add date prefix
  %(prog)s "{name}_backup" * --add-date

  # Regex replace: IMG_001.jpg -> photo_001.jpg
  %(prog)s "photo_{i:03d}.jpg" IMG_*.jpg --regex "IMG_(\\d+)" "\\1"

  # Convert to lowercase
  %(prog)s "{name}" * --case lower

  # Dry run (preview only)
  %(prog)s "new_{i}.txt" *.txt --dry-run
        """
    )
    parser.add_argument(
        "pattern",
        help="New filename pattern. Use {i} for index, {n} or {name} for original name"
    )
    parser.add_argument(
        "files",
        nargs="+",
        help="Files to rename (supports wildcards)"
    )
    parser.add_argument(
        "--regex", "-r",
        help="Regex pattern to match in original filename"
    )
    parser.add_argument(
        "--replace", "-p",
        help="Replacement string for regex (use \\1, \\2 for groups)"
    )
    parser.add_argument(
        "--add-date",
        action="store_true",
        help="Add YYYY-MM-DD prefix"
    )
    parser.add_argument(
        "--add-time",
        action="store_true",
        help="Add HHMMSS time prefix"
    )
    parser.add_argument(
        "--case",
        choices=['upper', 'lower', 'title'],
        help="Convert filename to uppercase/lowercase/titlecase"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without renaming"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Show detailed logs"
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"smart_rename {__version__}"
    )
    return parser.parse_args()


def main():
    args = parse_args()

    # Expand wildcards (glob)
    files = []
    for pattern in args.files:
        files.extend(Path('.').glob(pattern))

    if not files:
        print(f"Error: No files match pattern: {args.files}", file=sys.stderr)
        sys.exit(1)

    renamer = SmartRename(
        pattern=args.pattern,
        files=[str(f) for f in files],
        regex=args.regex,
        replace=args.replace,
        add_date=args.add_date,
        add_time=args.add_time,
        case=args.case,
        dry_run=args.dry_run,
        verbose=args.verbose
    )
    renamed = renamer.run()

    if not renamed and not args.dry_run:
        print("\nNo files were renamed.", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()