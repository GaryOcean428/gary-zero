#!/usr/bin/env python3
"""
Railway PostgreSQL Database Test Script

This script is designed to be deployed on Railway to test database connectivity
within the Railway environment. It will attempt to connect to the PostgreSQL database
using environment variables provided by Railway.
"""

import os
import socket
import sys
import time

import psycopg2


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

        conn.close()
        return True
    except Exception as e:
        print(f"❌ Connection to {connection_name} failed: {str(e)}")
        return False

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

def main():
    """Main test function."""
    print("🚀 Railway PostgreSQL Connection Test")
    print("=" * 50)

    # Print all environment variables (helpful for diagnosis)
    print("\n📋 Environment Variables:")
    for key, value in sorted(os.environ.items()):
        # Only print keys and hide sensitive values for security
        if any(sensitive in key.lower() for sensitive in ['password', 'secret', 'key', 'token']):
            print(f"{key} = [REDACTED]")
        else:
            print(f"{key} = {value}")

    # Get database connection strings from environment
    db_url = os.getenv('DATABASE_URL')
    db_public_url = os.getenv('DATABASE_PUBLIC_URL')

    # Get Postgres-specific connection parameters
    pg_host = os.getenv('PGHOST')
    pg_port = os.getenv('PGPORT')
    pg_database = os.getenv('PGDATABASE')
    pg_user = os.getenv('PGUSER')
    pg_password = os.getenv('PGPASSWORD')

    # Test socket connections
    print("\n📡 Testing socket connectivity...")

    # Test connections to various endpoints
    if pg_host and pg_port:
        test_socket_connection(pg_host, int(pg_port))

    if 'postgres.railway.internal' != pg_host:
        test_socket_connection('postgres.railway.internal', 5432)

    # TCP proxy test if available
    tcp_proxy_domain = os.getenv('RAILWAY_TCP_PROXY_DOMAIN')
    tcp_proxy_port = os.getenv('RAILWAY_TCP_PROXY_PORT')
    if tcp_proxy_domain and tcp_proxy_port:
        test_socket_connection(tcp_proxy_domain, int(tcp_proxy_port))

    # Test PostgreSQL connections
    results = []

    # Test connection using DATABASE_URL
    if db_url:
        results.append(test_db_connection(db_url, "DATABASE_URL"))
    else:
        print("⚠️ DATABASE_URL environment variable not found")

    # Test connection using DATABASE_PUBLIC_URL
    if db_public_url:
        results.append(test_db_connection(db_public_url, "DATABASE_PUBLIC_URL"))
    else:
        print("⚠️ DATABASE_PUBLIC_URL environment variable not found")

    # Test connection using Postgres environment variables
    if all([pg_host, pg_port, pg_database, pg_user, pg_password]):
        pg_conn_string = f"host={pg_host} port={pg_port} dbname={pg_database} user={pg_user} password={pg_password}"
        results.append(test_db_connection(pg_conn_string, "Postgres Env Variables"))
    else:
        print("⚠️ Some Postgres environment variables are missing")

    # Try alternative connection methods with sslmode options
    print("\n🔄 Testing alternative connection methods...")

    if db_url:
        # Test with sslmode=prefer
        ssl_prefer_url = f"{db_url}?sslmode=prefer"
        results.append(test_db_connection(ssl_prefer_url, "DATABASE_URL with sslmode=prefer"))

        # Test with sslmode=disable
        ssl_disable_url = f"{db_url}?sslmode=disable"
        results.append(test_db_connection(ssl_disable_url, "DATABASE_URL with sslmode=disable"))

    # Check DNS resolution
    print("\n🔍 Testing DNS resolution...")
    hostnames = [
        'postgres.railway.internal',
        os.getenv('RAILWAY_PRIVATE_DOMAIN', ''),
        os.getenv('RAILWAY_PUBLIC_DOMAIN', ''),
        os.getenv('RAILWAY_TCP_PROXY_DOMAIN', '')
    ]

    for hostname in hostnames:
        if hostname:
            try:
                print(f"Resolving {hostname}...")
                ip = socket.gethostbyname(hostname)
                print(f"✅ {hostname} resolves to {ip}")
            except socket.gaierror as e:
                print(f"❌ Failed to resolve {hostname}: {e}")

    # Print summary
    print("\n" + "=" * 50)
    if any(results):
        print("✅ At least one database connection was successful!")
    else:
        print("❌ All database connection attempts failed.")
        print("Troubleshooting recommendations:")
        print("1. Check if the database service is running in Railway")
        print("2. Verify that the correct database credentials are being provided")
        print("3. Check for network restrictions or firewall issues")
        print("4. Ensure the database service is in the same Railway project and environment")
        print("5. Try restarting the database service")

if __name__ == "__main__":
    main()
