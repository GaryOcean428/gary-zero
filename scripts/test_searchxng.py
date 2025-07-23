#!/usr/bin/env python3
"""
Quick test script to verify SearchXNG connectivity.
Run this to check if SearchXNG is properly configured and accessible.
"""

import asyncio
import os
from datetime import datetime

import aiohttp


async def test_searchxng():
    """Test SearchXNG connectivity and configuration."""
    print("=" * 60)
    print("SearchXNG Connectivity Test")
    print("=" * 60)
    print(f"Time: {datetime.now().isoformat()}")
    print()

    # Check environment configuration
    searxng_url = os.getenv('SEARXNG_URL')
    search_provider = os.getenv('SEARCH_PROVIDER', 'duckduckgo')

    print("Configuration:")
    print(f"  SEARXNG_URL: {searxng_url or 'NOT SET'}")
    print(f"  SEARCH_PROVIDER: {search_provider}")

    # Check Railway environment
    railway_env = os.getenv('RAILWAY_ENVIRONMENT')
    if railway_env:
        print(f"  RAILWAY_ENVIRONMENT: {railway_env}")
        print(f"  RAILWAY_PROJECT_NAME: {os.getenv('RAILWAY_PROJECT_NAME', 'NOT SET')}")
        print(f"  RAILWAY_SERVICE_SEARXNG_URL: {os.getenv('RAILWAY_SERVICE_SEARXNG_URL', 'NOT SET')}")

    print()

    # Validate configuration
    if not searxng_url:
        print("❌ ERROR: SEARXNG_URL not configured")
        print("   Set SEARXNG_URL environment variable to your SearchXNG service URL")
        return False

    if '${{' in searxng_url:
        print("❌ ERROR: SEARXNG_URL contains unresolved reference variables")
        print(f"   Current value: {searxng_url}")
        print("   Make sure the searchxng service has a PORT environment variable set")
        return False

    # Test connectivity
    print(f"Testing connection to: {searxng_url}")
    print()

    try:
        async with aiohttp.ClientSession() as session:
            # Test 1: Basic connectivity
            print("Test 1: Basic connectivity...")
            test_url = f"{searxng_url}/search"
            params = {'q': 'test', 'format': 'json'}

            async with session.get(test_url, params=params, timeout=10) as response:
                print(f"  Response status: {response.status}")

                if response.status == 200:
                    data = await response.json()
                    results_count = len(data.get('results', []))
                    print(f"  ✅ SUCCESS: Got {results_count} results")

                    # Test 2: Actual search
                    print("\nTest 2: Performing actual search...")
                    params = {'q': 'Python programming', 'format': 'json'}

                    async with session.get(test_url, params=params, timeout=10) as response2:
                        if response2.status == 200:
                            data2 = await response2.json()
                            results_count2 = len(data2.get('results', []))
                            print(f"  ✅ SUCCESS: Got {results_count2} results for 'Python programming'")

                            # Show first result
                            if results_count2 > 0:
                                first_result = data2['results'][0]
                                print("\n  First result:")
                                print(f"    Title: {first_result.get('title', 'No title')}")
                                print(f"    URL: {first_result.get('url', 'No URL')}")
                        else:
                            print(f"  ❌ Test 2 failed with status: {response2.status}")
                else:
                    print(f"  ❌ FAILED: Got HTTP {response.status}")
                    try:
                        error_text = await response.text()
                        print(f"  Error response: {error_text[:200]}")
                    except:
                        pass

    except aiohttp.ClientError as e:
        print(f"  ❌ CONNECTION FAILED: {e}")
        print("\n  Possible causes:")
        print("  - SearchXNG service is not running")
        print("  - Network connectivity issues")
        print("  - Incorrect URL or port")
        return False

    except TimeoutError:
        print("  ❌ CONNECTION TIMEOUT")
        print("\n  SearchXNG is not responding within 10 seconds")
        return False

    except Exception as e:
        print(f"  ❌ UNEXPECTED ERROR: {e}")
        return False

    print("\n" + "=" * 60)
    print("✅ All tests passed! SearchXNG is properly configured.")
    print("=" * 60)
    return True


def main():
    """Main function to run the test."""
    # Load environment variables
    from framework.helpers import dotenv
    dotenv.load_dotenv()

    # Run the async test
    result = asyncio.run(test_searchxng())

    # Exit with appropriate code
    exit(0 if result else 1)


if __name__ == "__main__":
    main()
