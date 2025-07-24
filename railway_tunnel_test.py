#!/usr/bin/env python3
"""
Railway SSH Tunnel Database Test

This script tests connecting to a Railway PostgreSQL database via an SSH tunnel
using the railway proxy command. This is an alternative approach when direct
connections aren't working.
"""

import socket
import subprocess
import sys
import time

import psycopg2


def check_command_exists(command):
    """Check if a command exists on the system."""
    try:
        subprocess.check_output(["which", command])
        return True
    except subprocess.CalledProcessError:
        return False


def start_railway_tunnel(port=6432):
    """Start a Railway SSH tunnel on the specified port."""
    # Check if railway CLI is installed
    if not check_command_exists("railway"):
        print("❌ Railway CLI not found. Please install it with:")
        print("npm install -g @railway/cli")
        return False

    # Start the tunnel
    print(f"🔄 Starting Railway tunnel on port {port}...")

    # Use subprocess.Popen to run the tunnel in the background
    process = subprocess.Popen(
        ["railway", "connect", "postgres", f"--port={port}"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    # Give the tunnel a few seconds to establish
    time.sleep(5)

    # Check if the tunnel is running
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(3)
        result = sock.connect_ex(("127.0.0.1", port))
        sock.close()
        if result == 0:
            print(f"✅ Railway tunnel started on port {port}")
            return process
        else:
            print(f"❌ Failed to establish tunnel on port {port}")
            process.terminate()
            return False
    except Exception as e:
        print(f"❌ Error checking tunnel: {e}")
        process.terminate()
        return False


def test_tunneled_connection(port=6432):
    """Test connection to PostgreSQL via the Railway tunnel."""
    connection_string = f"postgresql://postgres:SrtjmSLiWGHrUVQnGogqodYpNUQqzjsn@localhost:{port}/railway"
    print("🔍 Testing PostgreSQL connection via tunnel")
    print(f"Connection string: {connection_string}")

    try:
        conn = psycopg2.connect(connection_string)
        print("✅ Connection successful!")

        # Test basic query execution
        with conn.cursor() as cursor:
            cursor.execute("SELECT version();")
            version = cursor.fetchone()
            print(f"PostgreSQL version: {version[0]}")

            cursor.execute("SELECT current_database();")
            db_name = cursor.fetchone()
            print(f"Current database: {db_name[0]}")

        conn.close()
        return True
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False


def main():
    """Main function."""
    print("🚀 Railway PostgreSQL SSH Tunnel Test")
    print("=" * 50)

    tunnel_port = 6432
    tunnel_process = start_railway_tunnel(tunnel_port)

    if not tunnel_process:
        print("❌ Could not establish Railway tunnel")
        sys.exit(1)

    try:
        # Test the connection via the tunnel
        success = test_tunneled_connection(tunnel_port)

        if success:
            print("\n✅ Successfully connected to PostgreSQL via Railway tunnel!")
            print(
                "==> This confirms your database is working but has connectivity issues"
            )
            print("==> Use the 'railway tunnel' approach for your application")
        else:
            print("\n❌ Failed to connect to PostgreSQL via Railway tunnel")
            print(
                "==> This indicates issues with your database credentials or configuration"
            )
    finally:
        # Clean up the tunnel process
        if tunnel_process:
            print("\n🔍 Stopping Railway tunnel...")
            tunnel_process.terminate()
            tunnel_process.wait()
            print("✅ Railway tunnel stopped")


if __name__ == "__main__":
    main()
