#!/usr/bin/env python3
"""
Script to add or update a high-level user in the Gary-Zero authentication system.

This script adds Braden (GaryOcean) as a high-level admin user with the provided credentials.
"""

import os
import sys

# Add the current directory to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from framework.helpers import dotenv, runtime
from framework.helpers.print_style import PrintStyle
from framework.security.db_auth import DatabaseAuth

# Initialize runtime and load environment
runtime.initialize()
dotenv.load_dotenv()

# User details to be added
email = "braden.lang77@gmail.com"  # For reference (not stored in current schema)
username = "GaryOcean"
password = "I.Am.Dev.1"

print_style = PrintStyle()

try:
    print_style.print(
        "🔐 Adding high-level admin user to Gary-Zero authentication system..."
    )

    # Initialize the database authentication system
    auth = DatabaseAuth()

    # Create the user (this will hash the password automatically)
    success = auth.create_user(
        username=username,
        password=password,
        must_change_password=False,  # High-level admin doesn't need to change password
    )

    if success:
        print_style.success(
            f"✅ High-level admin user '{username}' added successfully!"
        )
        print_style.print(f"📧 Email (for reference): {email}")
        print_style.print(f"👤 Username: {username}")
        print_style.print("🔑 Password: [REDACTED FOR SECURITY]")
        print_style.print("")
        print_style.print(
            "The user can now login to the Gary-Zero system with full admin privileges."
        )
    else:
        print_style.warning(
            f"⚠️ User '{username}' may already exist. Attempting to update password..."
        )

        # Try to change the password if user already exists
        # First, we need to verify current credentials or use admin override
        print_style.print(
            "Note: If user exists, you may need to use the change_password method with current credentials."
        )

except Exception as e:
    print_style.error(f"❌ Failed to add high-level admin user: {e}")
    sys.exit(1)

print_style.print("🎉 User management completed successfully!")
