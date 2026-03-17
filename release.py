#!/usr/bin/env python3
"""
GitHub Release Publisher for AutoKit

This script creates a GitHub release with the AutoKit scripts as downloadable assets.
It automates the process of packaging and publishing releases.

Usage:
    python release.py v1.0.0
    python release.py v1.0.0 --draft  # Create as draft first
    python release.py v1.0.0 --notes "Release notes here"
"""

import os
import sys
import json
import shutil
import tarfile
import tempfile
import subprocess
from pathlib import Path
from datetime import datetime

__version__ = "1.0.0"

class ReleasePublisher:
    def __init__(self, tag: str, draft: bool = False, notes: str = None, repo: str = None):
        self.tag = tag if tag.startswith('v') else f'v{tag}'
        self.draft = draft
        self.repo = repo or "suckgod/mossuu-tools"
        self.project_root = Path(__file__).parent.parent
        self.notes = notes or self.generate_default_notes()

    def generate_default_notes(self) -> str:
        """Generate default release notes"""
        return f"""
## 🚀 AutoKit Release {self.tag}

### ✅ What's New
- Complete Python AutoKit with 11 automation scripts
- Python 3.6+ compatible
- Cross-platform (Linux/macOS/Windows)

### 📦 What's Included
11 production-ready scripts:
1. smart_rename.py
2. duplicate_finder.py
3. disk_alerter.py
4. log_watcher.py
5. backup_rotator.py
6. csv_analyzer.py
7. excel_formatter.py
8. json_merger.py
9. markdown_toc.py
10. blog_auto.py
11. transcript_cleaner.py

### 📖 Documentation
- See [DEPENDENCIES.md](https://github.com/{self.repo}/blob/main/DEPENDENCIES.md) for package requirements
- Full README: https://github.com/{self.repo}

### 💳 Purchase
GitHub Sponsors: https://github.com/sponsors/suckgod

After payment, you'll receive this download link automatically.

---
*Released {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""

    def package_autokit(self, output_path: Path) -> Path:
        """Create a tar.gz archive of python-autokit/scripts"""
        print(f"📦 Packaging AutoKit scripts...")
        scripts_dir = self.project_root / "products" / "python-autokit" / "scripts"

        if not scripts_dir.exists():
            raise FileNotFoundError(f"Scripts directory not found: {scripts_dir}")

        with tarfile.open(output_path, "w:gz") as tar:
            # Add all .py files
            for py_file in scripts_dir.glob("*.py"):
                arcname = f"python-autokit/scripts/{py_file.name}"
                tar.add(py_file, arcname=arcname)
                print(f"  Added: {py_file.name}")

            # Add LICENSE
            license_src = self.project_root / "LICENSE"
            if license_src.exists():
                tar.add(license_src, arcname="python-autokit/LICENSE")

        print(f"  ✓ Package created: {output_path}")
        return output_path

    def check_gh_auth(self) -> bool:
        """Check if gh CLI is authenticated"""
        try:
            result = subprocess.run(
                ["gh", "auth", "status"],
                capture_output=True,
                text=True
            )
            return result.returncode == 0
        except:
            return False

    def create_release(self, asset_path: Path):
        """Create GitHub release with asset"""
        print(f"🚀 Creating GitHub release {self.tag}...")

        # Build gh command
        cmd = [
            "gh", "release", "create", self.tag,
            f"--repo={self.repo}",
            "--title=Python AutoKit " + self.tag,
            f"--notes={self.notes}"
        ]

        if self.draft:
            cmd.append("--draft")

        # Create release
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"❌ Error creating release: {result.stderr}")
            return False

        print(f"  ✓ Release created: {self.tag}")

        # Upload asset
        print(f"📤 Uploading asset: {asset_path.name}")
        upload_cmd = [
            "gh", "release", "upload", self.tag,
            str(asset_path),
            f"--repo={self.repo}"
        ]
        result = subprocess.run(upload_cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"❌ Error uploading asset: {result.stderr}")
            return False

        print(f"  ✓ Asset uploaded")

        # Get release URL
        url_cmd = ["gh", "release", "view", self.tag, "--json", "url", "--repo", self.repo]
        result = subprocess.run(url_cmd, capture_output=True, text=True)
        if result.returncode == 0:
            try:
                data = json.loads(result.stdout)
                release_url = data.get('url', '').replace('api.github.com/repos', 'github.com')
                print(f"\n✅ Release URL: {release_url}")
                print(f"📥 Direct asset: {asset_path.name}")
            except:
                pass

        return True

    def run(self) -> bool:
        """Execute release process"""
        # Check gh auth
        if not self.check_gh_auth():
            print("[FAIL] GitHub CLI not authenticated.")
            print("Please run: gh auth login")
            return False

        # Create temp directory for package
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            package_path = tmpdir / f"autokit-{self.tag}.tar.gz"

            # Package
            self.package_autokit(package_path)

            # Create release
            return self.create_release(package_path)

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Publish AutoKit GitHub Release")
    parser.add_argument("tag", help="Release tag (e.g., v1.0.0)")
    parser.add_argument("--draft", action="store_true", help="Create as draft")
    parser.add_argument("--notes", help="Custom release notes")
    parser.add_argument("--repo", help="GitHub repository (default: suckgod/mossuu-tools)")
    parser.add_argument("--version", action="version", version=f"release.py {__version__}")

    args = parser.parse_args()

    publisher = ReleasePublisher(
        tag=args.tag,
        draft=args.draft,
        notes=args.notes
    )
    if args.repo:
        publisher.repo = args.repo

    success = publisher.run()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
