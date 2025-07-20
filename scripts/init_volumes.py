#!/usr/bin/env python3
"""
Volume initialization script for Railway persistent storage.
Creates the directory structure needed for persistent data.
"""

import os
import json
from pathlib import Path

def initialize_volume_structure():
    """Initialize volume directory structure on first run"""
    data_dir = Path(os.getenv('DATA_DIR', '/app/data'))
    
    # Create all required subdirectories
    directories = [
        'memory',        # Agent persistent memory storage
        'logs',          # HTML CLI-style chat logs  
        'knowledge',     # Knowledge base and RAG data
        'work_dir',      # Agent working directory
        'reports',       # Generated analysis reports
        'scheduler',     # Task scheduling data
        'tmp'            # Temporary files
    ]
    
    print(f"Initializing volume structure at {data_dir}")
    
    for dir_name in directories:
        dir_path = data_dir / dir_name
        dir_path.mkdir(parents=True, exist_ok=True)
        print(f"✓ Created directory: {dir_path}")
    
    # Initialize scheduler tasks if not exists
    scheduler_file = data_dir / 'scheduler' / 'tasks.json'
    if not scheduler_file.exists():
        scheduler_file.write_text('[]')
        print(f"✓ Initialized scheduler tasks: {scheduler_file}")
    
    # Create .gitkeep files to ensure directories persist in git
    for dir_name in directories:
        gitkeep_file = data_dir / dir_name / '.gitkeep'
        if not gitkeep_file.exists():
            gitkeep_file.touch()
    
    print(f"✅ Volume structure initialized successfully at {data_dir}")
    return True

def create_symlinks():
    """Create symlinks from app directories to volume directories"""
    data_dir = Path(os.getenv('DATA_DIR', '/app/data'))
    app_dir = Path('/app')
    
    symlink_mappings = {
        'memory': app_dir / 'memory',
        'logs': app_dir / 'logs', 
        'knowledge': app_dir / 'knowledge',
        'work_dir': app_dir / 'work_dir',
        'reports': app_dir / 'reports'
    }
    
    print("Creating symlinks to volume directories...")
    
    for volume_subdir, app_path in symlink_mappings.items():
        volume_path = data_dir / volume_subdir
        
        # Remove existing directory/symlink if it exists
        if app_path.exists() or app_path.is_symlink():
            if app_path.is_symlink():
                app_path.unlink()
                print(f"✓ Removed existing symlink: {app_path}")
            elif app_path.is_dir():
                # Move existing data to volume before creating symlink
                import shutil
                if any(app_path.iterdir()):  # Directory is not empty
                    print(f"📦 Moving existing data from {app_path} to {volume_path}")
                    for item in app_path.iterdir():
                        shutil.move(str(item), str(volume_path))
                app_path.rmdir()
                print(f"✓ Moved existing directory: {app_path}")
        
        # Create symlink
        app_path.symlink_to(volume_path)
        print(f"✓ Created symlink: {app_path} -> {volume_path}")

if __name__ == "__main__":
    try:
        # Initialize volume directory structure
        initialize_volume_structure()
        
        # Create symlinks for seamless integration
        create_symlinks()
        
        print("\n🎉 Volume initialization completed successfully!")
        
    except Exception as e:
        print(f"❌ Volume initialization failed: {e}")
        exit(1)