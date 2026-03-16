#!/usr/bin/env python3
"""
Smart Rename - Batch intelligent file renaming
"""

import os
import re
import sys
import time
import io
from pathlib import Path
from datetime import datetime

# Force UTF-8 output (for systems with ASCII default)
if sys.version_info[0] == 3 and sys.stdout.encoding != 'UTF-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

class SmartRenamer:
    def __init__(self, target_dir):
        self.target_dir = Path(target_dir)
        self.history = []

    def guess_category(self, filename):
        """根据扩展名猜测文件类型"""
        ext = Path(filename).suffix.lower()
        categories = {
            '.jpg': 'image', '.jpeg': 'image', '.png': 'image', '.gif': 'image',
            '.mp4': 'video', '.mov': 'video', '.avi': 'video',
            '.pdf': 'doc', '.doc': 'doc', '.docx': 'doc', '.txt': 'doc',
            '.py': 'code', '.js': 'code', '.html': 'code', '.css': 'code',
            '.mp3': 'audio', '.wav': 'audio', '.m4a': 'audio'
        }
        return categories.get(ext, 'misc')

    def sanitize_name(self, name):
        """移除特殊字符，保留字母数字和连字符"""
        return re.sub(r'[^\w\-\.]', '_', name)

    def generate_new_name(self, filepath, index):
        """生成新文件名"""
        cat = self.guess_category(filepath)
        stem = Path(filepath).stem
        ext = Path(filepath).suffix
        timestamp = datetime.now().strftime("%Y%m%d")
        safe_stem = self.sanitize_name(stem)[:30]  # 限制长度
        new_name = f"{timestamp}_{cat}_{safe_stem}{ext}"
        return new_name

    def run(self, dry_run=False):
        """Execute renaming"""
        files = list(self.target_dir.iterdir())
        files = [f for f in files if f.is_file() and not f.name.startswith('.')]

        print(f"Found {len(files)} files in {self.target_dir}")

        for idx, filepath in enumerate(files, 1):
            new_name = self.generate_new_name(filepath, idx)
            new_path = self.target_dir / new_name

            if new_path.exists():
                # If conflict, add counter
                base = new_path.stem
                ext = new_path.suffix
                counter = 1
                while new_path.exists():
                    new_path = self.target_dir / f"{base}_{counter}{ext}"
                    counter += 1

            if dry_run:
                print(f"[DRY] {filepath.name} -> {new_path.name}")
            else:
                filepath.rename(new_path)
                print(f"[OK] {filepath.name} -> {new_path.name}")
                self.history.append((str(filepath), str(new_path)))

        if not dry_run:
            print(f"\nDone! Renamed {len(self.history)} files.")

if __name__ == "__main__":
    import sys
    target = sys.argv[1] if len(sys.argv) > 1 else "."
    dry = "--dry-run" in sys.argv

    renamer = SmartRenamer(target)
    renamer.run(dry_run=dry)
