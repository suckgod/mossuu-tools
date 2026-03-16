#!/usr/bin/env python3
"""
Duplicate Finder - Find and manage duplicate files

Usage:
    python duplicate_finder.py <directory> [--min-size <bytes>] [--extensions <ext1,ext2>] [--delete] [--hardlink] [--report <path>]

Options:
    <directory>     Directory to scan (recursively)
    --min-size      Minimum file size to consider (default: 1 byte)
    --extensions    Comma-separated list of extensions to scan (e.g., .jpg,.png,.pdf). Empty = all files.
    --delete        Auto-delete duplicates (keeps first occurrence)
    --hardlink      Replace duplicates with hard links (saves space, keeps originals)
    --report        Generate CSV report of duplicates (optional path)
    --dry-run       Show what would be done without making changes
    --verbose       Print detailed logs
    --version       Show version info

Examples:
    %(prog)s ./photos                          # Scan all files in photos/
    %(prog)s ./docs --extensions .pdf,.docx  # Only PDF and DOCX
    %(prog)s ./data --delete --dry-run        # Preview deletions first
    %(prog)s ./backup --hardlink --report duplicates.csv  # Save space with hard links
"""

import os
import sys
import hashlib
import argparse
from datetime import datetime
from pathlib import Path
from collections import defaultdict
import csv

__version__ = "1.0.0"

def compute_hash(filepath, block_size=65536, quick=False):
    """Compute SHA256 hash of a file"""
    hasher = hashlib.sha256()
    try:
        with open(filepath, 'rb') as f:
            if quick:
                # Quick mode: only hash first and last blocks
                f.seek(0, 0)
                buf = f.read(block_size)
                hasher.update(buf)

                size = f.seek(0, 2)
                if size > block_size * 2:
                    f.seek(-block_size, 2)
                    buf = f.read(block_size)
                    hasher.update(buf)
            else:
                # Full hash
                for buf in iter(lambda: f.read(block_size), b''):
                    hasher.update(buf)
        return hasher.hexdigest()
    except (IOError, OSError) as e:
        return None

class DuplicateFinder:
    def __init__(self, directory, min_size=1, extensions=None, dry_run=False,
                 delete=False, hardlink=False, report=None, verbose=False):
        self.directory = Path(directory)
        self.min_size = min_size
        self.extensions = extensions  # List of extensions or None for all
        self.dry_run = dry_run
        self.delete = delete
        self.hardlink = hardlink
        self.report = report
        self.verbose = verbose
        self.files_scanned = 0
        self.duplicates_found = 0
        self.space_saved = 0

    def log(self, msg):
        """Print message if verbose"""
        if self.verbose:
            print(msg)

    def should_process(self, filepath):
        """Check if file should be processed based on criteria"""
        if not filepath.is_file():
            return False

        if filepath.stat().st_size < self.min_size:
            return False

        if self.extensions:
            if filepath.suffix.lower() not in self.extensions:
                return False

        return True

    def scan_files(self):
        """Recursively scan directory for files"""
        self.log(f"Scanning: {self.directory}")
        files = []

        try:
            for root, dirs, filenames in os.walk(self.directory):
                root_path = Path(root)
                for filename in filenames:
                    filepath = root_path / filename
                    if self.should_process(filepath):
                        files.append(filepath)
        except (PermissionError, OSError) as e:
            print(f"Warning: Cannot access some directories: {e}", file=sys.stderr)

        self.log(f"Found {len(files)} files to process")
        return files

    def find_duplicates(self):
        """Find duplicate files by content hash"""
        hashes = defaultdict(list)
        files = self.scan_files()

        print(f"Computing hashes for {len(files)} files...")

        for i, filepath in enumerate(files, 1):
            if i % 100 == 0:
                print(f"  Progress: {i}/{len(files)}", end='\r')

            filehash = compute_hash(filepath, quick=True)  # Quick hash first
            if filehash:
                hashes[filehash].append(filepath)

        print(f"\nFound {len(hashes)} unique hashes")

        # Now verify full hash for potential duplicates
        duplicates = []
        for filehash, file_list in hashes.items():
            if len(file_list) > 1:
                # Full hash verification
                full_hashes = defaultdict(list)
                for fp in file_list:
                    full_hash = compute_hash(fp, quick=False)
                    if full_hash:
                        full_hashes[full_hash].append(fp)

                for fhash, flist in full_hashes.items():
                    if len(flist) > 1:
                        duplicates.append(flist)

        total_dups = sum(len(d) - 1 for d in duplicates)
        print(f"Found {len(duplicates)} duplicate sets ({total_dups} duplicate files)")

        return duplicates

    def handle_duplicates(self, duplicates):
        """Process duplicate files according to mode"""
        actions = []

        for file_list in duplicates:
            # Sort by modification time (keep oldest)
            file_list.sort(key=lambda x: x.stat().st_mtime)
            keeper = file_list[0]
            duplicates_to_handle = file_list[1:]

            for dup in duplicates_to_handle:
                size = dup.stat().st_size
                action = {
                    "keeper": keeper,
                    "duplicate": dup,
                    "size": size,
                    "action": None
                }

                if self.dry_run:
                    action["action"] = "dry-run"
                elif self.hardlink:
                    try:
                        dup.unlink()
                        os.link(keeper, dup)
                        self.space_saved += size
                        action["action"] = "hardlink"
                    except Exception as e:
                        print(f"Error hardlinking {dup}: {e}", file=sys.stderr)
                        action["action"] = "error"
                elif self.delete:
                    try:
                        dup.unlink()
                        self.space_saved += size
                        action["action"] = "delete"
                    except Exception as e:
                        print(f"Error deleting {dup}: {e}", file=sys.stderr)
                        action["action"] = "error"
                else:
                    action["action"] = "none"  # Just report

                actions.append(action)
                self.duplicates_found += 1

        return actions

    def generate_report(self, actions):
        """Generate CSV report of duplicate files"""
        if not self.report:
            return

        report_path = Path(self.report)
        if self.dry_run and not report_path.parent.exists():
            self.log(f"[DRY RUN] Would create report: {report_path}")
            return

        report_path.parent.mkdir(parents=True, exist_ok=True)

        with open(report_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=["keeper", "duplicate", "size_bytes", "action"])
            writer.writeheader()
            for action in actions:
                writer.writerow({
                    "keeper": str(action["keeper"]),
                    "duplicate": str(action["duplicate"]),
                    "size_bytes": action["size"],
                    "action": action["action"]
                })

        print(f"Report saved: {report_path}")

    def run(self):
        """Execute duplicate finding"""
        print(f"Duplicate Finder v{__version__}")
        print(f"Scan directory: {self.directory}")
        print(f"Mode: {'DRY RUN' if self.dry_run else 'LIVE'}")
        print()

        if not self.directory.exists():
            print(f"Error: Directory does not exist: {self.directory}", file=sys.stderr)
            return 1

        duplicates = self.find_duplicates()

        if not duplicates:
            print("✅ No duplicates found!")
            return 0

        print(f"\nProcessing {sum(len(d)-1 for d in duplicates)} duplicates...")
        actions = self.handle_duplicates(duplicates)

        # Summary
        print(f"\n📊 Summary:")
        print(f"  Files scanned: {self.files_scanned}")
        print(f"  Duplicate sets: {len(duplicates)}")
        print(f"  Duplicates handled: {self.duplicates_found}")

        if self.space_saved > 0:
            gb = self.space_saved / (1024**3)
            mb = self.space_saved / (1024**2)
            if gb >= 1:
                print(f"  Space saved: {gb:.2f} GB")
            else:
                print(f"  Space saved: {mb:.2f} MB")

        if self.report:
            self.generate_report(actions)
            print(f"  Report: {self.report}")

        if self.dry_run:
            print("\n💡 Tip: Run without --dry-run to apply changes")

        print("\n✅ Done!")
        return 0

