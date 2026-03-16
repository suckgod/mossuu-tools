#!/usr/bin/env python3
"""
Duplicate Finder - Find and manage duplicate files

Finds duplicate files based on content hash (MD5/SHA1/SHA256).
Supports interactive selection, safe deletion, and reporting.

Usage:
    python duplicate_finder.py /path/to/search --min-size 1MB
    python duplicate_finder.py . --hash sha256 --action delete
    python duplicate_finder.py . --output duplicates.csv
"""

import os
import sys
import hashlib
import argparse
from pathlib import Path
from datetime import datetime
from collections import defaultdict
from typing import List, Tuple, Dict

__version__ = "1.0.0"

class DuplicateFinder:
    HASH_ALGORITHMS = {
        'md5': hashlib.md5,
        'sha1': hashlib.sha1,
        'sha256': hashlib.sha256,
    }

    def __init__(self, search_dir, min_size=0, max_size=None,
                 hash_algo='md5', action='list', output=None,
                 keep_newer=True, dry_run=False, verbose=False):
        self.search_dir = Path(search_dir).resolve()
        self.min_size = self._parse_size(min_size)
        self.max_size = self._parse_size(max_size) if max_size else None
        self.hash_algo = hash_algo
        self.action = action  # 'list', 'delete', 'move', 'report'
        self.output = Path(output) if output else None
        self.keep_newer = keep_newer
        self.dry_run = dry_run
        self.verbose = verbose
        self.hashes: Dict[str, List[Path]] = defaultdict(list)
        self.duplicates = []  # List of (original, duplicate) tuples

    def _parse_size(self, size_str):
        """Convert size string like '1MB', '500KB' to bytes"""
        if isinstance(size_str, (int, float)):
            return int(size_str)
        size_str = str(size_str).strip().upper()
        units = {'B': 1, 'K': 1024, 'M': 1024**2, 'G': 1024**3, 'T': 1024**4}
        for unit, factor in units.items():
            if size_str.endswith(unit):
                try:
                    num = float(size_str[:-1])
                    return int(num * factor)
                except:
                    raise ValueError(f"Invalid size format: {size_str}")
        try:
            return int(size_str)
        except:
            raise ValueError(f"Invalid size: {size_str}")

    def _get_file_hash(self, filepath: Path, chunk_size=8192) -> str:
        """Calculate hash of a file"""
        h = self.HASH_ALGORITHMS[self.hash_algo]()
        with open(filepath, 'rb') as f:
            while True:
                chunk = f.read(chunk_size)
                if not chunk:
                    break
                h.update(chunk)
        return h.hexdigest()

    def _should_skip(self, filepath: Path) -> Tuple[bool, str]:
        """Check if file should be skipped based on criteria"""
        try:
            stat = filepath.stat()
            size = stat.st_size

            if size < self.min_size:
                return True, f"too small (< {self.min_size} bytes)"
            if self.max_size and size > self.max_size:
                return True, f"too large (> {self.max_size} bytes)"
            return False, ""
        except Exception as e:
            return True, f"error: {e}"

    def scan_files(self):
        """Walk directory and compute hashes"""
        print(f"Scanning {self.search_dir} (min size: {self._format_size(self.min_size)})...")
        file_count = 0
        skipped = 0
        errors = 0

        for root, dirs, files in os.walk(self.search_dir):
            # Skip hidden directories
            dirs[:] = [d for d in dirs if not d.startswith('.')]

            for filename in files:
                if filename.startswith('.'):
                    continue

                filepath = Path(root) / filename
                skip, reason = self._should_skip(filepath)
                if skip:
                    skipped += 1
                    if self.verbose:
                        print(f"  Skipping {filepath.relative_to(self.search_dir)}: {reason}")
                    continue

                try:
                    file_hash = self._get_file_hash(filepath)
                    self.hashes[file_hash].append(filepath)
                    file_count += 1

                    if self.verbose and file_count % 100 == 0:
                        print(f"  Processed {file_count} files...")

                except Exception as e:
                    errors += 1
                    if self.verbose:
                        print(f"  Error reading {filepath}: {e}")

        print(f"Processed {file_count} files, skipped {skipped}, errors {errors}")
        print(f"Found {len([h for h, files in self.hashes.items() if len(files) > 1])} sets of duplicates")

    def _format_size(self, bytes):
        """Human readable file size"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if bytes < 1024.0:
                return f"{bytes:.1f}{unit}"
            bytes /= 1024.0
        return f"{bytes:.1f}TB"

    def identify_duplicates(self):
        """Identify which files to keep vs delete"""
        self.duplicates = []

        for file_hash, paths in self.hashes.items():
            if len(paths) < 2:
                continue

            # Sort by modification time (newest last)
            paths.sort(key=lambda p: p.stat().st_mtime)

            # Keep the first (oldest or manually marked)
            keeper = paths[0]
            duplicates = paths[1:]

            self.duplicates.append((keeper, duplicates))

    def list_action(self):
        """Just list duplicates"""
        print("\n" + "="*80)
        print("DUPLICATE FILES REPORT")
        print("="*80)

        total_wasted = 0
        for keeper, dupes in self.duplicates:
            keeper_size = keeper.stat().st_size
            print(f"\nOriginal: {keeper.relative_to(self.search_dir)} "
                  f"({self._format_size(keeper_size)})")
            for dup in dupes:
                dup_size = dup.stat().st_size
                print(f"  Duplicate: {dup.relative_to(self.search_dir)} "
                      f"({self._format_size(dup_size)})")
                total_wasted += dup_size

        print("\n" + "-"*80)
        print(f"Total space that could be freed: {self._format_size(total_wasted)}")

    def delete_action(self):
        """Delete duplicates (with confirmation)"""
        if not self.duplicates:
            print("No duplicates found.")
            return

        print("\n" + "="*80)
        print("DELETE DUPLICATES")
        print("="*80)

        total_size = sum(d.stat().st_size for _, dupes in self.duplicates for d in dupes)
        count = sum(len(dupes) for _, dupes in self.duplicates)

        print(f"\nWould delete {count} duplicate files")
        print(f"Space to free: {self._format_size(total_size)}\n")

        if self.dry_run:
            print("[DRY RUN] No files would actually be deleted.")
            return

        response = input(f"Delete {count} duplicate files? (yes/NO): ").strip().lower()
        if response != 'yes':
            print("Cancelled.")
            return

        deleted = 0
        errors = 0
        for keeper, dupes in self.duplicates:
            for dup in dupes:
                try:
                    dup.unlink()
                    deleted += 1
                except Exception as e:
                    errors += 1
                    print(f"  Error deleting {dup}: {e}")

        print(f"\n✅ Deleted {deleted} files, {errors} errors")
        print(f"Freed: {self._format_size(total_size)}")

    def move_action(self):
        """Move duplicates to a folder"""
        if not self.duplicates:
            print("No duplicates found.")
            return

        target_dir = self.search_dir / "_duplicates"
        if not self.dry_run:
            target_dir.mkdir(exist_ok=True)

        print(f"\nWould move duplicates to: {target_dir}")

        if self.dry_run:
            return

        moved = 0
        for keeper, dupes in self.duplicates:
            for dup in dupes:
                try:
                    new_path = target_dir / dup.name
                    # Handle name collisions
                    counter = 1
                    while new_path.exists():
                        new_path = target_dir / f"{dup.stem}_{counter}{dup.suffix}"
                        counter += 1
                    dup.rename(new_path)
                    moved += 1
                except Exception as e:
                    print(f"  Error moving {dup}: {e}")

        print(f"\n✅ Moved {moved} files to {target_dir}")

    def report_action(self):
        """Generate CSV report of duplicates"""
        if not self.output:
            self.output = Path('duplicates_report.csv')

        print(f"\nWriting report to {self.output}...")

        import csv
        with open(self.output, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['Keeper', 'Duplicate', 'Size(bytes)', 'Keeper Modified', 'Duplicate Modified'])
            for keeper, dupes in self.duplicates:
                keeper_mtime = datetime.fromtimestamp(keeper.stat().st_mtime)
                for dup in dupes:
                    dup_mtime = datetime.fromtimestamp(dup.stat().st_mtime)
                    writer.writerow([
                        str(keeper.relative_to(self.search_dir)),
                        str(dup.relative_to(self.search_dir)),
                        dup.stat().st_size,
                        keeper_mtime,
                        dup_mtime
                    ])

        print(f"✅ Report written with {len(self.duplicates)} duplicate sets")

    def run(self):
        """Execute the duplicate finding process"""
        self.scan_files()
        self.identify_duplicates()

        if self.action == 'list':
            self.list_action()
        elif self.action == 'delete':
            self.delete_action()
        elif self.action == 'move':
            self.move_action()
        elif self.action == 'report':
            self.report_action()
        else:
            print(f"Unknown action: {self.action}", file=sys.stderr)
            sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Duplicate Finder - Find and manage duplicate files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Find duplicates (list only)
  %(prog)s . --min-size 1MB

  # Delete duplicates (keeps oldest version)
  %(prog)s . --min-size 1MB --action delete

  # Move duplicates to a folder (dry run first!)
  %(prog)s /photos --action move --dry-run

  # Generate CSV report
  %(prog)s . --min-size 100KB --action report --output duplicates.csv

  # Use SHA256 (slower but more accurate for large files)
  %(prog)s . --hash sha256 --min-size 10MB
        """
    )
    parser.add_argument(
        "directory",
        nargs="?",
        default=".",
        help="Directory to search (default: current directory)"
    )
    parser.add_argument(
        "--min-size",
        default="0",
        help="Minimum file size (e.g., 1KB, 5MB, default: 0)"
    )
    parser.add_argument(
        "--max-size",
        help="Maximum file size (e.g., 100MB)"
    )
    parser.add_argument(
        "--hash",
        choices=['md5', 'sha1', 'sha256'],
        default='md5',
        help="Hash algorithm (default: md5)"
    )
    parser.add_argument(
        "--action",
        choices=['list', 'delete', 'move', 'report'],
        default='list',
        help="Action to take (default: list)"
    )
    parser.add_argument(
        "--output", "-o",
        help="Output file for report action"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview actions without making changes"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Show detailed logs"
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"duplicate_finder {__version__}"
    )

    args = parser.parse_args()

    try:
        finder = DuplicateFinder(
            search_dir=args.directory,
            min_size=args.min_size,
            max_size=args.max_size,
            hash_algo=args.hash,
            action=args.action,
            output=args.output,
            dry_run=args.dry_run,
            verbose=args.verbose
        )
        finder.run()
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
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