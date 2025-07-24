#!/usr/bin/env python3
"""
Railway PostgreSQL Connection Fix

This script creates a new environment file with corrected database connection settings
for deployment to Railway. It detects if passwords need URL encoding and formats
connection strings properly.
"""

import os
import urllib.parse


def format_railway_env():
    """Format Railway environment variables correctly."""
    print("🔧 Railway PostgreSQL Connection Fix")
    print("=" * 50)

    # Get the password from Railway variables output
    password = "SrtjmSLiWGHrUVQnGogqodYpNUQqzjsn"

    # URL encode the password to handle special characters
    password_encoded = urllib.parse.quote_plus(password)

    # Create connection strings with encoded password
    internal_url = f"postgresql://postgres:{password_encoded}@postgres.railway.internal:5432/railway"
    public_url = (
        f"postgresql://postgres:{password_encoded}@metro.proxy.rlwy.net:20783/railway"
    )

    # Output the formatted environment variables
    env_vars = {
        "DATABASE_URL": internal_url,
        "DATABASE_PUBLIC_URL": public_url,
        "PGHOST": "postgres.railway.internal",
        "PGPORT": "5432",
        "PGUSER": "postgres",
        "PGPASSWORD": password,
        "PGDATABASE": "railway",
        "POSTGRES_USER": "postgres",
        "POSTGRES_PASSWORD": password,
        "POSTGRES_DB": "railway",
    }

    # Create .env file with proper formatting
    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env.railway")
    with open(env_path, "w") as f:
        for key, value in env_vars.items():
            f.write(f"{key}={value}\n")

    print(f"✅ Created environment file at: {env_path}")
    print("\nTo apply these settings to Railway:")
    print("1. Use `cat .env.railway` to view the file")
    print("2. Copy the contents to your Railway environment variables")
    print("3. Deploy your application again")

    print("\n📋 Environment Variables Preview:")
    for key, value in env_vars.items():
        if "PASSWORD" in key:
            print(f"{key}=[REDACTED]")
        else:
            print(f"{key}={value}")


def check_current_env():
    """Check for existing environment variables."""
    print("\n🔍 Checking for existing environment variables...")

    env_vars = [
        "DATABASE_URL",
        "DATABASE_PUBLIC_URL",
        "PGHOST",
        "PGPORT",
        "PGUSER",
        "PGPASSWORD",
        "PGDATABASE",
    ]

    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    found_vars = set()

    if os.path.exists(env_path):
        print(f"Found .env file at: {env_path}")
        with open(env_path) as f:
            for line in f:
                for var in env_vars:
                    if line.startswith(f"{var}="):
                        found_vars.add(var)
                        break

    for var in env_vars:
        if var in found_vars:
            print(f"✅ Found {var} in .env file")
        elif var in os.environ:
            print(f"✅ Found {var} in environment")
            found_vars.add(var)
        else:
            print(f"❌ Missing {var}")

    return found_vars