def main():
    parser = argparse.ArgumentParser(
        description="Duplicate Finder - Find and manage duplicate files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Modes:
  (default)        Just report duplicates (safe)
  --delete         Delete duplicate files (keeps first/oldest)
  --hardlink       Replace duplicates with hard links (saves space, keeps data)

Note: Always test with --dry-run first!
        """
    )

    parser.add_argument(
        "directory",
        help="Directory to scan (recursively)"
    )
    parser.add_argument(
        "--min-size",
        type=int,
        default=1,
        help="Minimum file size in bytes (default: 1)"
    )
    parser.add_argument(
        "--extensions",
        type=str,
        help="Comma-separated file extensions (e.g., .jpg,.png,.pdf). Empty = all files."
    )
    parser.add_argument(
        "--delete",
        action="store_true",
        help="Delete duplicate files (use with caution!)"
    )
    parser.add_argument(
        "--hardlink",
        action="store_true",
        help="Replace duplicates with hard links (saves disk space)"
    )
    parser.add_argument(
        "--report",
        type=str,
        help="Generate CSV report at specified path"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without making changes"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print detailed logs"
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"duplicate_finder {__version__}",
        help="Show version information"
    )

    args = parser.parse_args()

    # Parse extensions
    extensions = None
    if args.extensions:
        extensions = [ext.lower() if ext.startswith('.') else f'.{ext.lower()}'
                      for ext in args.extensions.split(',')]
        extensions = [e for e in extensions if e]  # Remove empty

    # Confirmation for destructive operations
    if args.delete or args.hardlink:
        if args.dry_run:
            print("[DRY RUN] No files will be modified")
        else:
            print("⚠️  WARNING: This will modify files!")
            if args.delete:
                print("   Mode: DELETE duplicates")
            if args.hardlink:
                print("   Mode: HARD LINK duplicates")
            confirm = input("   Continue? (yes/no): ").strip().lower()
            if confirm != "yes":
                print("Aborted.")
                sys.exit(1)

    finder = DuplicateFinder(
        directory=args.directory,
        min_size=args.min_size,
        extensions=extensions,
        dry_run=args.dry_run,
        delete=args.delete,
        hardlink=args.hardlink,
        report=args.report,
        verbose=args.verbose
    )

    sys.exit(finder.run())

if __name__ == "__main__":
    main()
