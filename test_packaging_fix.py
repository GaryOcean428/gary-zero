#!/usr/bin/env python3
"""
Test script to validate packaging dependency conflict resolution.

This test ensures that:
1. packaging module can be imported and has the correct version
2. e2b-code-interpreter can be imported without dependency conflicts  
3. Both packages are compatible with each other
"""

import sys
import subprocess
import pkg_resources


def test_packaging_version():
    """Test that packaging version satisfies the requirements."""
    try:
        import packaging
        from packaging import version
        
        packaging_version = version.parse(packaging.__version__)
        min_required = version.parse("24.1")
        max_allowed = version.parse("25.0")
        
        print(f"✓ packaging version: {packaging.__version__}")
        
        if packaging_version >= min_required and packaging_version < max_allowed:
            print(f"✓ packaging version {packaging.__version__} satisfies requirements (>=24.1,<25)")
            return True
        else:
            print(f"✗ packaging version {packaging.__version__} does not satisfy requirements (>=24.1,<25)")
            return False
            
    except ImportError as e:
        print(f"✗ Failed to import packaging: {e}")
        return False


def test_e2b_import():
    """Test that e2b-code-interpreter can be imported."""
    try:
        # Test core e2b import
        import e2b
        print(f"✓ e2b imported successfully, version: {e2b.__version__}")
        
        # Test e2b-code-interpreter import
        from e2b_code_interpreter import CodeInterpreter
        print("✓ e2b-code-interpreter imported successfully")
        return True
        
    except ImportError as e:
        print(f"✗ Failed to import e2b modules: {e}")
        return False


def test_dependency_compatibility():
    """Test that pip sees no dependency conflicts."""
    try:
        result = subprocess.run([
            sys.executable, "-m", "pip", "check"
        ], capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            print("✓ pip check passed - no dependency conflicts detected")
            return True
        else:
            print(f"✗ pip check failed:")
            print(result.stdout)
            print(result.stderr)
            return False
            
    except subprocess.TimeoutExpired:
        print("✗ pip check timed out")
        return False
    except Exception as e:
        print(f"✗ pip check failed with exception: {e}")
        return False


def main():
    """Run all tests and return success status."""
    print("Testing packaging dependency fix...")
    print("=" * 50)
    
    tests = [
        ("Packaging Version", test_packaging_version),
        ("E2B Import", test_e2b_import),
        ("Dependency Compatibility", test_dependency_compatibility)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{test_name}:")
        try:
            result = test_func()
            results.append(result)
        except Exception as e:
            print(f"✗ {test_name} failed with exception: {e}")
            results.append(False)
    
    print("\n" + "=" * 50)
    if all(results):
        print("✓ All tests passed! Packaging dependency conflict resolved.")
        return 0
    else:
        print("✗ Some tests failed. Check output above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())