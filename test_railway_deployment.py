#!/usr/bin/env python3
"""
Test Railway deployment configuration and template substitution.
"""

import os
import sys
import tempfile
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def print_test_separator() -> None:
    """Output a visual separator between tests."""
    print("=" * 40)

def test_config_loader():
    """Test the configuration loader."""
    print("🧪 Testing configuration loader...")
    
    try:
        from framework.helpers.config_loader import get_config_loader
        
        config_loader = get_config_loader()
        
        # Test port resolution
        port = config_loader.get_port()
        print(f"✅ Port resolved: {port}")
        assert isinstance(port, int), f"Port should be int, got {type(port)}"
        assert 1 <= port <= 65535, f"Port should be in valid range, got {port}"
        
        # Test host resolution
        host = config_loader.get_host()
        print(f"✅ Host resolved: {host}")
        assert isinstance(host, str), f"Host should be string, got {type(host)}"
        
        # Test version info
        version_info = config_loader.get_version_info()
        print(f"✅ Version info: {version_info}")
        assert "version_no" in version_info, "Missing version_no"
        assert "version_time" in version_info, "Missing version_time"
        
        # Test feature flags config
        feature_flags = config_loader.get_feature_flags_config()
        print(f"✅ Feature flags generated: {len(feature_flags)} chars")
        assert "<script>" in feature_flags, "Feature flags should contain JavaScript"
        
        # Test validation
        validation = config_loader.validate_railway_config()
        print(f"✅ Configuration validation: {validation['valid']}")
        if validation["warnings"]:
            for warning in validation["warnings"]:
                print(f"⚠️  {warning}")
        if validation["issues"]:
            for issue in validation["issues"]:
                print(f"❌ {issue}")
        
        print("✅ Configuration loader tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Configuration loader test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_template_helper():
    """Test the template helper."""
    print("\n🧪 Testing template helper...")
    
    try:
        from framework.helpers.template_helper import get_template_helper
        
        template_helper = get_template_helper()
        
        # Create a test template
        test_template_content = """<!DOCTYPE html>
<html>
<head>
    <title>Test Template</title>
    {{feature_flags_config}}
</head>
<body>
    <h1>Version {{version_no}}</h1>
    <p>Build time: {{version_time}}</p>
</body>
</html>"""
        
        # Write test template to temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
            f.write(test_template_content)
            test_template_path = f.name
        
        try:
            # Test template rendering
            rendered = template_helper.render_html_template(test_template_path)
            print(f"✅ Template rendered: {len(rendered)} chars")
            
            # Verify placeholders are replaced
            assert "{{version_no}}" not in rendered, "version_no placeholder not replaced"
            assert "{{version_time}}" not in rendered, "version_time placeholder not replaced"
            assert "{{feature_flags_config}}" not in rendered, "feature_flags_config placeholder not replaced"
            assert "<script>" in rendered, "Feature flags script not injected"
            
            print("✅ Template helper tests passed!")
            return True
            
        finally:
            # Clean up temporary file
            os.unlink(test_template_path)
        
    except Exception as e:
        print(f"❌ Template helper test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_index_html_placeholders():
    """Test that index.html has the expected placeholders."""
    print("\n🧪 Testing index.html placeholders...")
    
    try:
        index_path = project_root / "webui" / "index.html"
        if not index_path.exists():
            print(f"❌ index.html not found at {index_path}")
            return False
        
        with open(index_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for expected placeholders
        expected_placeholders = ["{{version_no}}", "{{version_time}}", "{{feature_flags_config}}"]
        found_placeholders = []
        
        for placeholder in expected_placeholders:
            if placeholder in content:
                found_placeholders.append(placeholder)
        
        print(f"✅ Found placeholders in index.html: {found_placeholders}")
        
        if len(found_placeholders) != len(expected_placeholders):
            missing = set(expected_placeholders) - set(found_placeholders)
            print(f"⚠️  Missing placeholders: {missing}")
        
        # Test actual rendering
        from framework.helpers.template_helper import render_index_html
        rendered_html = render_index_html()
        
        # Verify placeholders are replaced
        remaining_placeholders = []
        for placeholder in expected_placeholders:
            if placeholder in rendered_html:
                remaining_placeholders.append(placeholder)
        
        if remaining_placeholders:
            print(f"❌ Placeholders not replaced: {remaining_placeholders}")
            return False
        
        print("✅ index.html template tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ index.html test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_railway_config_consistency():
    """Test Railway configuration file consistency."""
    print("\n🧪 Testing Railway configuration consistency...")
    
    try:
        # Check railway.toml
        railway_toml_path = project_root / "railway.toml"
        if railway_toml_path.exists():
            with open(railway_toml_path, 'r') as f:
                railway_content = f.read()
            
            if "python start_uvicorn.py" in railway_content:
                print("✅ railway.toml uses consistent startup command")
            else:
                print("❌ railway.toml startup command inconsistent")
                return False
        
        # Check nixpacks.toml
        nixpacks_toml_path = project_root / "nixpacks.toml"
        if nixpacks_toml_path.exists():
            with open(nixpacks_toml_path, 'r') as f:
                nixpacks_content = f.read()
            
            if "python start_uvicorn.py" in nixpacks_content:
                print("✅ nixpacks.toml uses consistent startup command")
            else:
                print("❌ nixpacks.toml startup command inconsistent")
                return False
        
        # Check Procfile
        procfile_path = project_root / "Procfile"
        if procfile_path.exists():
            with open(procfile_path, 'r') as f:
                procfile_content = f.read()
            
            if "python start_uvicorn.py" in procfile_content:
                print("✅ Procfile uses consistent startup command")
            else:
                print("❌ Procfile startup command inconsistent")
                return False
        
        print("✅ Railway configuration consistency tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Railway configuration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests."""
    print("🚀 Testing Railway deployment fixes...")
    
    # Set up test environment
    os.environ.setdefault("PORT", "8000")
    os.environ.setdefault("WEB_UI_HOST", "0.0.0.0")
    
    # Run tests
    tests = [
        test_config_loader,
        test_template_helper,
        test_index_html_placeholders,
        test_railway_config_consistency
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print_test_separator()  # Add spacing between tests
    
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed!")
        return 0
    else:
        print("❌ Some tests failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())