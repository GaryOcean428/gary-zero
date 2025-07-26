import argparse
import json
import logging
import os
import shutil
from pathlib import Path

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def ensure_directory_exists(directory_path):
    """Ensure the directory exists, create if it doesn't."""
    try:
        Path(directory_path).mkdir(parents=True, exist_ok=True)
        return True
    except Exception as e:
        logger.error(f"Failed to create directory {directory_path}: {e}")
        return False


def migrate_settings(verify=False):
    """Migrate settings from legacy location to new location."""
    src = "/app/tmp/settings.json"
    dst = "/app/data/settings.json"

    logger.info("Starting settings migration...")

    # Check if source file exists
    if not os.path.exists(src):
        logger.info(f"Source settings.json not found at {src} - no migration needed")
        if verify:
            # For verification, we still check if target exists and is valid
            if os.path.exists(dst):
                try:
                    with open(dst) as f:
                        json.load(f)
                    logger.info(
                        "Verification: Destination settings.json exists and is valid"
                    )
                    return True
                except json.JSONDecodeError as e:
                    logger.error(
                        f"Verification failed: JSON decode error in {dst}: {e}"
                    )
                    return False
            else:
                logger.info("Verification: No settings file to migrate or verify")
                return True
        return True

    # Validate source JSON before migration
    try:
        with open(src) as f:
            source_data = json.load(f)
        logger.info(f"Source settings.json validated at {src}")
    except json.JSONDecodeError as e:
        logger.error(f"Source JSON decode error in {src}: {e}")
        return False
    except Exception as e:
        logger.error(f"Error reading source file {src}: {e}")
        return False

    # Ensure destination directory exists
    dst_dir = os.path.dirname(dst)
    if not ensure_directory_exists(dst_dir):
        logger.error(f"Failed to create destination directory {dst_dir}")
        return False

    # Check if destination already exists
    if os.path.exists(dst):
        logger.info(f"Destination settings.json already exists at {dst}")

        # Validate existing destination file
        try:
            with open(dst) as f:
                existing_data = json.load(f)
            logger.info("Existing destination settings.json is valid")

            # Compare source and destination (optional logging)
            if source_data == existing_data:
                logger.info("Source and destination settings are identical")
            else:
                logger.info(
                    "Source and destination settings differ - keeping existing destination"
                )

        except json.JSONDecodeError as e:
            logger.warning(
                f"Existing destination has JSON decode error: {e}. Overwriting with source."
            )
            try:
                shutil.copy2(src, dst)
                logger.info(f"Corrupted destination overwritten from {src}")
            except Exception as copy_error:
                logger.error(f"Failed to overwrite corrupted destination: {copy_error}")
                return False
        except Exception as e:
            logger.error(f"Error reading existing destination file {dst}: {e}")
            return False
    else:
        # Copy source to destination
        try:
            shutil.copy2(src, dst)
            logger.info(f"Settings successfully migrated from {src} to {dst}")
        except Exception as e:
            logger.error(f"Error copying settings.json from {src} to {dst}: {e}")
            return False

    # Final validation of destination
    try:
        with open(dst) as f:
            final_data = json.load(f)
        logger.info("Final validation: Destination settings.json is valid")
    except json.JSONDecodeError as e:
        logger.error(f"Final validation failed: JSON decode error in {dst}: {e}")
        return False
    except Exception as e:
        logger.error(f"Final validation failed: Error reading {dst}: {e}")
        return False

    logger.info("Settings migration completed successfully")

    if verify:
        logger.info("Verification mode: Migration validation passed")

    return True


def main():
    parser = argparse.ArgumentParser(description="Migration script for legacy settings")
    parser.add_argument(
        "--verify", action="store_true", help="Verify successful migration"
    )
    args = parser.parse_args()
    migrate_settings(verify=args.verify)


if __name__ == "__main__":
    main()
