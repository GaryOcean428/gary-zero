#!/usr/bin/env python3
"""
Script to test PostgreSQL database connection.
This script attempts to connect to the PostgreSQL database using the provided
connection string and runs some basic queries to validate the connection.
"""

import os
import socket
import sys
import time
import urllib.parse

import psycopg2

# Database connection parameters from Railway
# URL encode the password to handle special characters
DB_USER = "postgres"
DB_PASS = "SrtjmSLiWGHrUVQnGogqodYpNUQqzjsn"
DB_PASS_ENCODED = urllib.parse.quote_plus(DB_PASS)
DB_NAME = "railway"
DB_HOST_PUBLIC = "metro.proxy.rlwy.net"
DB_PORT_PUBLIC = 20783
DB_HOST_INTERNAL = "postgres.railway.internal"
DB_PORT_INTERNAL = 5432

DB_PUBLIC_URL = f"postgresql://{DB_USER}:{DB_PASS_ENCODED}@{DB_HOST_PUBLIC}:{DB_PORT_PUBLIC}/{DB_NAME}"
DB_INTERNAL_URL = f"postgresql://{DB_USER}:{DB_PASS_ENCODED}@{DB_HOST_INTERNAL}:{DB_PORT_INTERNAL}/{DB_NAME}"

# Try both encoded and non-encoded passwords
DB_PUBLIC_URL_DIRECT = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST_PUBLIC}:{DB_PORT_PUBLIC}/{DB_NAME}"

def test_socket_connection(host, port, timeout=5):
    """Test if we can connect to the host:port via socket."""
    print(f"🔍 Testing socket connection to {host}:{port}")
    start_time = time.time()
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((host, port))
        duration = time.time() - start_time
        if result == 0:
            print(f"✅ Socket connection to {host}:{port} successful (took {duration:.2f}s)")
            return True
        else:
            print(f"❌ Socket connection to {host}:{port} failed with error code {result} (took {duration:.2f}s)")
            return False
    except socket.gaierror:
        print(f"❌ Socket connection to {host}:{port} failed - hostname resolution failed")
        return False
    except Exception as e:
        print(f"❌ Socket connection to {host}:{port} failed with error: {e}")
        return False
    finally:
        try:
            sock.close()
        except:
            pass

def test_db_connection(connection_string, connection_name):
    """Test database connection using psycopg2."""
    print(f"\n🔍 Testing PostgreSQL connection to {connection_name}")
    print(f"Connection string: {connection_string}")

    try:
        start_time = time.time()
        conn = psycopg2.connect(connection_string)
        conn_time = time.time() - start_time

        print(f"✅ Connection to {connection_name} established successfully (took {conn_time:.2f}s)")

        # Test basic query execution
        with conn.cursor() as cursor:
            cursor.execute("SELECT version();")
            version = cursor.fetchone()
            print(f"PostgreSQL version: {version[0]}")

            cursor.execute("SELECT current_database();")
            db_name = cursor.fetchone()
            print(f"Current database: {db_name[0]}")

            cursor.execute("SELECT inet_server_addr();")
            server_addr = cursor.fetchone()
            print(f"Server address: {server_addr[0]}")

            # List tables in database
            cursor.execute("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
            """)
            tables = cursor.fetchall()
            if tables:
                print("Tables in database:")
                for table in tables:
                    print(f"  - {table[0]}")
            else:
                print("No tables found in database")

        conn.close()
        return True
    except Exception as e:
        print(f"❌ Connection to {connection_name} failed: {str(e)}")
        return False

def main():
    """Main function to test database connections."""
    print("🚀 Railway PostgreSQL Connection Test")
    print("=" * 50)

    # Test socket connections first
    print("\n📡 Testing socket connectivity...")
    public_socket = test_socket_connection(DB_HOST_PUBLIC, DB_PORT_PUBLIC)
    internal_socket = test_socket_connection(DB_HOST_INTERNAL, DB_PORT_INTERNAL)

    # Test PostgreSQL connections
    results = []

    if public_socket:
        # Try with URL-encoded password
        results.append(test_db_connection(DB_PUBLIC_URL, "Public URL (encoded password)"))

        # Try with direct password as fallback
        if not results[-1]:
            results.append(test_db_connection(DB_PUBLIC_URL_DIRECT, "Public URL (direct password)"))

        # Try with sslmode disabled as another fallback
        if not results[-1]:
            results.append(test_db_connection(
                f"{DB_PUBLIC_URL_DIRECT}?sslmode=disable",
                "Public URL (SSL disabled)"
            ))
    else:
        print("\n⚠️ Skipping public URL connection test due to socket connection failure")

    if internal_socket:
        results.append(test_db_connection(DB_INTERNAL_URL, "Internal URL"))
    else:
        print("\n⚠️ Skipping internal URL connection test due to socket connection failure")

    # Try some additional variations
    print("\n🔍 Testing additional connection parameters...")

    # Try direct connection with minimal parameters
    try:
        print("Attempting direct connection with minimal parameters...")
        conn = psycopg2.connect(
            host=DB_HOST_PUBLIC,
            port=DB_PORT_PUBLIC,
            user=DB_USER,
            password=DB_PASS,
            dbname=DB_NAME
        )
        print("✅ Direct connection successful!")
        conn.close()
        results.append(True)
    except Exception as e:
        print(f"❌ Direct connection failed: {e}")

    # Try connecting with sslmode=prefer
    try:
        print("Attempting connection with sslmode=prefer...")
        conn = psycopg2.connect(
            host=DB_HOST_PUBLIC,
            port=DB_PORT_PUBLIC,
            user=DB_USER,
            password=DB_PASS,
            dbname=DB_NAME,
            sslmode="prefer"
        )
        print("✅ Connection with sslmode=prefer successful!")
        conn.close()
        results.append(True)
    except Exception as e:
        print(f"❌ Connection with sslmode=prefer failed: {e}")

    # Test DNS resolution
    print("\n📡 Testing DNS resolution...")
    try:
        print(f"Resolving {DB_HOST_PUBLIC}...")
        ip = socket.gethostbyname(DB_HOST_PUBLIC)
        print(f"✅ {DB_HOST_PUBLIC} resolves to {ip}")
    except socket.gaierror as e:
        print(f"❌ Failed to resolve {DB_HOST_PUBLIC}: {e}")

    try:
        print(f"Resolving {DB_HOST_INTERNAL}...")
        ip = socket.gethostbyname(DB_HOST_INTERNAL)
        print(f"✅ {DB_HOST_INTERNAL} resolves to {ip}")
    except socket.gaierror as e:
        print(f"❌ Failed to resolve {DB_HOST_INTERNAL}: {e}")

    print("\n" + "=" * 50)
    if any(results):
        print("✅ At least one database connection was successful!")
        sys.exit(0)
    else:
        print("❌ All database connection attempts failed.")
        print("\nTroubleshooting steps:")
        print("1. Verify Railway service is running")
        print("2. Check for network connectivity issues")
        print("3. Verify database credentials")
        print("4. Check if Railway's services are functioning normally")
        sys.exit(1)

if __name__ == "__main__":
    main()
