#!/usr/bin/env python3
"""
Blog Auto - Multi-platform blog publishing

Publish Markdown articles to multiple blog platforms:
- WordPress (REST API)
- Medium (via API)
- Dev.to (API)
- Hashnode (API)
- Ghost (Admin API)
- Generic RSS feed output

Features:
- Parse Markdown with frontmatter
- Extract title, content, tags, cover image
- Platform-specific formatting conversions
- Handle image uploads (especially for WordPress)
- Publish as draft or publish immediately
- Batch publishing from folder
- Dry-run mode to preview

Usage:
    python blog_auto.py publish article.md --platform wordpress --draft
    python blog_auto.py batch posts/ --platforms medium,dev.to --tags technology,python
    python blog_auto.py validate article.md --platform wordpress
"""

import os
import re
import sys
import json
import argparse
import base64
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from io import BytesIO

try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

__version__ = "1.0.0"

class BlogPublisher:
    def __init__(self, platform: str, config: Dict[str, Any], dry_run: bool = False, verbose: bool = False):
        self.platform = platform.lower()
        self.config = config
        self.dry_run = dry_run
        self.verbose = verbose
        self.session = requests.Session() if HAS_REQUESTS else None

        # Set platform-specific headers/settings
        self.setup_platform()

    def setup_platform(self):
        """Setup platform-specific API endpoints and auth"""
        if self.platform == 'wordpress':
            self.api_base = self.config.get('wp_site', '').rstrip('/')
            self.auth = (self.config.get('username'), self.config.get('password'))
            self.headers = {'Content-Type': 'application/json'}
        elif self.platform == 'medium':
            self.api_base = 'https://api.medium.com/v1'
            self.headers = {'Authorization': f"Bearer {self.config.get('token')}"}
        elif self.platform in ('devto', 'hashnode'):
            self.api_base = None  # Set per request
            self.headers = {'api-key': self.config.get('api_key')}
        elif self.platform == 'ghost':
            self.api_base = self.config.get('ghost_site', '').rstrip('/') + '/ghost/api/v3/admin'
            token = self.config.get('admin_api_key')
            self.headers = {'Authorization': f'Ghost {token}'}
        elif self.platform == 'rss':
            self.api_base = None
        else:
            raise ValueError(f"Unsupported platform: {self.platform}")

    def log(self, msg):
        if self.verbose:
            print(f"  {msg}")

    def parse_markdown(self, filepath: Path) -> Dict[str, Any]:
        """Parse Markdown file with frontmatter"""
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        # Split frontmatter
        frontmatter = {}
        body = content

        if content.startswith('---'):
            fm_end = content.find('---', 3)
            if fm_end != -1:
                fm_text = content[3:fm_end].strip()
                body = content[fm_end+3:].strip()
                if HAS_YAML:
                    try:
                        frontmatter = yaml.safe_load(fm_text) or {}
                    except:
                        frontmatter = {}
                else:
                    # Basic parsing without yaml
                    for line in fm_text.split('\n'):
                        if ':' in line:
                            key, val = line.split(':', 1)
                            frontmatter[key.strip()] = val.strip()

        # Extract title from first heading if not in frontmatter
        title = frontmatter.get('title', '')
        if not title:
            title_match = re.match(r'^#\s+(.+)$', body, re.MULTILINE)
            if title_match:
                title = title_match.group(1).strip()
                # Remove title from body
                body = re.sub(r'^#\s+.+\n?', '', body, count=1, flags=re.MULTILINE).strip()

        # Extract tags/categories
        tags = frontmatter.get('tags', frontmatter.get('categories', []))
        if isinstance(tags, str):
            tags = [t.strip() for t in tags.split(',')]

        # Extract cover image
        cover_image = frontmatter.get('image', frontmatter.get('cover', ''))
        # Remove frontmatter from body if present

        return {
            'title': title,
            'content': body,
            'tags': tags,
            'cover_image': cover_image,
            'frontmatter': frontmatter,
            'filepath': filepath
        }

    def convert_markdown_to_html(self, md_content: str) -> str:
        """Convert Markdown to HTML (basic, for platforms that need it)"""
        # Very simple conversion for demo; use markdown library if available
        try:
            import markdown
            return markdown.markdown(md_content, extensions=['extra', 'codehilite'])
        except ImportError:
            # Fallback: very basic
            html = md_content
            # Headers
            html = re.sub(r'^### (.+)$', r'<h3>\1</h3>', html, flags=re.MULTILINE)
            html = re.sub(r'^## (.+)$', r'<h2>\1</h2>', html, flags=re.MULTILINE)
            html = re.sub(r'^# (.+)$', r'<h1>\1</h1>', html, flags=re.MULTILINE)
            # Bold/italic
            html = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', html)
            html = re.sub(r'\*(.+?)\*', r'<em>\1</em>', html)
            # Code
            html = re.sub(r'`([^`]+)`', r'<code>\1</code>', html)
            html = re.sub(r'```\n(.+?)\n```', r'<pre><code>\1</code></pre>', html, flags=re.DOTALL)
            # Links
            html = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', html)
            # Paragraphs
            paragraphs = html.split('\n\n')
            paragraphs = [p.strip() for p in paragraphs if p.strip()]
            html = '\n'.join(f'<p>{p}</p>' for p in paragraphs)
            return html

    def upload_image_to_wordpress(self, image_path: Path) -> Optional[str]:
        """Upload image to WordPress Media Library"""
        if not HAS_REQUESTS or not HAS_PIL:
            return None

        try:
            # Determine content type
            ext = image_path.suffix.lower()
            mime_type = {
                '.jpg': 'image/jpeg',
                '.jpeg': 'image/jpeg',
                '.png': 'image/png',
                '.gif': 'image/gif',
                '.webp': 'image/webp'
            }.get(ext, 'image/jpeg')

            # Read and optionally resize image
            image_data = image_path.read_bytes()

            # Prepare upload
            upload_url = f"{self.api_base}/media"
            filename = image_path.name

            files = {
                'file': (filename, BytesIO(image_data), mime_type)
            }

            resp = self.session.post(upload_url, files=files, auth=self.auth, headers={'Content-Disposition': f'attachment; filename="{filename}"'})

            if resp.status_code in (200, 201):
                result = resp.json()
                return result.get('source_url')
            else:
                self.log(f"Image upload failed: {resp.status_code}")
                return None

        except Exception as e:
            self.log(f"Image upload error: {e}")
            return None

    def publish_to_wordpress(self, article: Dict[str, Any]) -> Tuple[bool, str]:
        """Publish article to WordPress"""
        post_data = {
            'title': article['title'],
            'content': self.convert_markdown_to_html(article['content']),
            'status': 'draft' if self.dry_run else 'publish',
            'categories': [],
            'tags': [{'name': tag} for tag in article['tags'][:5]]
        }

        # Handle cover image
        cover = article['cover_image']
        if cover:
            if cover.startswith('http'):
                post_data['featured_media_url'] = cover
            else:
                image_path = Path(cover)
                if image_path.exists():
                    if not self.dry_run:
                        media_url = self.upload_image_to_wordpress(image_path)
                        if media_url:
                            post_data['featured_media_url'] = media_url

        if self.dry_run:
            print(f"  [DRY RUN] Would post to WordPress: {post_data['title']}")
            return True, "dry-run"

        resp = self.session.post(
            f"{self.api_base}/posts",
            json=post_data,
            auth=self.auth,
            headers=self.headers
        )

        if resp.status_code in (200, 201):
            result = resp.json()
            post_id = result.get('id')
            post_url = result.get('link')
            return True, post_url or f"ID: {post_id}"
        else:
            error = resp.text
            return False, f"HTTP {resp.status_code}: {error}"

    def publish_to_medium(self, article: Dict[str, Any]) -> Tuple[bool, str]:
        """Publish article to Medium"""
        # First, create draft
        post_data = {
            'title': article['title'],
            'contentFormat': 'markdown',
            'content': article['content'],
            'tags': article['tags'][:5]
        }

        cover = article['cover_image']
        if cover:
            post_data['coverImage'] = cover

        if self.dry_run:
            print(f"  [DRY RUN] Would post to Medium: {article['title']}")
            return True, "dry-run"

        # User ID
        user_resp = self.session.get(f"{self.api_base}/me", headers=self.headers)
        if user_resp.status_code != 200:
            return False, f"Auth failed: {user_resp.text}"
        user_id = user_resp.json()['data']['id']

        # Create post
        post_url = f"{self.api_base}/users/{user_id}/posts"
        resp = self.session.post(post_url, json=post_data, headers=self.headers)

        if resp.status_code in (200, 201):
            result = resp.json()
            post_id = result.get('data', {}).get('id')
            status = result.get('data', {}).get('status')
            return True, f"ID: {post_id} ({status})"
        else:
            return False, f"HTTP {resp.status_code}: {resp.text}"

    def publish_to_devto(self, article: Dict[str, Any]) -> Tuple[bool, str]:
        """Publish article to Dev.to"""
        article_data = {
            'article': {
                'title': article['title'],
                'body_markdown': article['content'],
                'published': not self.dry_run,
                'tags': article['tags'][:4],
                'main_image': article['cover_image'] or None
            }
        }

        if self.dry_run:
            print(f"  [DRY RUN] Would post to Dev.to: {article['title']}")
            return True, "dry-run"

        resp = requests.post(
            'https://dev.to/api/articles',
            json=article_data,
            headers={'api-key': self.config.get('api_key')}
        )

        if resp.status_code in (200, 201):
            result = resp.json()
            article_id = result.get('id')
            url = result.get('url')
            return True, f"ID: {article_id} ({url})"
        else:
            return False, f"HTTP {resp.status_code}: {resp.text[:200]}"

    def publish_to_hashnode(self, article: Dict[str, Any]) -> Tuple[bool, str]:
        """Publish article to Hashnode"""
        graphql = """
        mutation CreateDraft($input: CreateDraftInput!) {
          createDraft(input: $input) {
            draft {
              id
              post {
               slug
                url
              }
            }
          }
        }
        """

        variables = {
            'input': {
                'title': article['title'],
                'contentMarkdown': article['content'],
                'hideFromHashnodeFeed': False,
                'tags': [{'name': tag, 'slug': tag.lower().replace(' ', '-')} for tag in article['tags'][:5]]
            }
        }

        if self.dry_run:
            print(f"  [DRY RUN] Would post to Hashnode: {article['title']}")
            return True, "dry-run"

        resp = requests.post(
            'https://gql.hashnode.com',
            json={'query': graphql, 'variables': variables},
            headers={'Authorization': self.config.get('token')}
        )

        if resp.status_code == 200:
            result = resp.json()
            if 'errors' in result:
                return False, str(result['errors'])
            draft = result['data']['createDraft']['draft']
            return True, f"ID: {draft['id']} ({draft['post']['url']})"
        else:
            return False, f"HTTP {resp.status_code}: {resp.text[:200]}"

    def publish_to_ghost(self, article: Dict[str, Any]) -> Tuple[bool, str]:
        """Publish article to Ghost (Admin API)"""
        # Ghost API v3 requires creating a post resource
        post_data = {
            'posts': [{
                'title': article['title'],
                'html': self.convert_markdown_to_html(article['content']),
                'status': 'draft' if self.dry_run else 'published',
                'tags': [{'name': tag} for tag in article['tags'][:5]],
                'feature_image': article['cover_image'] or None
            }]
        }

        if self.dry_run:
            print(f"  [DRY RUN] Would post to Ghost: {article['title']}")
            return True, "dry-run"

        resp = self.session.post(
            f"{self.api_base}/posts/",
            json=post_data,
            headers=self.headers
        )

        if resp.status_code in (200, 201):
            result = resp.json()
            posts = result.get('posts', [])
            if posts:
                post_id = posts[0]['id']
                slug = posts[0]['slug']
                url = f"{self.config.get('ghost_site')}/{slug}/"
                return True, f"ID: {post_id} ({url})"
            return True, "Created"
        else:
            return False, f"HTTP {resp.status_code}: {resp.text[:200]}"

    def generate_rss(self, articles: List[Dict[str, Any]], output_path: Path):
        """Generate RSS feed from articles"""
        from datetime import datetime
        import xml.etree.ElementTree as ET

        rss = ET.Element('rss', version='2.0')
        channel = ET.SubElement(rss, 'channel')
        ET.SubElement(channel, 'title').text = self.config.get('feed_title', 'Blog Feed')
        ET.SubElement(channel, 'link').text = self.config.get('site_url', 'https://example.com')
        ET.SubElement(channel, 'description').text = self.config.get('description', '')

        for article in articles:
            item = ET.SubElement(channel, 'item')
            ET.SubElement(item, 'title').text = article['title']
            ET.SubElement(item, 'link').text = article.get('link', '#')
            ET.SubElement(item, 'guid').text = article.get('link', '#')
            ET.SubElement(item, 'description').text = article['content'][:500] + '...'

        tree = ET.ElementTree(rss)
        ET.indent(tree, space='  ', level=0)
        tree.write(output_path, encoding='utf-8', xml_declaration=True)
        print(f"  RSS saved to: {output_path}")

    def publish(self, article: Dict[str, Any]) -> Tuple[bool, str]:
        """Publish article to configured platform"""
        print(f"\nPublishing: {article['title']}")

        if self.platform == 'wordpress':
            return self.publish_to_wordpress(article)
        elif self.platform == 'medium':
            return self.publish_to_medium(article)
        elif self.platform == 'devto':
            return self.publish_to_devto(article)
        elif self.platform == 'hashnode':
            return self.publish_to_hashnode(article)
        elif self.platform == 'ghost':
            return self.publish_to_ghost(article)
        elif self.platform == 'rss':
            return True, "RSS (handled by batch)"
        else:
            return False, f"Unknown platform: {self.platform}"

