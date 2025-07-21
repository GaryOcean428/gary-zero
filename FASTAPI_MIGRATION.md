# Gary-Zero FastAPI Migration Guide

## Overview

This document describes the migration from Flask to FastAPI that has been implemented in Gary-Zero, providing enhanced performance, security, and Railway deployment optimization.

## Migration Summary

The migration maintains **backward compatibility** while introducing modern async capabilities and enhanced security features.

### Key Changes

1. **New FastAPI Application** (`main.py`)
   - Async/await support with uvicorn ASGI server
   - WebSocket endpoints for real-time communication
   - Pydantic v2 models for request/response validation
   - Railway-optimized middleware (CORS, GZip)
   - Comprehensive health and metrics endpoints

2. **Security Enhancements** (`security/validator.py`)
   - AST-based code validation
   - Configurable security levels (STRICT, MODERATE, PERMISSIVE)
   - Whitelist-based import filtering
   - Detection of dangerous functions and operations

3. **AI Model Registry** (`models/registry.py`)
   - Support for 9 AI providers (OpenAI, Anthropic, Google, etc.)
   - Model capability tracking (vision, function calling, etc.)
   - Cost estimation and usage statistics
   - Dynamic model recommendations

4. **Modern Python Packaging** (`pyproject.toml`)
   - PEP 621 compliant configuration
   - Proper dependency management
   - Development and optional dependencies

5. **Comprehensive Testing** (`tests/`)
   - 37+ tests across unit, integration, and performance categories
   - Async test support with pytest-asyncio
   - Complete coverage of new features

## Deployment Changes

### Railway Configuration

Updated `railway.toml` to use uvicorn with multiple workers:

```toml
[deploy]
startCommand = "uvicorn main:app --host 0.0.0.0 --port $PORT --workers 4 --loop uvloop"
healthcheckPath = "/health"
healthcheckTimeout = 30
restartPolicyType = "ON_FAILURE"
restartPolicyMaxRetries = 3
```

### Environment Variables

New environment variables for FastAPI:
- `RAILWAY_ENVIRONMENT`: Set to "production" in production
- `API_DOCS_ENABLED`: Controls API documentation availability
- `CORS_ORIGINS`: Configure CORS origins

## API Endpoints

### Legacy Compatibility

The existing Flask API endpoints remain available (though with limited functionality during transition):
- `/message` - Agent messaging
- `/settings_get` - Get settings
- `/settings_set` - Update settings
- `/health` - Health checks
- All other existing endpoints

### Enhanced FastAPI Endpoints

New enhanced endpoints with full async support:

#### Health & Monitoring
- `GET /health` - Comprehensive health check with system metrics
- `GET /ready` - Readiness check for Railway
- `GET /metrics` - Detailed application metrics

#### AI Models
- `GET /api/models` - List all available AI models
- `GET /api/models/{model_name}` - Get model details
- `POST /api/models/recommend` - Get model recommendations

#### Security
- `POST /api/validate-code` - Validate code for security issues

#### Real-time Communication
- `WebSocket /ws` - Real-time agent communication

## Security Features

### Code Validation

The new security validator provides multiple levels of protection:

```python
from security.validator import validate_code, SecurityLevel

# Validate user code
result = validate_code(user_code, SecurityLevel.STRICT)
if not result.is_valid:
    print("Blocked items:", result.blocked_items)
```

### Security Levels

- **STRICT**: Only basic Python modules (math, json, datetime, etc.)
- **MODERATE**: Includes requests, pathlib, and common data libraries
- **PERMISSIVE**: Adds scientific libraries (numpy, pandas, etc.)

## Model Registry Usage

### Getting Model Information

```python
from models.registry import get_registry, get_model

# Get all models
registry = get_registry()
models = registry.list_models()

# Get specific model
model = get_model("gpt-4o")
print(f"Cost: ${model.cost_per_1k_input_tokens}/1K tokens")
```

### Model Recommendations

```python
from models.registry import get_recommended_model

# Get recommendation for specific use case
model = get_recommended_model("coding", max_cost=0.01)
print(f"Recommended: {model.display_name}")
```

## Testing

### Running Tests

```bash
# Run all tests
pytest

# Run specific test categories
pytest tests/unit/           # Unit tests
pytest tests/integration/    # Integration tests
pytest tests/performance/    # Performance tests
pytest tests/e2e/           # End-to-end tests

# Run with coverage
pytest --cov=main --cov=security --cov=models
```

### Test Structure

```
tests/
├── unit/                  # Individual component tests
│   ├── test_security_validator.py
│   ├── test_model_registry.py
│   └── test_fastapi_app.py
├── integration/           # Multi-component tests
│   ├── test_api_bridge.py
│   └── test_multi_agent.py
├── e2e/                   # End-to-end workflows
│   └── test_web_ui.py
└── performance/           # Performance benchmarks
    └── test_concurrent_agents.py
```

## Migration Benefits

### Performance Improvements
- **Async/Await Support**: Non-blocking request handling
- **Multiple Workers**: Parallel request processing on Railway
- **WebSocket Support**: Real-time communication
- **Optimized Middleware**: GZip compression, CORS handling

### Security Enhancements
- **Code Validation**: AST-based security scanning
- **Input Sanitization**: Pydantic model validation
- **Rate Limiting**: Protection against abuse
- **Comprehensive Logging**: Security event tracking

### Developer Experience
- **Auto-Generated Docs**: OpenAPI/Swagger interface
- **Type Safety**: Pydantic models throughout
- **Modern Testing**: Comprehensive test suite
- **Better Error Handling**: Structured error responses

### Railway Optimization
- **Health Checks**: Proper readiness and liveness probes
- **Metrics Endpoint**: Application performance monitoring
- **Environment Management**: Production-ready configuration
- **Restart Policies**: Automatic failure recovery

## Backward Compatibility

The migration maintains compatibility with existing systems:

1. **Existing Flask App**: Still available at `run_ui.py`
2. **API Endpoints**: Legacy endpoints preserved with placeholders
3. **Agent System**: Existing agent code continues to work
4. **Configuration**: Environment variables and settings preserved

## Next Steps

1. **Complete Integration**: Full integration with existing agent system
2. **Performance Testing**: Load testing on Railway infrastructure
3. **Documentation Updates**: Update user guides and API docs
4. **Gradual Migration**: Phase out Flask components over time

## Troubleshooting

### Common Issues

1. **Import Conflicts**: The new `models/` directory may conflict with existing `models` imports
2. **Async Dependencies**: Some existing code may need async/await updates
3. **Environment Variables**: New variables need to be set in Railway

### Getting Help

- Check application logs: `GET /metrics` endpoint
- Review health status: `GET /health` endpoint  
- Validate code security: `POST /api/validate-code` endpoint
- Test model availability: `GET /api/models` endpoint

## Conclusion

The FastAPI migration provides a solid foundation for Gary-Zero's future development with improved performance, security, and scalability while maintaining compatibility with existing functionality.