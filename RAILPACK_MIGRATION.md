# Railway Deployment Migration: railway.toml → railpack.json

## Overview

This document details the migration from `railway.toml` to `railpack.json` for deployment configuration, along with the implementation of automated validation via CI/CD.

## Migration Summary

### Changes Made

1. **Configuration Format Migration**
   - Converted `railway.toml` → `railpack.json`
   - Maintained all existing deployment settings
   - Preserved builder configuration (NIXPACKS)

2. **JSON Schema Validation**
   - Created `.github/schemas/railpack.schema.json`
   - Implements Railway deployment standards
   - Validates required fields and constraints

3. **CI/CD Integration**
   - Added `railpack-validation.yml` workflow
   - Integrated validation into feature branch CI
   - Automatic PR comments on validation failures

### Key Configuration

**railpack.json Structure:**
```json
{
  "$schema": "./.github/schemas/railpack.schema.json",
  "builder": "NIXPACKS",
  "buildCommand": "bash scripts/build.sh",
  "startCommand": "bash scripts/start.sh", 
  "healthcheckPath": "/health",
  "healthcheckTimeout": 300,
  "restartPolicyType": "ON_FAILURE",
  "restartPolicyMaxRetries": 3,
  "environment": {
    "PORT": "${PORT}",
    "WEB_UI_HOST": "0.0.0.0",
    "PYTHONUNBUFFERED": "1",
    "TOKENIZERS_PARALLELISM": "false"
  },
  "services": {
    "web": {
      "source": "."
    }
  }
}
```

## Validation Rules

The CI validation enforces these requirements:

### Required Fields
- ✅ `builder` (must be: NIXPACKS, DOCKERFILE, or BUILDPACKS)
- ✅ `buildCommand` (non-empty string)
- ✅ `startCommand` (non-empty string)
- ✅ `healthcheckPath` (must start with `/`)

### PORT Environment Variable
- ✅ Must reference `${PORT}` in environment section OR
- ✅ Scripts must reference `$PORT` environment variable
- ❌ Fails if PORT is not properly configured

### Script File Validation
- ✅ Referenced scripts must exist
- ⚠️ Warns if scripts are not executable
- ✅ Validates build and start script paths

### Additional Checks
- ✅ JSON syntax validation
- ✅ JSON Schema compliance
- ✅ Dual validation with AJV and check-jsonschema

## CI/CD Integration

### Workflow Triggers
- Pull requests targeting `main` or `develop`
- Pushes to `main` branch
- Changes to:
  - `railpack.json`
  - `.github/schemas/railpack.schema.json`
  - `scripts/**`

### Validation Tools
- **AJV**: JSON Schema validation
- **check-jsonschema**: Alternative validation
- **jq**: JSON syntax and field extraction
- **bash**: Custom validation logic

### Failure Handling
- Automatic PR comments on validation failures
- Clear error messages and remediation steps
- Integration with feature branch status checks

## Benefits

1. **Better Validation**: Strict schema enforcement prevents deployment issues
2. **CI Integration**: Automated validation on every PR
3. **Clear Feedback**: Immediate feedback on configuration issues
4. **Railway Standards**: Enforces Railway deployment best practices
5. **Documentation**: Self-documenting schema with descriptions

## Migration Preservation

- `railway.toml` is kept for reference
- Added migration note to original file
- No breaking changes to existing deployment process
- Backward compatibility maintained

## Usage

### Local Validation
```bash
# Install validation tools
npm install -g ajv-cli
pip install check-jsonschema

# Validate configuration
ajv validate --spec=draft7 --schema=.github/schemas/railpack.schema.json --data=railpack.json
check-jsonschema --schemafile .github/schemas/railpack.schema.json railpack.json
```

### Schema Reference
The JSON schema is located at `.github/schemas/railpack.schema.json` and includes:
- Field requirements and constraints
- PORT reference validation
- Builder type validation
- Path format validation
- Environment variable naming rules

## Future Enhancements

Potential improvements to consider:
- Environment-specific validation rules
- Additional builder type support
- Webhook integration for deployment notifications
- Advanced healthcheck configuration validation
- Service dependency validation

---

**Migration completed successfully** ✅

All deployment configurations have been migrated to the new format with full CI validation support.