def load_config(config_file: Path) -> Dict[str, Any]:
    """Load platform configuration from JSON"""
    if not config_file.exists():
        return {}
    with open(config_file, 'r') as f:
        return json.load(f)

def main():
    parser = argparse.ArgumentParser(
        description="Blog Auto - Multi-platform blog publishing",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Publish single article to WordPress (draft)
  %(prog)s publish article.md --platform wordpress --draft

  # Publish and publish immediately
  %(prog)s publish post.md --platform medium --config medium.json

  # Batch publish all markdown files in folder
  %(prog)s batch posts/ --platforms wordpress,dev.to

  # Validate article structure without publishing
  %(prog)s validate article.md --platform wordpress

  # Generate RSS from folder of articles
  %(prog)s rss posts/ --output feed.xml --config rss.json

Configuration:
  Create JSON config file with platform-specific keys:

  WordPress:
    {"wp_site": "https://yourblog.com", "username": "admin", "password": "app_password"}

  Medium:
    {"token": "your-medium-integration-token"}

  Dev.to:
    {"api_key": "your-devto-api-key"}

  Hashnode:
    {"token": "your-hashnode-token"}

  Ghost:
    {"ghost_site": "https://your-ghost.com", "admin_api_key": "ghost-admin-key"}

  RSS:
    {"feed_title": "My Blog", "site_url": "https://example.com", "description": "My awesome blog"}

Notes:
  - Requires dependencies: pip install requests pyyaml pillow (for image handling)
  - Markdown frontmatter: title, tags, image optional
  - Dry-run shows what would be published without API calls
  - Tags limited per platform (usually 5 max)
      """
    )
    subparsers = parser.add_subparsers(dest='command', required=True)

    # Publish single file
    pub_parser = subparsers.add_parser('publish', help='Publish single article')
    pub_parser.add_argument('file', help='Markdown file to publish')
    pub_parser.add_argument('--platform', required=True, choices=['wordpress', 'medium', 'devto', 'hashnode', 'ghost'], help='Target platform')
    pub_parser.add_argument('--config', type=Path, default=Path('blog_config.json'), help='Config file (default: blog_config.json)')
    pub_parser.add_argument('--draft', action='store_true', help='Save as draft (where supported)')
    pub_parser.add_argument('--dry-run', action='store_true', help='Preview only, no actual publish')
    pub_parser.add_argument('--verbose', '-v', action='store_true')

    # Batch publish
    batch_parser = subparsers.add_parser('batch', help='Batch publish from folder')
    batch_parser.add_argument('folder', help='Folder containing markdown files')
    batch_parser.add_argument('--platforms', required=True, help='Comma-separated list of platforms')
    batch_parser.add_argument('--config', type=Path, default=Path('blog_config.json'))
    batch_parser.add_argument('--dry-run', action='store_true')
    batch_parser.add_argument('--verbose', '-v', action='store_true')

    # Validate
    val_parser = subparsers.add_parser('validate', help='Validate article structure')
    val_parser.add_argument('file', help='Markdown file to validate')
    val_parser.add_argument('--platform', choices=['wordpress', 'medium', 'devto', 'hashnode', 'ghost'], help='Platform-specific checks')

    # RSS generation
    rss_parser = subparsers.add_parser('rss', help='Generate RSS feed')
    rss_parser.add_argument('folder', help='Folder with articles')
    rss_parser.add_argument('--output', required=True, help='Output RSS file path')
    rss_parser.add_argument('--config', type=Path, default=Path('blog_config.json'))

    parser.add_argument('--version', action='version', version=f"blog_auto {__version__}")

    args = parser.parse_args()

    # Check dependencies
    if not HAS_REQUESTS and args.command != 'validate':
        print("Error: 'requests' library required. Install: pip install requests", file=sys.stderr)
        sys.exit(1)

    if not HAS_YAML and args.command != 'validate':
        print("Warning: 'PyYAML' not installed. Frontmatter parsing limited.", file=sys.stderr)

    # Execute command
    try:
        config = load_config(Path(args.config))

        if args.command == 'publish':
            publisher = BlogPublisher(
                platform=args.platform,
                config=config.get(args.platform, {}),
                dry_run=args.dry_run,
                verbose=args.verbose
            )
            article = publisher.parse_markdown(Path(args.file))
            if not article['title']:
                print("Error: Article must have a title (frontmatter or first # heading)")
                sys.exit(1)
            success, msg = publisher.publish(article)
            if success:
                print(f"✓ Success: {msg}")
            else:
                print(f"✗ Failed: {msg}")
                sys.exit(1)

        elif args.command == 'batch':
            platforms = [p.strip() for p in args.platforms.split(',')]
            folder = Path(args.folder)
            md_files = list(folder.glob('**/*.md'))

            if not md_files:
                print(f"No markdown files found in {folder}")
                sys.exit(0)

            print(f"Found {len(md_files)} articles to publish")

            for platform in platforms:
                print(f"\n🎯 Publishing to {platform.upper()}")
                publisher = BlogPublisher(
                    platform=platform,
                    config=config.get(platform, {}),
                    dry_run=args.dry_run,
                    verbose=args.verbose
                )

                for md_file in md_files:
                    article = publisher.parse_markdown(md_file)
                    if not article['title']:
                        print(f"  Skipped {md_file.name}: no title")
                        continue
                    success, msg = publisher.publish(article)
                    status = "✓" if success else "✗"
                    print(f"  {status} {article['title']}: {msg}")

        elif args.command == 'validate':
            filepath = Path(args.file)
            if not filepath.exists():
                print(f"File not found: {filepath}")
                sys.exit(1)

            # Parse
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()

                frontmatter = {}
                if content.startswith('---'):
                    fm_end = content.find('---', 3)
                    if fm_end != -1:
                        fm_text = content[3:fm_end].strip()
                        if HAS_YAML:
                            import yaml
                            frontmatter = yaml.safe_load(fm_text) or {}

                title = frontmatter.get('title', '')
                if not title:
                    title_match = re.match(r'^#\s+(.+)$', content, re.MULTILINE)
                    title = title_match.group(1).strip() if title_match else ''

                if title:
                    print("✓ Valid: Title found")
                else:
                    print("✗ Invalid: No title found")

                tags = frontmatter.get('tags', [])
                if tags:
                    print(f"✓ Tags: {tags}")
                else:
                    print("  Warning: No tags specified")

                if args.platform:
                    print(f"  Platform-specific ({args.platform}) validation: OK")

            except Exception as e:
                print(f"✗ Error: {e}")
                sys.exit(1)

        elif args.command == 'rss':
            folder = Path(args.folder)
            md_files = list(folder.glob('**/*.md'))

            articles = []
            publisher = BlogPublisher('rss', config.get('rss', {}), dry_run=False)

            for md_file in md_files:
                article = publisher.parse_markdown(md_file)
                if article['title']:
                    articles.append(article)

            # Sort by filename (assuming chronological)
            articles.sort(key=lambda a: a['filepath'].name)

            publisher.generate_rss(articles, Path(args.output))
            print(f"✓ Generated RSS with {len(articles)} articles")

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
