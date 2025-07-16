#!/usr/bin/env python3
"""
Build Monitor for Railway Deployments
Monitors build process and provides warnings for timeout scenarios
"""

import logging
import subprocess
import sys
import time
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

def monitor_build():
    """Monitor the build process with timeout warnings"""
    start_time = time.time()
    start_datetime = datetime.now()

    logger.info("🚀 Railway build monitoring started")
    logger.info(f"⏰ Build started at {start_datetime.strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("📊 Monitoring for 30-minute timeout window")

    # Timeout thresholds (in seconds)
    warning_threshold = 1500  # 25 minutes
    critical_threshold = 1680  # 28 minutes
    max_timeout = 1800  # 30 minutes

    warning_sent = False
    critical_sent = False
    last_logged_interval = -1  # Track last 5-minute interval logged

    try:
        while True:
            elapsed = time.time() - start_time
            elapsed_minutes = elapsed / 60

            # Progress logging every 5 minutes
            current_interval = int(elapsed // 300)
            if current_interval != last_logged_interval:
                logger.info(f"📈 Build progress: {elapsed_minutes:.1f} minutes elapsed")
                last_logged_interval = current_interval

            # Warning at 25 minutes
            if elapsed > warning_threshold and not warning_sent:
                logger.warning(
                    f"⚠️  Build approaching timeout! Running for {elapsed_minutes:.1f} minutes"
                )
                logger.warning("🔄 Retry mechanism will activate if timeout occurs")
                warning_sent = True

            # Critical warning at 28 minutes
            if elapsed > critical_threshold and not critical_sent:
                logger.error(
                    f"🚨 CRITICAL: Build near timeout! {elapsed_minutes:.1f} minutes elapsed"
                )
                logger.error("⏱️  Less than 2 minutes remaining before timeout")
                critical_sent = True

            # Exit if we've reached the timeout
            if elapsed > max_timeout:
                logger.error("❌ Build timeout reached (30 minutes)")
                logger.error("🔄 Railway will attempt retry (3 attempts configured)")
                return False

            time.sleep(30)  # Check every 30 seconds

    except KeyboardInterrupt:
        elapsed_final = time.time() - start_time
        logger.info(f"🛑 Monitoring stopped. Total elapsed: {elapsed_final/60:.1f} minutes")
        return True
    except Exception as e:
        logger.error(f"❌ Monitor error: {e}")
        return False

def check_railway_config():
    """Verify Railway configuration is properly set"""
    try:
        import toml

        with open('railway.toml') as f:
            config = toml.load(f)

        build_config = config.get('build', {})
        timeout = build_config.get('timeout', 0)
        retries = build_config.get('retries', 0)

        logger.info("🔧 Railway configuration check:")
        logger.info(f"  ⏱️  Timeout: {timeout}s ({timeout/60:.1f} minutes)")
        logger.info(f"  🔄 Retries: {retries}")

        if timeout >= 1800 and retries >= 3:
            logger.info("✅ Railway timeout and retry configuration looks good")
            return True
        else:
            logger.warning("⚠️  Railway configuration may need adjustment")
            return False

    except ImportError:
        logger.warning("📦 toml package not available for config check")
        return None
    except Exception as e:
        logger.error(f"❌ Config check failed: {e}")
        return False

def test_uv_availability():
    """Test if UV package manager is available"""
    try:
        result = subprocess.run(['uv', '--version'],
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            logger.info(f"✅ UV available: {result.stdout.strip()}")
            return True
        else:
            logger.warning("⚠️  UV command failed")
            return False
    except subprocess.TimeoutExpired:
        logger.warning("⚠️  UV command timeout")
        return False
    except FileNotFoundError:
        logger.warning("❌ UV not found in PATH")
        return False
    except Exception as e:
        logger.error(f"❌ UV check failed: {e}")
        return False

if __name__ == "__main__":
    logger.info("🔍 Pre-build checks:")

    # Run configuration checks
    config_ok = check_railway_config()
    uv_ok = test_uv_availability()

    if '--check-only' in sys.argv:
        logger.info("📋 Check-only mode completed")
        sys.exit(0 if config_ok and uv_ok else 1)

    # Start monitoring
    success = monitor_build()
    sys.exit(0 if success else 1)
