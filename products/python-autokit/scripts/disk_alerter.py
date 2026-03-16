#!/usr/bin/env python3
"""
Disk Space Monitor - Alert when disk usage exceeds thresholds

Monitors disk space on local or mounted drives and sends notifications
via email, desktop, or webhook when thresholds are exceeded.

Usage:
    python disk_alerter.py --threshold 90%
    python disk_alerter.py / /home --threshold 80% --interval 600
    python disk_alerter.py --email admin@example.com
"""

import os
import sys
import time
import argparse
import json
from pathlib import Path
from datetime import datetime
from email.mime.text import MIMEText
from typing import List, Dict, Optional

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

__version__ = "1.0.0"

class DiskAlerter:
    def __init__(self, paths: List[str], threshold=90.0, check_interval=300,
                 email_to=None, email_from=None, smtp_server=None,
                 webhook_url=None, history_file=None, verbose=False):
        self.paths = [Path(p).resolve() for p in paths]
        self.threshold = self._parse_threshold(threshold)
        self.check_interval = check_interval
        self.email_to = email_to
        self.email_from = email_from or os.getenv('USER')
        self.smtp_server = smtp_server or 'localhost'
        self.webhook_url = webhook_url
        self.history_file = Path(history_file) if history_file else None
        self.verbose = verbose
        self.alerts_sent = set()  # Track alerts to avoid spamming

    def _parse_threshold(self, thresh):
        """Parse threshold string like '90%' or '0.9'"""
        if isinstance(thresh, (int, float)):
            return float(thresh)
        thresh = str(thresh).strip()
        if thresh.endswith('%'):
            return float(thresh[:-1])
        return float(thresh) * 100 if float(thresh) < 1 else float(thresh)

    def get_disk_usage(self, path: Path) -> Optional[Dict]:
        """Get disk usage stats for a path"""
        if not PSUTIL_AVAILABLE:
            if self.verbose:
                print("  Error: psutil not installed. Install with: pip install psutil")
            return None

        try:
            usage = psutil.disk_usage(str(path))
            return {
                'path': str(path),
                'total': usage.total,
                'used': usage.used,
                'free': usage.free,
                'percent': usage.percent,
                'fstype': self._get_fstype(path)
            }
        except Exception as e:
            if self.verbose:
                print(f"  Error checking {path}: {e}")
            return None

    def _get_fstype(self, path: Path) -> str:
        """Get filesystem type (Unix only, simplified)"""
        try:
            import subprocess
            result = subprocess.run(
                ['df', '-T', str(path)],
                capture_output=True, text=True
            )
            lines = result.stdout.strip().split('\n')
            if len(lines) >= 2:
                return lines[1].split()[1]
        except:
            pass
        return "unknown"

    def format_bytes(self, bytes_val):
        """Human readable bytes"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_val < 1024.0:
                return f"{bytes_val:.1f}{unit}"
            bytes_val /= 1024.0
        return f"{bytes_val:.1f}PB"

    def check_disks(self) -> List[Dict]:
        """Check all monitored paths and return alerts"""
        alerts = []
        for path in self.paths:
            usage = self.get_disk_usage(path)
            if not usage:
                continue

            if usage['percent'] >= self.threshold:
                alerts.append(usage)
                if self.verbose:
                    print(f"  ⚠️  {path}: {usage['percent']:.1f}% used")

        return alerts

    def send_email(self, alerts: List[Dict]):
        """Send email notification"""
        if not self.email_to:
            return False

        subject = f"Disk Space Alert on {os.uname().nodename if hasattr(os, 'uname') else 'localhost'}"
        body_lines = ["Disk space threshold exceeded:\n"]
        for alert in alerts:
            body_lines.append(
                f"Path: {alert['path']}\n"
                f"  Used: {alert['percent']:.1f}% "
                f"({self.format_bytes(alert['used'])} / {self.format_bytes(alert['total'])})\n"
                f"  Free: {self.format_bytes(alert['free'])}\n"
                f"  FS: {alert['fstype']}\n"
            )

        msg = MIMEText('\n'.join(body_lines))
        msg['Subject'] = subject
        msg['From'] = self.email_from
        msg['To'] = self.email_to

        try:
            with smtplib.SMTP(self.smtp_server) as server:
                server.send_message(msg)
            print(f"Email sent to {self.email_to}")
            return True
        except Exception as e:
            print(f"Failed to send email: {e}")
            return False

    def send_webhook(self, alerts: List[Dict]):
        """Send webhook notification (e.g., Slack, Discord)"""
        if not self.webhook_url:
            return False

        if not REQUESTS_AVAILABLE:
            print("Error: requests library not installed. Install with: pip install requests")
            return False

        try:
            payload = {
                "text": "🚨 Disk Space Alert",
                "attachments": []
            }
            for alert in alerts:
                payload["attachments"].append({
                    "title": alert['path'],
                    "text": f"Used: {alert['percent']:.1f}% | Free: {self.format_bytes(alert['free'])}",
                    "color": "warning" if alert['percent'] < 95 else "danger"
                })

            resp = requests.post(self.webhook_url, json=payload, timeout=10)
            if resp.status_code == 200:
                print("Webhook sent")
                return True
            else:
                print(f"Webhook failed: {resp.status_code}")
        except Exception as e:
            print(f"Webhook error: {e}")
        return False

    def save_history(self, alerts: List[Dict]):
        """Save alert history to file"""
        if not self.history_file:
            return

        entry = {
            'timestamp': datetime.now().isoformat(),
            'alerts': alerts
        }

        try:
            if self.history_file.exists():
                with open(self.history_file, 'r') as f:
                    history = json.load(f)
            else:
                history = []

            history.append(entry)

            # Keep last 1000 entries
            if len(history) > 1000:
                history = history[-1000:]

            with open(self.history_file, 'w') as f:
                json.dump(history, f, indent=2)
        except Exception as e:
            if self.verbose:
                print(f"Error saving history: {e}")

    def run_once(self) -> bool:
        """Run one check cycle. Returns True if alerts were sent."""
        alerts = self.check_disks()

        if not alerts:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] All disks OK")
            return False

        print(f"\n⚠️  ALERT: {len(alerts)} disk(s) exceeding {self.threshold}% usage")

        # Display current usage
        for alert in alerts:
            print(f"\n  {alert['path']}")
            print(f"    Used: {alert['percent']:.1f}% "
                  f"({self.format_bytes(alert['used'])} / {self.format_bytes(alert['total'])})")
            print(f"    Free: {self.format_bytes(alert['free'])}")

        # Send notifications
        if self.email_to:
            self.send_email(alerts)
        if self.webhook_url:
            self.send_webhook(alerts)

        self.save_history(alerts)
        return True

    def run_daemon(self):
        """Run continuously, checking at intervals"""
        print(f"Starting disk alerter daemon (threshold: {self.threshold}%)")
        print(f"Monitoring: {', '.join(str(p) for p in self.paths)}")
        print(f"Check interval: {self.check_interval}s")
        print("Press Ctrl+C to stop\n")

        try:
            while True:
                self.run_once()
                time.sleep(self.check_interval)
        except KeyboardInterrupt:
            print("\nStopped.")
            sys.exit(0)

def main():
    parser = argparse.ArgumentParser(
        description="Disk Space Monitor - Alert when disk usage exceeds thresholds",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Simple check of root partition, threshold 90%%
  %(prog)s /

  # Monitor multiple paths with email notification
  %(prog)s / /home --threshold 85%% --email admin@example.com

  # Run as daemon, check every 10 minutes
  %(prog)s / --interval 600 --daemon

  # Use webhook (Slack/Discord) instead of email
  %(prog)s / --webhook https://hooks.slack.com/...

  # Save history to file
  %(prog)s / --history /var/log/disk_alerter.json
        """
    )
    parser.add_argument(
        "paths",
        nargs="+",
        help="Paths or mount points to monitor"
    )
    parser.add_argument(
        "--threshold",
        default="90%",
        help="Alert threshold (e.g., 90%%, 0.9, default: 90%%)"
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=300,
        help="Check interval in seconds (default: 300 = 5min)"
    )
    parser.add_argument(
        "--email-to",
        help="Email address to send alerts to"
    )
    parser.add_argument(
        "--email-from",
        help="From email address (default: current user)"
    )
    parser.add_argument(
        "--smtp-server",
        default="localhost",
        help="SMTP server (default: localhost:25)"
    )
    parser.add_argument(
        "--webhook",
        help="Webhook URL for Slack/Discord/Custom"
    )
    parser.add_argument(
        "--history",
        help="JSON file to save alert history"
    )
    parser.add_argument(
        "--daemon",
        action="store_true",
        help="Run continuously (default if interval specified)"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Show detailed output"
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"disk_alerter {__version__}"
    )

    args = parser.parse_args()

    alerter = DiskAlerter(
        paths=args.paths,
        threshold=args.threshold,
        check_interval=args.interval,
        email_to=args.email_to,
        email_from=args.email_from,
        smtp_server=args.smtp_server,
        webhook_url=args.webhook,
        history_file=args.history,
        verbose=args.verbose
    )

    if args.daemon or args.interval > 0:
        alerter.run_daemon()
    else:
        alerter.run_once()


if __name__ == "__main__":
    main()