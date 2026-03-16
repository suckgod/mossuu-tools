#!/usr/bin/env python3
"""
Log Watcher - Real-time log file monitoring and alerting

Watch log files for patterns and trigger notifications via email,
desktop alerts, or webhooks. Handles log rotation gracefully.

Usage:
    python log_watcher.py /var/log/app/error.log --pattern "ERROR|FATAL"
    python log_watcher.py /var/log/syslog --email admin@example.com
"""

import os
import sys
import time
import argparse
import re
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Pattern

try:
    import smtplib
    from email.mime.text import MIMEText
    EMAIL_AVAILABLE = True
except ImportError:
    EMAIL_AVAILABLE = False

try:
    import requests
    WEBHOOK_AVAILABLE = True
except ImportError:
    WEBHOOK_AVAILABLE = False

__version__ = "1.0.0"

class LogWatcher:
    def __init__(self, logfile: str, pattern: str, case_sensitive=False,
                 email_to=None, webhook_url=None, state_file=None,
                 follow=True, ignore_older_days=7, verbose=False):
        self.logfile = Path(logfile).resolve()
        self.pattern = re.compile(pattern, re.IGNORECASE if not case_sensitive else 0)
        self.email_to = email_to
        self.webhook_url = webhook_url
        self.state_file = Path(state_file) if state_file else self.logfile.parent / f".{self.logfile.name}.offset"
        self.follow = follow
        self.ignore_older_days = ignore_older_days
        self.verbose = verbose
        self.last_position = 0
        self.alerts_sent = 0

    def get_file_size(self) -> int:
        """Get current file size, 0 if file doesn't exist"""
        try:
            return self.logfile.stat().st_size
        except FileNotFoundError:
            return 0

    def load_state(self):
        """Load last read position"""
        if self.state_file.exists():
            try:
                with open(self.state_file, 'r') as f:
                    self.last_position = int(f.read().strip())
            except:
                self.last_position = 0

    def save_state(self):
        """Save current position"""
        try:
            self.state_file.write_text(str(self.last_position))
        except Exception as e:
            if self.verbose:
                print(f"Warning: Could not save state: {e}")

    def read_new_lines(self) -> List[str]:
        """Read new lines since last check"""
        if not self.logfile.exists():
            return []

        current_size = self.get_file_size()

        # File was rotated (shrunk)
        if current_size < self.last_position:
            if self.verbose:
                print(f"[!] Log rotation detected: {self.logfile.name}")
            self.last_position = 0

        # No new data
        if current_size == self.last_position:
            return []

        # Read new content
        try:
            with open(self.logfile, 'r', encoding='utf-8', errors='ignore') as f:
                f.seek(self.last_position)
                lines = f.readlines()
                self.last_position = f.tell()
            return lines
        except Exception as e:
            if self.verbose:
                print(f"Error reading {self.logfile}: {e}")
            return []

    def matches_pattern(self, line: str) -> Optional[re.Match]:
        """Check if line matches the pattern"""
        return self.pattern.search(line)

    def format_alert(self, line: str, match: Optional[re.Match]) -> str:
        """Format alert message"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        matched_text = match.group(0) if match else "Pattern matched"
        return f"[{timestamp}] {self.logfile.name}: {matched_text}\nLine: {line.rstrip()}"

    def send_email(self, alerts: List[str]):
        """Send email alert"""
        if not EMAIL_AVAILABLE:
            print("Email not available (smtplib missing)", file=sys.stderr)
            return False

        if not self.email_to:
            return False

        subject = f"Log Alert: {self.logfile.name}"
        body = f"Detected {len(alerts)} matching line(s):\n\n" + "\n".join(alerts)

        msg = MIMEText(body)
        msg['Subject'] = subject
        msg['From'] = os.getenv('USER', 'logwatcher')
        msg['To'] = self.email_to

        try:
            with smtplib.SMTP('localhost') as server:
                server.send_message(msg)
            print(f"Email alert sent to {self.email_to}")
            return True
        except Exception as e:
            print(f"Failed to send email: {e}")
            return False

    def send_webhook(self, alerts: List[str]):
        """Send webhook alert"""
        if not WEBHOOK_AVAILABLE:
            print("Webhook not available (requests missing)", file=sys.stderr)
            return False

        if not self.webhook_url:
            return False

        payload = {
            "text": f"🚨 Log Alert: {self.logfile.name}",
            "content": f"Detected {len(alerts)} matching line(s):\n\n" + "\n".join(alerts[:10]),
            "timestamp": datetime.now().isoformat()
        }

        try:
            resp = requests.post(self.webhook_url, json=payload, timeout=10)
            if resp.status_code == 200:
                print("Webhook alert sent")
                return True
            else:
                print(f"Webhook failed: {resp.status_code}")
        except Exception as e:
            print(f"Webhook error: {e}")
        return False

    def run_once(self) -> int:
        """Process new lines, return number of alerts triggered"""
        self.load_state()
        lines = self.read_new_lines()
        alerts = []

        for line in lines:
            match = self.matches_pattern(line)
            if match:
                alert_msg = self.format_alert(line, match)
                alerts.append(alert_msg)
                if self.verbose:
                    print(f"[MATCH] {line.rstrip()}")

        if alerts:
            print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Found {len(alerts)} match(es):")
            for alert in alerts[:5]:  # Show first 5
                print(alert)
            if len(alerts) > 5:
                print(f"... and {len(alerts)-5} more")

            # Send notifications
            if self.email_to:
                self.send_email(alerts)
            if self.webhook_url:
                self.send_webhook(alerts)

            self.alerts_sent += len(alerts)

        self.save_state()
        return len(alerts)

    def run_daemon(self):
        """Run continuously, checking every second"""
        print(f"Starting log watcher: {self.logfile}")
        print(f"Pattern: {self.pattern.pattern}")
        print("Press Ctrl+C to stop\n")

        try:
            while True:
                self.run_once()
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nStopped.")
            print(f"Total alerts sent: {self.alerts_sent}")
            sys.exit(0)


def main():
    parser = argparse.ArgumentParser(
        description="Log Watcher - Real-time log monitoring and alerting",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Watch for ERROR or FATAL lines
  %(prog)s /var/log/app/error.log --pattern "ERROR|FATAL"

  # Send email when pattern matches
  %(prog)s /var/log/syslog --email admin@example.com

  # Run as daemon
  %(prog)s /var/log/nginx/access.log --pattern "50[0-9]" --daemon

  # Webhook to Slack/Discord
  %(prog)s /var/log/access.log --webhook https://hooks.slack.com/...
        """
    )
    parser.add_argument(
        "logfile",
        help="Log file to watch (will be created if doesn't exist)"
    )
    parser.add_argument(
        "--pattern", "-p",
        required=True,
        help="Regex pattern to match (e.g., 'ERROR', '50[0-9]')"
    )
    parser.add_argument(
        "--case-sensitive",
        action="store_true",
        help="Make pattern case-sensitive (default: case-insensitive)"
    )
    parser.add_argument(
        "--email-to",
        help="Email address to send alerts (requires local MTA)"
    )
    parser.add_argument(
        "--webhook",
        help="Webhook URL for Slack/Discord/Custom notifications"
    )
    parser.add_argument(
        "--state-file",
        help="File to store read position (default: .<logfile>.offset)"
    )
    parser.add_argument(
        "--daemon",
        action="store_true",
        help="Run continuously (default when used with wait)"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Show detailed output"
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"log_watcher {__version__}"
    )

    args = parser.parse_args()

    watcher = LogWatcher(
        logfile=args.logfile,
        pattern=args.pattern,
        case_sensitive=args.case_sensitive,
        email_to=args.email_to,
        webhook_url=args.webhook,
        state_file=args.state_file,
        verbose=args.verbose
    )

    if args.daemon:
        watcher.run_daemon()
    else:
        alerts = watcher.run_once()
        if alerts == 0 and not args.verbose:
            print("No new matches.")


if __name__ == "__main__":
    main()