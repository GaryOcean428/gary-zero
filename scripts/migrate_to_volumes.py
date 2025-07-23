#!/usr/bin/env python3
"""
Migration script for existing Gary-Zero installations to use volume storage.
Safely migrates existing data to volume structure without data loss.
"""

import os
import shutil
from pathlib import Path


def migrate_existing_data():
    """Migrate existing data to volume structure"""
    data_dir = Path(os.getenv('DATA_DIR', '/app/data'))

    # Directories to migrate
    migration_paths = {
        '/app/memory': 'memory',
        '/app/logs': 'logs',
        '/app/knowledge': 'knowledge',
        '/app/work_dir': 'work_dir',
        '/app/reports': 'reports'
    }

    print("🔄 Starting data migration to volume structure...")

    # Ensure data directory exists
    data_dir.mkdir(parents=True, exist_ok=True)

    for old_path_str, subdir_name in migration_paths.items():
        old_path = Path(old_path_str)
        target_path = data_dir / subdir_name

        # Create target directory
        target_path.mkdir(parents=True, exist_ok=True)

        if old_path.exists() and not old_path.is_symlink():
            print(f"📦 Migrating {old_path} -> {target_path}")

            # Move all contents from old location to volume
            if old_path.is_dir() and any(old_path.iterdir()):
                for item in old_path.iterdir():
                    dest_item = target_path / item.name
                    if dest_item.exists():
                        print(f"⚠️  Skipping {item.name} (already exists in volume)")
                        continue
                    shutil.move(str(item), str(target_path))
                    print(f"✓ Moved {item.name}")

                # Remove the now-empty directory
                old_path.rmdir()
                print(f"✓ Removed empty directory {old_path}")

            elif old_path.is_file():
                # Handle case where directories might be files
                backup_file = target_path.parent / f"{old_path.name}.backup"
                shutil.move(str(old_path), str(backup_file))
                print(f"✓ Backed up file {old_path} to {backup_file}")

        # Create symlink from old location to volume location
        if not old_path.exists():
            old_path.symlink_to(target_path)
            print(f"🔗 Created symlink {old_path} -> {target_path}")
        elif old_path.is_symlink():
            print(f"✓ Symlink already exists: {old_path}")
        else:
            print(f"⚠️  {old_path} exists but is not a symlink - manual intervention needed")

def verify_migration():
    """Verify that migration completed successfully"""
    data_dir = Path(os.getenv('DATA_DIR', '/app/data'))

    required_dirs = ['memory', 'logs', 'knowledge', 'work_dir', 'reports']

    print("\n🔍 Verifying migration...")

    all_good = True
    for dir_name in required_dirs:
        volume_dir = data_dir / dir_name
        app_dir = Path(f'/app/{dir_name}')

        if not volume_dir.exists():
            print(f"❌ Volume directory missing: {volume_dir}")
            all_good = False
        elif not app_dir.is_symlink():
            print(f"❌ App directory is not a symlink: {app_dir}")
            all_good = False
        elif app_dir.readlink() != volume_dir:
            print(f"❌ Symlink points to wrong location: {app_dir} -> {app_dir.readlink()}")
            all_good = False
        else:
            print(f"✓ {dir_name}: Volume and symlink configured correctly")

    return all_good

def rollback_migration():
    """Rollback migration if something goes wrong"""
    print("🔄 Rolling back migration...")

    data_dir = Path(os.getenv('DATA_DIR', '/app/data'))
    migration_paths = ['memory', 'logs', 'knowledge', 'work_dir', 'reports']

    for subdir_name in migration_paths:
        app_path = Path(f'/app/{subdir_name}')
        volume_path = data_dir / subdir_name

        if app_path.is_symlink():
            app_path.unlink()
            print(f"✓ Removed symlink: {app_path}")

        if volume_path.exists():
            app_path.mkdir(parents=True, exist_ok=True)
            # Move data back
            for item in volume_path.iterdir():
                if item.name != '.gitkeep':
                    shutil.move(str(item), str(app_path))
                    print(f"✓ Moved back: {item.name}")

    print("✅ Migration rollback completed")

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == 'rollback':
        rollback_migration()
        exit(0)

    try:
        # Perform migration
        migrate_existing_data()

        # Verify it worked
        if verify_migration():
            print("\n🎉 Migration completed successfully!")
            print("Your data is now stored in the persistent volume and will survive deployments.")
        else:
            print("\n❌ Migration verification failed!")
            print("Run with 'rollback' argument to undo changes.")
            exit(1)

    except Exception as e:
        print(f"❌ Migration failed: {e}")
        print("Run with 'rollback' argument to undo any partial changes.")
        exit(1)
