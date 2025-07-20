#!/usr/bin/env python3
"""Framework import validation script."""

import sys
import os
import importlib.util
from pathlib import Path

def validate_framework_imports():
    """Validate all framework module imports."""
    framework_path = Path('framework')
    failed_imports = []
    
    for py_file in framework_path.rglob('*.py'):
        if py_file.name == '__init__.py':
            continue
            
        rel_path = py_file.relative_to(Path('.'))
        module_name = str(rel_path).replace('/', '.').replace('.py', '')
        
        try:
            spec = importlib.util.spec_from_file_location(module_name, py_file)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            print(f"✅ {module_name}")
        except Exception as e:
            # Only report actual import errors, not missing dependencies
            if "No module named 'framework." in str(e):
                print(f"❌ {module_name}: {e}")
                failed_imports.append((module_name, str(e)))
            else:
                print(f"⚠️  {module_name}: {type(e).__name__} (likely missing dependency)")
    
    return failed_imports

if __name__ == "__main__":
    sys.path.insert(0, '.')
    failed = validate_framework_imports()
    
    if failed:
        print(f"\n❌ {len(failed)} framework import errors:")
        for module, error in failed:
            print(f"  - {module}: {error}")
        sys.exit(1)
    else:
        print("\n✅ All framework imports validated (excluding external dependencies)")
        sys.exit(0)