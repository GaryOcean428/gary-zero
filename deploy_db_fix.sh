#!/bin/bash
# Railway Database Connection Fix Deployment Script

# Set color codes for output
GREEN="\033[0;32m"
RED="\033[0;31m"
YELLOW="\033[1;33m"
NC="\033[0m" # No Color

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
    env | grep -v "PASSWORD\|SECRET\|TOKEN\|KEY" | sort
    
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
print("
📋 Use these connection strings in your Railway variables:")
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
