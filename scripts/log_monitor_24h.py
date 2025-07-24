#!/usr/bin/env python3
"""
24-Hour Log Monitoring Script for Gary-Zero Production
Monitors Railway logs for 4xx/5xx HTTP error spikes over 24 hours
"""

import json
import re
import subprocess
import sys
import time
from collections import defaultdict, deque
from datetime import datetime, timedelta


class LogMonitor:
    def __init__(self):
        self.error_counts = defaultdict(int)
        self.hourly_errors = deque(maxlen=24)  # Keep last 24 hours
        self.baseline_threshold = 10  # Normal error rate per hour
        self.spike_threshold = 50  # Alert if errors exceed this per hour
        self.monitor_duration = 24 * 3600  # 24 hours in seconds
        self.check_interval = 300  # Check every 5 minutes
        self.start_time = datetime.now()

    def get_railway_logs(self):
        """Fetch recent logs from Railway"""
        try:
            # Use timeout command to limit log collection to 10 seconds
            result = subprocess.run(
                [
                    "timeout",
                    "10s",
                    "railway",
                    "logs",
                    "--service",
                    "gary-zero",
                    "--environment",
                    "production",
                ],
                capture_output=True,
                text=True,
            )

            # Timeout command returns 124 when it times out, which is expected
            if result.returncode not in [0, 124]:
                print(f"Error fetching logs: {result.stderr}")
                return []

            # Parse text logs
            logs = []
            for line in result.stdout.strip().split("\n"):
                if line.strip():
                    logs.append(
                        {
                            "message": line.strip(),
                            "timestamp": datetime.now().isoformat(),
                        }
                    )

            return logs

        except Exception as e:
            print(f"Exception fetching logs: {e}")
            return []

    def parse_http_status(self, message):
        """Extract HTTP status codes from log messages"""
        # Common patterns for HTTP status codes
        patterns = [
            r"\b([4-5]\d{2})\b",  # 4xx or 5xx status codes
            r"status[:\s]+([4-5]\d{2})",
            r"HTTP/\d\.\d\s+([4-5]\d{2})",
            r"response_status[:\s]+([4-5]\d{2})",
        ]

        status_codes = []
        for pattern in patterns:
            matches = re.findall(pattern, str(message), re.IGNORECASE)
            status_codes.extend(matches)

        return [int(code) for code in status_codes if code.isdigit()]

    def analyze_logs(self, logs):
        """Analyze logs for 4xx/5xx errors"""
        current_hour_errors = defaultdict(int)

        for log_entry in logs:
            try:
                message = log_entry.get("message", "")
                timestamp = log_entry.get("timestamp", "")

                # Extract HTTP status codes
                status_codes = self.parse_http_status(message)

                for status_code in status_codes:
                    if 400 <= status_code < 600:  # 4xx and 5xx errors
                        current_hour_errors[status_code] += 1

            except Exception as e:
                print(f"Error parsing log entry: {e}")
                continue

        return current_hour_errors

    def check_for_spikes(self, current_errors):
        """Check if current error counts indicate a spike"""
        total_errors = sum(current_errors.values())

        alerts = []

        # Check total error spike
        if total_errors > self.spike_threshold:
            alerts.append(
                f"HIGH ERROR SPIKE: {total_errors} errors in current period (threshold: {self.spike_threshold})"
            )

        # Check specific status code spikes
        for status_code, count in current_errors.items():
            if count > 20:  # Individual status code spike threshold
                alerts.append(f"Status {status_code} spike: {count} occurrences")

        return alerts

    def log_status(self, current_errors, alerts):
        """Log current monitoring status"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        total_errors = sum(current_errors.values())

        print(f"\n[{timestamp}] Log Monitor Status:")
        print(f"  Total 4xx/5xx errors in recent logs: {total_errors}")

        if current_errors:
            print("  Error breakdown:")
            for status_code, count in sorted(current_errors.items()):
                print(f"    {status_code}: {count}")
        else:
            print("  No 4xx/5xx errors detected ✓")

        if alerts:
            print("  🚨 ALERTS:")
            for alert in alerts:
                print(f"    - {alert}")
        else:
            print("  No alerts ✓")

        # Calculate monitoring progress
        elapsed = datetime.now() - self.start_time
        remaining = timedelta(seconds=self.monitor_duration) - elapsed
        progress = (elapsed.total_seconds() / self.monitor_duration) * 100

        print(f"  Monitoring progress: {progress:.1f}% ({remaining} remaining)")

    def run_monitoring(self):
        """Run 24-hour monitoring cycle"""
        print("🔍 Starting 24-hour log monitoring for Gary-Zero production")
        print(f"Start time: {self.start_time}")
        print(
            f"Checking every {self.check_interval / 60} minutes for 4xx/5xx error spikes"
        )
        print(f"Spike threshold: {self.spike_threshold} errors per check")
        print("-" * 60)

        end_time = self.start_time + timedelta(seconds=self.monitor_duration)
        check_count = 0

        try:
            while datetime.now() < end_time:
                check_count += 1
                print(f"\n📊 Check #{check_count}")

                # Fetch and analyze logs
                logs = self.get_railway_logs()
                current_errors = self.analyze_logs(logs)

                # Check for spikes
                alerts = self.check_for_spikes(current_errors)

                # Log status
                self.log_status(current_errors, alerts)

                # Store hourly data
                self.hourly_errors.append(
                    {
                        "timestamp": datetime.now(),
                        "errors": dict(current_errors),
                        "total": sum(current_errors.values()),
                        "alerts": alerts,
                    }
                )

                # Wait for next check
                if datetime.now() < end_time:
                    print(f"⏳ Next check in {self.check_interval / 60} minutes...")
                    time.sleep(self.check_interval)

        except KeyboardInterrupt:
            print("\n\n⚠️  Monitoring interrupted by user")
            self.generate_summary()
            return

        print("\n\n✅ 24-hour monitoring period completed!")
        self.generate_summary()

    def generate_summary(self):
        """Generate final monitoring summary"""
        print("\n" + "=" * 60)
        print("📋 24-HOUR MONITORING SUMMARY")
        print("=" * 60)

        if not self.hourly_errors:
            print("No monitoring data collected.")
            return

        total_checks = len(self.hourly_errors)
        total_errors = sum(entry["total"] for entry in self.hourly_errors)
        max_errors = (
            max(entry["total"] for entry in self.hourly_errors)
            if self.hourly_errors
            else 0
        )
        alert_periods = sum(1 for entry in self.hourly_errors if entry["alerts"])

        print(
            f"Monitoring period: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        print(f"Total checks performed: {total_checks}")
        print(f"Total 4xx/5xx errors detected: {total_errors}")
        print(f"Maximum errors in single check: {max_errors}")
        print(f"Alert periods: {alert_periods}/{total_checks}")

        if alert_periods == 0:
            print("\n✅ NO ERROR SPIKES DETECTED - Production is stable!")
        else:
            print(f"\n⚠️  {alert_periods} alert periods detected - Review recommended!")

        # Save detailed report
        report_file = (
            f"log_monitor_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )
        with open(report_file, "w") as f:
            json.dump(
                {
                    "monitoring_start": self.start_time.isoformat(),
                    "monitoring_end": datetime.now().isoformat(),
                    "total_checks": total_checks,
                    "total_errors": total_errors,
                    "max_errors": max_errors,
                    "alert_periods": alert_periods,
                    "hourly_data": [
                        {
                            "timestamp": entry["timestamp"].isoformat(),
                            "errors": entry["errors"],
                            "total": entry["total"],
                            "alerts": entry["alerts"],
                        }
                        for entry in self.hourly_errors
                    ],
                },
                f,
                indent=2,
            )

        print(f"\n📄 Detailed report saved to: {report_file}")


def main():
    """Main execution function"""
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        # Test mode - run for 2 minutes instead of 24 hours
        monitor = LogMonitor()
        monitor.monitor_duration = 120  # 2 minutes
        monitor.check_interval = 30  # Check every 30 seconds
        print("🧪 Running in TEST MODE (2 minutes)")
    else:
        monitor = LogMonitor()

    monitor.run_monitoring()


if __name__ == "__main__":
    main()
