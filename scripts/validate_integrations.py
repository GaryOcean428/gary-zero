#!/usr/bin/env python3
"""
Environment validation script for Gary Zero integrations.
Validates SearchXNG and E2B integrations for proper service connectivity.
"""

import os
import asyncio
import aiohttp
import sys


async def validate_integrations():
    """Validate SearchXNG and E2B integrations."""
    issues = []
    successes = []
    
    print("🔍 Validating Gary Zero service integrations...\n")
    
    # Check E2B integration
    await validate_e2b(issues, successes)
    
    # Check SearchXNG integration
    await validate_searchxng(issues, successes)
    
    # Check execution mode configuration
    validate_execution_config(issues, successes)
    
    # Print results
    print("\n" + "="*50)
    print("VALIDATION RESULTS")
    print("="*50)
    
    if successes:
        print("\n✅ WORKING INTEGRATIONS:")
        for success in successes:
            print(f"   {success}")
    
    if issues:
        print("\n❌ ISSUES FOUND:")
        for issue in issues:
            print(f"   {issue}")
        print(f"\nTotal issues: {len(issues)}")
        return False
    else:
        print("\n🎉 All integrations validated successfully!")
        return True


async def validate_e2b(issues, successes):
    """Validate E2B integration."""
    print("🔒 Checking E2B integration...")
    
    e2b_api_key = os.getenv('E2B_API_KEY')
    if not e2b_api_key:
        issues.append("E2B_API_KEY not configured")
        print("   ❌ E2B_API_KEY not found")
        return
    
    print("   ✓ E2B_API_KEY configured")
    
    try:
        # Try importing E2B executor
        from framework.executors.e2b_executor import E2BCodeExecutor
        print("   ✓ E2B executor module imported successfully")
        
        # Try initializing executor
        executor = E2BCodeExecutor()
        print("   ✓ E2B executor initialized")
        
        # Try creating a session (this will test the API key)
        session_id = executor.create_session()
        print(f"   ✓ E2B session created: {session_id}")
        
        # Clean up session
        executor.close_session(session_id)
        print("   ✓ E2B session cleaned up")
        
        successes.append("E2B integration working (cloud sandbox execution)")
        
    except ImportError as e:
        issues.append(f"E2B executor import failed: {e}")
        print(f"   ❌ E2B import failed: {e}")
    except Exception as e:
        issues.append(f"E2B integration failed: {e}")
        print(f"   ❌ E2B integration failed: {e}")


async def validate_searchxng(issues, successes):
    """Validate SearchXNG integration."""
    print("\n🔍 Checking SearchXNG integration...")
    
    searxng_url = os.getenv('SEARXNG_URL')
    if not searxng_url:
        issues.append("SEARXNG_URL not configured")
        print("   ❌ SEARXNG_URL not found")
        return
    
    print(f"   ✓ SEARXNG_URL configured: {searxng_url}")
    
    try:
        async with aiohttp.ClientSession() as session:
            # Test basic connectivity
            test_url = f"{searxng_url}/search"
            params = {'q': 'test', 'format': 'json'}
            
            print("   🔗 Testing SearchXNG connectivity...")
            
            async with session.get(test_url, params=params, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    results_count = len(data.get('results', []))
                    print(f"   ✓ SearchXNG responded successfully ({results_count} results)")
                    successes.append(f"SearchXNG integration working ({searxng_url})")
                else:
                    issues.append(f"SearchXNG returned status {response.status}")
                    print(f"   ❌ SearchXNG returned status {response.status}")
                    
    except aiohttp.ClientError as e:
        issues.append(f"SearchXNG connection failed: {e}")
        print(f"   ❌ SearchXNG connection failed: {e}")
    except asyncio.TimeoutError:
        issues.append("SearchXNG connection timeout")
        print("   ❌ SearchXNG connection timeout")
    except Exception as e:
        issues.append(f"SearchXNG error: {e}")
        print(f"   ❌ SearchXNG error: {e}")


def validate_execution_config(issues, successes):
    """Validate execution mode configuration."""
    print("\n⚙️  Checking execution configuration...")
    
    code_execution_mode = os.getenv('CODE_EXECUTION_MODE', 'ssh')
    disable_ssh = os.getenv('DISABLE_SSH_EXECUTION', 'false').lower() == 'true'
    e2b_api_key = os.getenv('E2B_API_KEY')
    
    print(f"   CODE_EXECUTION_MODE: {code_execution_mode}")
    print(f"   DISABLE_SSH_EXECUTION: {disable_ssh}")
    print(f"   E2B_API_KEY: {'SET' if e2b_api_key else 'NOT SET'}")
    
    # Check for Railway environment
    railway_env = os.getenv('RAILWAY_ENVIRONMENT')
    if railway_env:
        print(f"   RAILWAY_ENVIRONMENT: {railway_env}")
        if not disable_ssh:
            issues.append("Railway deployment should have DISABLE_SSH_EXECUTION=true")
        else:
            successes.append("Railway deployment properly configured")
    
    # Check execution mode consistency
    if code_execution_mode == 'direct' and not disable_ssh:
        issues.append("CODE_EXECUTION_MODE=direct but SSH not disabled")
    elif code_execution_mode == 'ssh' and disable_ssh:
        issues.append("CODE_EXECUTION_MODE=ssh but SSH execution disabled")
    else:
        successes.append(f"Execution mode configured correctly ({code_execution_mode})")


def main():
    """Main function to run validation."""
    try:
        result = asyncio.run(validate_integrations())
        sys.exit(0 if result else 1)
    except KeyboardInterrupt:
        print("\n\n❌ Validation interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n💥 Validation failed with error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()