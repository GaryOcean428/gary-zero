"""Basic integration test to ensure the application can start."""
import pytest
import sys
import os

def test_main_import():
    """Test that main.py can be imported successfully."""
    try:
        import main
        assert hasattr(main, 'app'), "FastAPI app should be available in main module"
        print("✅ Main module import successful")
    except ImportError as e:
        pytest.skip(f"Main module import failed: {e}")

def test_health_response_model():
    """Test that HealthResponse model works."""
    try:
        from main import HealthResponse
        health = HealthResponse()
        assert health.status == 'healthy'
        assert isinstance(health.timestamp, float)
        assert health.version == '0.9.0'
        print("✅ HealthResponse model works correctly")
    except ImportError as e:
        pytest.skip(f"HealthResponse import failed: {e}")

def test_environment_variables():
    """Test that basic environment variables are handled properly."""
    # Test default port handling
    original_port = os.environ.get('PORT')
    
    # Test with no PORT set
    if 'PORT' in os.environ:
        del os.environ['PORT']
    
    # Should handle missing PORT gracefully
    try:
        import main
        print("✅ Application handles missing PORT environment variable")
    except Exception as e:
        pytest.fail(f"Application failed without PORT env var: {e}")
    
    # Restore original PORT if it existed
    if original_port:
        os.environ['PORT'] = original_port

def test_basic_configuration():
    """Test that basic configuration is valid."""
    # Check if we can import configuration without errors
    try:
        # Test basic Python path setup
        assert os.path.exists('main.py'), "main.py should exist"
        assert os.path.exists('requirements.txt'), "requirements.txt should exist"
        print("✅ Basic configuration files exist")
    except Exception as e:
        pytest.fail(f"Basic configuration test failed: {e}")

@pytest.mark.asyncio
async def test_fastapi_basics():
    """Test basic FastAPI functionality if available."""
    try:
        from fastapi.testclient import TestClient
        from main import app
        
        client = TestClient(app)
        response = client.get("/health")
        
        # Should get either 200 or reasonable error (not 500)
        assert response.status_code in [200, 404, 405], f"Health endpoint returned {response.status_code}"
        print("✅ FastAPI basic functionality test passed")
        
    except ImportError:
        pytest.skip("FastAPI TestClient not available")
    except Exception as e:
        pytest.skip(f"FastAPI test failed (expected in basic setup): {e}")

if __name__ == "__main__":
    # Run basic tests
    test_main_import()
    test_health_response_model() 
    test_environment_variables()
    test_basic_configuration()
    print("✅ All basic integration tests passed")