#!/usr/bin/env python3
"""
Package AutoKit for distribution

Creates a ZIP file with all AutoKit scripts ready for customer download.
"""

import zipfile
from pathlib import Path

def package_autokit(output_file: str = "autokit-v1.0.0.zip"):
    """Create distributable ZIP package"""
    project_root = Path(__file__).parent
    scripts_dir = project_root / "products" / "python-autokit" / "scripts"
    output_path = project_root / output_file

    print("[PACKAGE] Packaging AutoKit from: {}".format(scripts_dir))
    print("   Output: {}".format(output_path))

    with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        # Add all Python scripts
        for py_file in sorted(scripts_dir.glob("*.py")):
            zf.write(py_file, arcname=f"autokit/{py_file.name}")
            print("  + {}".format(py_file.name))

        # Add license
        license_file = project_root / "LICENSE"
        if license_file.exists():
            zf.write(license_file, arcname="autokit/LICENSE")
            print("  + LICENSE")

        # Add README
        readme_file = project_root / "README.md"
        if readme_file.exists():
            zf.write(readme_file, arcname="autokit/README.md")
            print("  + README.md")

        # Add DEPENDENCIES.md
        deps_file = project_root / "DEPENDENCIES.md"
        if deps_file.exists():
            zf.write(deps_file, arcname="autokit/DEPENDENCIES.md")
            print("  + DEPENDENCIES.md")

        # Add QUICKSTART.md
        quickstart = project_root / "QUICKSTART.md"
        if quickstart.exists():
            zf.write(quickstart, arcname="autokit/QUICKSTART.md")
            print("  + QUICKSTART.md")

    # Get file size
    size = output_path.stat().st_size
    size_mb = size / (1024*1024)
    print("\n[OK] Package created: {}".format(output_path))
    print("   Size: {:,} bytes ({:.2f} MB)".format(size, size_mb))
    print("\n[INFO] Upload this file to GitHub Release as an asset.")

if __name__ == "__main__":
    import sys
    tag = sys.argv[1] if len(sys.argv) > 1 else "v1.0.0"
    output = "autokit-{}.zip".format(tag)
    package_autokit(output)
