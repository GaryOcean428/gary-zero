# Changelog

All notable changes to Gary-Zero will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Removed
- **BREAKING**: Deprecated `railway-deployment.yml` GitHub workflow (superseded by railpack.json)
- **BREAKING**: Deprecated `nixpacks.toml` configuration file (superseded by railpack.json)

### Migration Notes

#### Railway Deployment Configuration Migration

**Date**: 2024-07-24

The project has migrated from legacy Railway deployment files to the new `railpack.json` standard:

**Removed Files:**
- `.github/workflows/railway-deployment.yml` - Legacy GitHub Actions workflow
- `nixpacks.toml` - Legacy Nixpacks configuration

**Superseded By:**
- `railpack.json` - New Railway deployment configuration with JSON schema validation
- `.github/workflows/railpack-validation.yml` - New CI/CD validation workflow
- `scripts/build.sh` and `scripts/start.sh` - Standardized deployment scripts

**Why This Change:**
1. **Better Validation**: JSON schema enforcement prevents deployment configuration errors
2. **CI Integration**: Automated validation on every pull request
3. **Railway Standards**: Compliance with Railway platform best practices
4. **Developer Experience**: Clear error messages and immediate feedback on configuration issues

**Action Required:**
- No action required for existing deployments - the migration maintains backward compatibility
- Future deployment configuration should be done via `railpack.json`
- Refer to [RAILPACK_MIGRATION.md](./RAILPACK_MIGRATION.md) for detailed migration documentation

**Key Benefits:**
- ✅ Strict schema validation prevents deployment failures  
- ✅ Automated CI/CD validation on pull requests
- ✅ Self-documenting configuration with JSON schema
- ✅ Enforcement of Railway deployment best practices
- ✅ Dynamic port binding validation for cloud environments

**For Developers:**
- All deployment changes should now be made in `railpack.json`
- The CI pipeline automatically validates configuration on every PR
- Local validation tools are available (see RAILPACK_MIGRATION.md)
- The old workflow files have been safely removed to prevent confusion

**Deployment Monitoring:**
After this change, monitor Railway deployment logs to confirm seamless operation:
1. Verify successful builds using `scripts/build.sh`
2. Confirm proper startup via `scripts/start.sh`
3. Check health endpoint accessibility at `/health`
4. Validate port binding on Railway-assigned PORT environment variable

## [0.9.0] - 2024-07-24

### Added
- Comprehensive Railway deployment standardization
- JSON schema validation for deployment configuration
- Automated CI/CD pipeline with security auditing
- Railpack.json configuration format with full validation
- Health check endpoint with proper Railway integration
- Dynamic port binding for cloud deployment environments

### Changed
- Migrated from railway.toml to railpack.json format
- Standardized build and start scripts for consistent deployment
- Enhanced CI/CD pipeline with comprehensive validation steps
- Improved error handling and deployment monitoring

### Security
- Added automated security scanning with OSSF Scorecard
- Implemented dependency vulnerability checking
- Enhanced secrets management and validation
- Added security audit reporting in CI/CD pipeline

### Infrastructure
- Railway deployment configuration standardization
- Docker build optimization and health check validation
- Container port binding validation for cloud environments
- Automated deployment script testing and validation

---

**Note**: This changelog will be maintained going forward to track all significant changes to the Gary-Zero project. For detailed technical documentation on specific migrations, see the corresponding documentation files in the repository root.