def create_migration_script():
    """Create a Railway deployment script for database migration."""
    script_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "deploy_db_fix.sh"
    )

    script_content = """#!/bin/bash
# Railway Database Connection Fix Deployment Script

# Set color codes for output
GREEN="\\033[0;32m"
RED="\\033[0;31m"
YELLOW="\\033[1;33m"
NC="\\033[0m" # No Color

echo -e "${YELLOW}=======================================${NC}"
echo -e "${YELLOW}Railway PostgreSQL Connection Fix${NC}"
echo -e "${YELLOW}=======================================${NC}"

# Install required packages
echo -e "${YELLOW}Installing required packages...${NC}"
pip install psycopg2-binary

# Create test database file
echo -e "${YELLOW}Creating database test script...${NC}"
cat > test_db_railway.py << 'EOL'
#!/usr/bin/env python3
import os
import sys
import psycopg2

def test_db():
    print("🔍 Testing database connections...")

    # Try internal URL first
    try:
        conn = psycopg2.connect(os.environ.get('DATABASE_URL'))
        print("✅ Successfully connected to DATABASE_URL")
        conn.close()
        return True
    except Exception as e:
        print(f"❌ Failed to connect to DATABASE_URL: {e}")

    # Try public URL as fallback
    try:
        conn = psycopg2.connect(os.environ.get('DATABASE_PUBLIC_URL'))
        print("✅ Successfully connected to DATABASE_PUBLIC_URL")
        conn.close()
        return True
    except Exception as e:
        print(f"❌ Failed to connect to DATABASE_PUBLIC_URL: {e}")

    # Try direct connection parameters
    try:
        conn = psycopg2.connect(
            host=os.environ.get('PGHOST'),
            port=os.environ.get('PGPORT'),
            user=os.environ.get('PGUSER'),
            password=os.environ.get('PGPASSWORD'),
            dbname=os.environ.get('PGDATABASE')
        )
        print("✅ Successfully connected using direct parameters")
        conn.close()
        return True
    except Exception as e:
        print(f"❌ Failed to connect using direct parameters: {e}")

    return False

if __name__ == "__main__":
    if test_db():
        print("✅ Database connection successful!")
        sys.exit(0)
    else:
        print("❌ All database connection attempts failed")
        sys.exit(1)
EOL

# Make the test script executable
chmod +x test_db_railway.py

# Run the test script
echo -e "${YELLOW}Testing database connection...${NC}"
if python test_db_railway.py; then
    echo -e "${GREEN}Database connection test passed!${NC}"
else
    echo -e "${RED}Database connection test failed!${NC}"
    echo -e "${YELLOW}Checking environment variables...${NC}"

    # Print environment variables (except sensitive ones)
    env | grep -v "PASSWORD\\|SECRET\\|TOKEN\\|KEY" | sort

    echo -e "${YELLOW}Creating URL-encoded connection strings...${NC}"

    # Create Python script to encode and test connection strings
    cat > fix_connection.py << 'EOL'
#!/usr/bin/env python3
import os
import sys
import urllib.parse
import psycopg2

# Get the password from environment
password = os.environ.get('PGPASSWORD')
if not password:
    print("❌ PGPASSWORD environment variable not found")
    sys.exit(1)

# URL encode the password to handle special characters
password_encoded = urllib.parse.quote_plus(password)

# Create connection strings with encoded password
internal_url = f"postgresql://postgres:{password_encoded}@postgres.railway.internal:5432/railway"
public_url = f"postgresql://postgres:{password_encoded}@metro.proxy.rlwy.net:20783/railway"

# Test the encoded connections
success = False

try:
    conn = psycopg2.connect(internal_url)
    print("✅ Successfully connected to internal URL with encoded password")
    conn.close()
    success = True
except Exception as e:
    print(f"❌ Failed to connect to internal URL: {e}")

try:
    conn = psycopg2.connect(public_url)
    print("✅ Successfully connected to public URL with encoded password")
    conn.close()
    success = True
except Exception as e:
    print(f"❌ Failed to connect to public URL: {e}")

# Print the connection strings for manual configuration
print("\n📋 Use these connection strings in your Railway variables:")
print(f"DATABASE_URL={internal_url}")
print(f"DATABASE_PUBLIC_URL={public_url}")

if success:
    sys.exit(0)
else:
    sys.exit(1)
EOL

    # Run the fix script
    chmod +x fix_connection.py
    echo -e "${YELLOW}Trying to fix connection strings...${NC}"
    python fix_connection.py
fi

echo -e "${YELLOW}=======================================${NC}"
echo -e "${YELLOW}Database configuration check complete${NC}"
echo -e "${YELLOW}=======================================${NC}"
"""

    with open(script_path, "w") as f:
        f.write(script_content)

    os.chmod(script_path, 0o755)  # Make executable

    print(f"✅ Created deployment script at: {script_path}")
    print("\nTo deploy this fix:")
    print("1. Add this script to your Railway deployment")
    print("2. Run it during the deployment process")
    print("3. Check the logs for connection status")


if __name__ == "__main__":
    format_railway_env()
    existing_vars = check_current_env()
    create_migration_script()

    print("\n📝 Summary:")
    if existing_vars:
        print(f"Found {len(existing_vars)} existing database environment variables")
        print(
            "⚠️ Your existing variables may need to be updated with URL-encoded passwords"
        )
    else:
        print("❌ No existing database environment variables found")
        print("✅ New variables have been generated in .env.railway")

    print("\n✨ Solution:")
    print("1. Use the new .env.railway file for correct database variables")
    print(
        "2. Deploy the deploy_db_fix.sh script to Railway to fix connections automatically"
    )
    print(
        "3. Update your application's database connection code to handle URL-encoded passwords"
    )
