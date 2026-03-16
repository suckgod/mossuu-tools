#!/usr/bin/env python3
"""
Backup Rotator - Smart backup cleanup policies

Rotate and clean up backup directories/files based on policies:
- Keep last N backups
- Keep daily backups for X days
- Keep weekly backups for X weeks
- Keep monthly backups for X months
- Delete older backups automatically

Usage:
    python backup_rotator.py /path/to/backup --keep-last 10
    python backup_rotator.py /backup --daily 7 --weekly 4 --monthly 12
    python backup_rotator.py /backup --dry-run --verbose
"""

import os
import sys
import re
import argparse
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional
import json

__version__ = "1.0.0"

class BackupRotator:
    def __init__(self, backup_dir: str,
                 keep_last: Optional[int] = None,
                 keep_daily: Optional[int] = None,
                 keep_weekly: Optional[int] = None,
                 keep_monthly: Optional[int] = None,
                 pattern: str = None,
                 dry_run: bool = False,
                 verbose: bool = False,
                 history_file: str = None):
        self.backup_dir = Path(backup_dir).resolve()
        self.keep_last = keep_last
        self.keep_daily = keep_daily
        self.keep_weekly = keep_weekly
        self.keep_monthly = keep_monthly
        self.dry_run = dry_run
        self.verbose = verbose
        self.history_file = Path(history_file) if history_file else None

        # Default patterns for common backup naming conventions
        self.patterns = [
            r'backup[_-]?(\d{4}[-_]?\d{2}[-_]?\d{2})',  # backup_2025-03-17
            r'(\d{4}[-_]?\d{2}[-_]?\d{2})[_-]?backup',  # 2025-03-17_backup
            r'.*?(\d{8})',  # anything with YYYYMMDD
            r'.*?(\d{4}-\d{2}-\d{2})',  # anything with YYYY-MM-DD
        ]
        self.custom_pattern = pattern
        self.backups = []  # List of (path, date, type) tuples

    def log(self, msg):
        if self.verbose:
            print(msg)

    def extract_date(self, filename: str) -> Optional[datetime]:
        """Extract date from filename using patterns"""
        patterns = [self.custom_pattern] if self.custom_pattern else self.patterns

        for pattern in patterns:
            match = re.search(pattern, filename, re.IGNORECASE)
            if match:
                date_str = match.group(1)
                for fmt in ['%Y%m%d', '%Y-%m-%d', '%Y_%m_%d', '%Y%m%d%H%M%S']:
                    try:
                        return datetime.strptime(date_str, fmt)
                    except ValueError:
                        continue
        return None

    def scan_backups(self):
        """Scan backup directory and categorize by date"""
        if not self.backup_dir.exists():
            raise FileNotFoundError(f"Backup directory not found: {self.backup_dir}")

        self.log(f"Scanning: {self.backup_dir}")

        for item in self.backup_dir.iterdir():
            if not item.is_file() and not item.is_dir():
                continue

            date = self.extract_date(item.name)
            if date:
                self.backups.append((item, date))
                self.log(f"  Found: {item.name} -> {date.date()}")
            else:
                self.log(f"  Skipped (no date): {item.name}")

        # Sort by date (oldest first)
        self.backups.sort(key=lambda x: x[1])
        self.log(f"\nTotal backups found: {len(self.backups)}")

    def categorize_by_period(self, backup_date: datetime, reference_date: datetime = None) -> str:
        """Categorize backup as daily, weekly, or monthly"""
        if reference_date is None:
            reference_date = datetime.now()

        delta = reference_date - backup_date

        # Same month = monthly candidate
        if backup_date.year == reference_date.year and backup_date.month == reference_date.month:
            return 'monthly'
        # Within 7 days = weekly candidate
        if delta.days <= 7:
            return 'weekly'
        # Otherwise daily
        return 'daily'

    def select_to_keep(self) -> List[Path]:
        """Apply retention policies and return list of backups to keep"""
        to_keep = set()
        now = datetime.now()

        # Group backups by period type
        daily = []
        weekly = []
        monthly = []

        for path, date in self.backups:
            period_type = self.categorize_by_period(date, now)
            if period_type == 'daily':
                daily.append((path, date))
            elif period_type == 'weekly':
                weekly.append((path, date))
            else:
                monthly.append((path, date))

        # Apply keep_daily policy (most recent N daily backups outside weekly/monthly)
        if self.keep_daily:
            # Daily backups are those not selected as weekly/monthly
            # We'll process in reverse order (newest first)
            remaining_daily = sorted(daily, key=lambda x: x[1], reverse=True)
            for path, date in remaining_daily[:self.keep_daily]:
                to_keep.add(path)
                self.log(f"  Keep daily: {path.name}")

        # Apply keep_weekly policy (most recent N weekly backups)
        if self.keep_weekly:
            weekly_sorted = sorted(weekly, key=lambda x: x[1], reverse=True)
            for path, date in weekly_sorted[:self.keep_weekly]:
                to_keep.add(path)
                self.log(f"  Keep weekly: {path.name}")

        # Apply keep_monthly policy (most recent N monthly backups)
        if self.keep_monthly:
            monthly_sorted = sorted(monthly, key=lambda x: x[1], reverse=True)
            for path, date in monthly_sorted[:self.keep_monthly]:
                to_keep.add(path)
                self.log(f"  Keep monthly: {path.name}")

        # Apply keep_last policy (absolute last N backups regardless of period)
        if self.keep_last:
            all_sorted = sorted(self.backups, key=lambda x: x[1], reverse=True)
            for path, date in all_sorted[:self.keep_last]:
                to_keep.add(path)
                self.log(f"  Keep last: {path.name}")

        return list(to_keep)

    def delete_backup(self, path: Path):
        """Delete a backup file or directory"""
        try:
            if path.is_file():
                path.unlink()
            elif path.is_dir():
                import shutil
                shutil.rmtree(path)
            self.log(f"  Deleted: {path.name}")
            return True
        except Exception as e:
            print(f"  Error deleting {path.name}: {e}", file=sys.stderr)
            return False

    def save_history(self, deleted: List[Path], kept: List[Path]):
        """Save rotation history to JSON file"""
        if not self.history_file:
            return

        entry = {
            'timestamp': datetime.now().isoformat(),
            'backup_dir': str(self.backup_dir),
            'deleted': [str(p) for p in deleted],
            'kept': [str(p) for p in kept],
            'total_backups': len(self.backups),
            'policies': {
                'keep_last': self.keep_last,
                'keep_daily': self.keep_daily,
                'keep_weekly': self.keep_weekly,
                'keep_monthly': self.keep_monthly
            }
        }

        try:
            if self.history_file.exists():
                with open(self.history_file, 'r') as f:
                    history = json.load(f)
            else:
                history = []

            history.append(entry)

            # Keep last 100 entries
            if len(history) > 100:
                history = history[-100:]

            with open(self.history_file, 'w') as f:
                json.dump(history, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save history: {e}", file=sys.stderr)

    def run(self) -> Tuple[List[Path], List[Path]]:
        """Execute rotation. Returns (deleted_list, kept_list)"""
        self.scan_backups()
        to_keep = self.select_to_keep()

        # Determine what to delete
        to_delete = [path for path, _ in self.backups if path not in to_keep]

        # Sort by date (oldest first) for clearer output
        to_delete.sort(key=lambda x: next(d for p, d in self.backups if p == x))

        print(f"\nBackups to KEEP: {len(to_keep)}")
        print(f"Backups to DELETE: {len(to_delete)}")

        if to_delete and self.verbose:
            print("\nMarked for deletion:")
            for path in to_delete:
                date = next(d for p, d in self.backups if p == path)
                print(f"  {path.name} ({date.date()})")

        # Perform deletion
        deleted = []
        if to_delete:
            if self.dry_run:
                print("\n[DRY RUN] No files deleted.")
            else:
                print("\nDeleting old backups...")
                for path in to_delete:
                    if self.delete_backup(path):
                        deleted.append(path)
                print(f"Deleted {len(deleted)} backups")

        # Save history
        self.save_history(deleted, to_keep)

        return deleted, to_keep

def main():
    parser = argparse.ArgumentParser(
        description="Backup Rotator - Smart backup cleanup policies",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Keep only the last 10 backups (simple rotation)
  %(prog)s /backup --keep-last 10

  # Keep 7 daily + 4 weekly + 12 monthly backups
  %(prog)s /backup --daily 7 --weekly 4 --monthly 12

  # Combine policies (keep last 30 + hourly retention)
  %(prog)s /backup --keep-last 30 --daily 3 --weekly 2 --monthly 6

  # Dry run to see what would be deleted
  %(prog)s /backup --keep-last 10 --dry-run --verbose

  # Custom date pattern (e.g., backup_20250317_1200)
  %(prog)s /backup --keep-last 20 --pattern "backup_\\d{8}_\\d{4}"

Notes:
  - Policies are additive. A backup is kept if it matches ANY keep rule.
  - Rotator works on both files and directories.
  - Date patterns: YYYYMMDD, YYYY-MM-DD, YYYY_MM_DD common formats.
  - Default patterns cover: backup_YYYY-MM-DD, YYYYMMDD, etc.
      """
    )
    parser.add_argument(
        "backup_dir",
        help="Directory containing backups"
    )
    parser.add_argument(
        "--keep-last",
        type=int,
        help="Keep the N most recent backups (regardless of time period)"
    )
    parser.add_argument(
        "--daily",
        type=int,
        help="Keep N most recent daily backups"
    )
    parser.add_argument(
        "--weekly",
        type=int,
        help="Keep N most recent weekly backups (within 7 days)"
    )
    parser.add_argument(
        "--monthly",
        type=int,
        help="Keep N most recent monthly backups (same month)"
    )
    parser.add_argument(
        "--pattern",
        help="Custom regex pattern with date capture group (e.g., 'backup_(\\d{8})')"
    )
    parser.add_argument(
        "--history",
        help="JSON file to save rotation history"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be deleted without actually deleting"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Show detailed output"
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"backup_rotator {__version__}"
    )

    args = parser.parse_args()

    # Require at least one retention policy
    if not any([args.keep_last, args.daily, args.weekly, args.keep_monthly]):
        parser.error("At least one retention policy required (--keep-last, --daily, --weekly, or --monthly)")

    rotator = BackupRotator(
        backup_dir=args.backup_dir,
        keep_last=args.keep_last,
        keep_daily=args.daily,
        keep_weekly=args.weekly,
        keep_monthly=args.monthly,
        pattern=args.pattern,
        dry_run=args.dry_run,
        verbose=args.verbose,
        history_file=args.history
    )

    try:
        deleted, kept = rotator.run()
        print(f"\nSummary: {len(kept)} kept, {len(deleted)} deleted")
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
