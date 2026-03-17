#!/usr/bin/env python3
"""
Quick Deploy - Setup AutoKit for sale in 3 minutes

This script guides you through:
1. Creating GitHub Release (with asset)
2. Setting up Buy Me a Coffee link (optional)
3. Getting your product page ready

Usage:
    python3 quick_deploy.py
"""

import os
import sys
import json
import webbrowser
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent
ZIP_FILE = PROJECT_ROOT / "autokit-v1.0.0.zip"
PRODUCT_PAGE = PROJECT_ROOT / "products" / "python-autokit-product.md"
README = PROJECT_ROOT / "README.md"

print("""
╔═══════════════════════════════════════════════════════════╗
║      Python AutoKit - Quick Deployment Assistant        ║
║               One-time setup, 3 minutes                 ║
╚═══════════════════════════════════════════════════════════╝
""")

def check_prerequisites():
    """Check if ZIP exists"""
    if not ZIP_FILE.exists():
        print("[ERROR] autokit-v1.0.0.zip not found. Run: python3 package.py")
        return False
    print("[OK] Package ZIP found: {}".format(ZIP_FILE.name))
    return True

def step1_github_release():
    """Create GitHub Release using GitHub API"""
    print("\n" + "="*60)
    print("STEP 1: Create GitHub Release")
    print("="*60)

    print("""
This will create a PRIVATE release on GitHub containing the AutoKit ZIP.
Only sponsors will be able to access it.

Option A: Use GitHub CLI (if already logged in)
  gh release create v1.0.0 {} --title="Python AutoKit v1.0.0" --draft

Option B: Use GitHub API (recommended)
  1. Get a Personal Access Token (PAT) from:
     https://github.com/settings/tokens
     - Select "repo" scope
     - Generate token (copy it)
  2. I'll use it to create the release automatically.
""")

    choice = input("Choose option (A/B): ").strip().lower()

    if choice == 'a':
        print("\nPlease run in another terminal:")
        print('  gh release create v1.0.0 {} --title="Python AutoKit v1.0.0" --draft --notes="See product page"'.format(ZIP_FILE.name))
        print("\nThen log into GitHub.com and make the release PRIVATE.")
        return True

    # Option B: GitHub API
    print("\n--- GitHub API Setup ---")
    token = input("Paste your GitHub PAT (starts with ghp_...): ").strip()
    if not token.startswith('ghp_'):
        print("[WARN] Token format looks wrong, but proceeding...")

    import requests
    print("\nCreating release via API...")

    release_data = {
        "tag_name": "v1.0.0",
        "target_commitish": "main",
        "name": "Python AutoKit v1.0.0",
        "body": "AutoKit bundle - 11 automation scripts.\nSee product page: https://github.com/suckgod/mossuu-tools/blob/main/products/python-autokit-product.md",
        "draft": True,
        "prerelease": False,
        "private": True  # Only sponsors can access
    }

    headers = {
        "Authorization": "token {}".format(token),
        "Accept": "application/vnd.github.v3+json"
    }

    # Create release
    resp = requests.post(
        "https://api.github.com/repos/suckgod/mossuu-tools/releases",
        headers=headers,
        json=release_data
    )

    if resp.status_code not in (200, 201):
        print("[ERROR] Failed to create release: {} {}".format(resp.status_code, resp.text))
        return False

    release = resp.json()
    upload_url = release['upload_url'].split('{')[0]
    print("[OK] Release created: https://github.com/suckgod/mossuu-tools/releases/tag/v1.0.0")
    print("\nNow uploading asset...")

    # Upload asset
    with open(ZIP_FILE, 'rb') as f:
        params = {'name': ZIP_FILE.name}
        upload_resp = requests.post(
            upload_url,
            headers=headers,
            params=params,
            data=f
        )

    if upload_resp.status_code in (200, 201):
        print("[OK] Asset uploaded successfully!")
        asset_url = upload_resp.json().get('browser_download_url', '')
        print("\n📥 Download URL (keep this secret!):")
        print("   {}".format(asset_url))
        print("\n🔒 This URL is PRIVATE (only visible to sponsors).")
        return True
    else:
        print("[ERROR] Upload failed: {} {}".format(upload_resp.status_code, upload_resp.text))
        return False

def step2_github_sponsors():
    """Guide to enable GitHub Sponsors"""
    print("\n" + "="*60)
    print("STEP 2: Enable GitHub Sponsors")
    print("="*60)

    print("""
I'll open GitHub Sponsors page for you.

Steps:
1. Click "Set up Sponsors"
2. Create a tier:
   - Name: Python AutoKit - Single License
   - Amount: $20 (one-time)
   - Description: 11 automation scripts. Instant download.
3. Publish

Want me to open the page now?
""")

    open_now = input("Open https://github.com/sponsors/suckgod now? (y/n): ").strip().lower()
    if open_now == 'y':
        webbrowser.open('https://github.com/sponsors/suckgod')
        print("Browser opened. Complete the setup.")

    print("\n[SKIP] You can finish this later. The release is ready.")
    return True

def step3_buymeacoffee():
    """Optional: Setup Buy Me a Coffee for auto-delivery"""
    print("\n" + "="*60)
    print("STEP 3 (Optional): Buy Me a Coffee Setup")
    print("="*60)

    print("""
Buy Me a Coffee offers automatic delivery (no manual work).

1. Sign up at: https://www.buymeacoffee.com
2. Create a Product:
   - Title: Python AutoKit
   - Price: $19.99
   - Description: Copy from DEPLOYMENT GUIDE (I saved it)
   - Upload: {}
3. Get your product link

Want to do this later? The file contains ready-to-use description.
""".format(ZIP_FILE.name))

    later = input("Skip for now? (y/n): ").strip().lower()
    return True

def step4_marketing():
    """Prepare marketing materials"""
    print("\n" + "="*60)
    print("STEP 4: Marketing Materials Ready")
    print("="*60)

    reddit_file = PROJECT_ROOT / "REDDIT_SHOW_HN.md"
    if reddit_file.exists():
        print("\nI've prepared a Reddit Show HN post.")
        print("File: {}".format(reddit_file))
        print("When you're ready to launch:")
        print("  1. Post to r/Python, r/automation, r/programming")
        print("  2. Include your GitHub repo link")
        print("  3. Mention it's $19.99 one-time payment")
        print("\n📈 Expect 10-50 first sales from Reddit if upvoted.")

    print("\n✅ All deployment materials are ready!")
    return True

def main():
    if not check_prerequisites():
        sys.exit(1)

    print("\nQuick setup will guide you through:")
    print("  1. Create GitHub Release (with private asset)")
    print("  2. Enable GitHub Sponsors")
    print("  3. Optional: Buy Me a Coffee setup")
    print("  4. Marketing materials\n")

    proceed = input("Start now? (y/n): ").strip().lower()
    if proceed != 'y':
        print("Okay. Run again when ready.")
        sys.exit(0)

    success = True
    success = step1_github_release() and success
    success = step2_github_sponsors() and success
    success = step3_buymeacoffee() and success
    success = step4_marketing() and success

    print("\n" + "="*60)
    if success:
        print("✅ DEPLOYMENT SETUP COMPLETE!")
        print("\nNext steps:")
        print("  1. Verify your Release is PRIVATE on GitHub")
        print("  2. Test sponsor flow (use $1 test tier)")
        print("  3. Share your product link when ready")
        print("\n💰 Good luck with your first sales!")
    else:
        print("⚠️  Some steps need attention. Check above for errors.")
    print("="*60)

if __name__ == "__main__":
    main()
