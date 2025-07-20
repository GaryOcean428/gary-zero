# Secure Code Execution Framework

This document describes the implementation of secure, isolated code execution for the Gary Zero agent framework.

## Overview

The secure code execution framework provides enterprise-grade isolation for AI-generated code execution, replacing the previous direct host system execution with containerized/sandboxed alternatives.

## Architecture

### Core Components

1. **BaseCodeExecutor** - Abstract base class defining the execution interface
2. **E2BCodeExecutor** - Cloud-based sandbox execution using E2B (production)
3. **DockerCodeExecutor** - Local containerized execution (development)
4. **SecureCodeExecutionManager** - Intelligent executor selection and management

### Execution Flow

```
SecureCodeExecutionManager
├── E2B Available? → E2BCodeExecutor (Production)
├── Docker Available? → DockerCodeExecutor (Development)
└── Fallback → Warning (No secure execution)
```

## Security Features

### E2B Cloud Sandbox (Production)
- ✅ Enterprise-grade isolation
- ✅ ~150ms startup time
- ✅ Persistent sessions with state management
- ✅ Rich output support (charts, tables, etc.)
- ✅ File operations (upload/download/list)
- ✅ Automatic resource management

### Docker Container (Development)
- ✅ Local containerized execution
- ✅ Resource limits (512MB RAM, 50% CPU)
- ✅ Isolated filesystem with persistent volumes
- ✅ Network isolation
- ✅ Automatic cleanup

## Integration

### Enhanced Code Execution Tool

The existing `CodeExecution` tool has been enhanced with secure execution capabilities:

```python
# Original usage remains the same
runtime: "python" | "nodejs" | "terminal" | "reset"

# New runtime options
runtime: "secure_info" | "install"
```

### Backwards Compatibility

- ✅ Existing tool interface unchanged
- ✅ Automatic fallback to legacy execution if secure execution unavailable
- ✅ Session management preserved
- ✅ All existing runtime types supported

## Usage Examples

### Python Code Execution
```python
tool_args = {
    "runtime": "python",
    "code": "import pandas as pd; print(pd.__version__)"
}
```

### Package Installation
```python
tool_args = {
    "runtime": "install", 
    "package": "matplotlib"
}
```

### Security Information
```python
tool_args = {"runtime": "secure_info"}
```

## Environment Configuration

### Production (Railway)
```bash
E2B_API_KEY=your_e2b_api_key  # Already configured
```

### Development (Local)
```bash
# Docker daemon must be running
docker --version  # Verify Docker is available
```

## Testing

Run the test suite to verify functionality:

```bash
python test_secure_execution.py    # Core framework tests
python test_integration.py         # Integration tests
```

## Security Improvements

| Aspect | Before | After |
|--------|--------|-------|
| Execution Environment | Host system | Isolated containers/sandboxes |
| Resource Limits | None | Memory + CPU limits |
| File System Access | Full host access | Isolated workspace |
| Package Installation | Host environment pollution | Isolated package environment |
| State Management | Shell persistence | Secure session management |
| Network Access | Full host network | Controlled/isolated network |

## Future Enhancements

- [ ] Add support for additional language runtimes
- [ ] Implement execution time limits
- [ ] Add support for custom Docker images
- [ ] Integrate with monitoring and logging systems
- [ ] Add execution analytics and metrics