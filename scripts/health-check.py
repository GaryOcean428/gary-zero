#!/usr/bin/env python3
"""
Comprehensive Health Check for Gary Zero
Validates error boundaries, routes, dependencies, and system health
"""

import asyncio
import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Any


class SystemHealthChecker:
    def __init__(self):
        self.results = {}
        self.start_time = time.time()

    def check_error_boundaries(self) -> dict[str, Any]:
        """Check error boundary implementation and coverage"""
        print("🛡️  Checking error boundaries...")

        # Check if error boundary file exists
        error_boundary_path = Path("webui/js/error-boundary.js")
        if not error_boundary_path.exists():
            return {
                "status": "fail",
                "message": "Error boundary file not found",
                "coverage": 0
            }

        # Read error boundary file and check implementation
        with open(error_boundary_path) as f:
            content = f.read()

        required_features = [
            "unhandledrejection",  # Promise rejection handling
            "error",  # JavaScript error handling
            "fetch",  # Network error handling
            "retry",  # Retry mechanism
            "logError",  # Error logging
            "reportError",  # Error reporting
        ]

        implemented_features = []
        for feature in required_features:
            if feature in content:
                implemented_features.append(feature)

        coverage = len(implemented_features) / len(required_features) * 100

        return {
            "status": "pass" if coverage >= 80 else "partial",
            "coverage": coverage,
            "implemented_features": implemented_features,
            "missing_features": [f for f in required_features if f not in implemented_features],
            "file_size": len(content),
            "global_initialization": "globalErrorBoundary" in content
        }

    def check_route_health(self) -> dict[str, Any]:
        """Check route configuration and health"""
        print("🛣️  Checking route health...")

        # Check main Flask application
        main_app_path = Path("run_ui.py")
        if not main_app_path.exists():
            return {"status": "fail", "message": "Main application file not found"}

        # Count API handlers
        api_dir = Path("framework/api")
        api_handlers = list(api_dir.glob("*.py")) if api_dir.exists() else []
        api_count = len([f for f in api_handlers if f.stem != "__init__"])

        # Check route definitions in main app
        with open(main_app_path) as f:
            app_content = f.read()

        static_routes = app_content.count("@webapp.route")
        error_handlers = app_content.count("@webapp.errorhandler")

        return {
            "status": "pass",
            "static_routes": static_routes,
            "api_handlers": api_count,
            "error_handlers": error_handlers,
            "total_routes": static_routes + api_count,
            "security_middleware": "add_security_headers" in app_content,
            "authentication": "requires_auth" in app_content,
            "health_endpoint": "/health" in app_content
        }

    def check_testing_coverage(self) -> dict[str, Any]:
        """Check test coverage and quality"""
        print("🧪 Checking test coverage...")

        tests_dir = Path("tests")
        if not tests_dir.exists():
            return {"status": "fail", "message": "Tests directory not found"}

        test_files = list(tests_dir.glob("*.test.js"))
        test_categories = {
            "error_boundary": any("error-boundary" in f.name for f in test_files),
            "component_loading": any("component-loading" in f.name for f in test_files),
            "alpine_integration": any("alpine" in f.name for f in test_files),
            "dom_fixes": any("dom-fixes" in f.name for f in test_files),
            "promise_handling": any("promise-rejection" in f.name for f in test_files),
        }

        coverage_percentage = sum(test_categories.values()) / len(test_categories) * 100

        return {
            "status": "pass" if coverage_percentage >= 70 else "partial",
            "test_files": len(test_files),
            "test_categories": test_categories,
            "coverage_percentage": coverage_percentage,
            "vitest_config": Path("vitest.config.js").exists(),
            "test_setup": Path("tests/setup.js").exists()
        }

    def check_code_quality(self) -> dict[str, Any]:
        """Check code quality metrics"""
        print("📊 Checking code quality...")

        # Run ESLint check
        try:
            result = subprocess.run(
                ["npm", "run", "lint:clean"],
                capture_output=True,
                text=True,
                timeout=60
            )

            lint_output = result.stdout + result.stderr

            # Parse ESLint output
            if "✖" in lint_output:
                # Extract error/warning counts
                lines = lint_output.split('\n')
                for line in lines:
                    if "problems" in line:
                        if "error" in line and "warning" in line:
                            parts = line.split()
                            errors = int(parts[1]) if len(parts) > 1 else 0
                            warnings = line.count("warning")
                        break
                else:
                    errors, warnings = 0, 0
            else:
                errors, warnings = 0, 0

            lint_status = "pass" if errors == 0 else "fail"

        except Exception as e:
            errors, warnings = -1, -1
            lint_status = "error"
            lint_output = str(e)

        # Check TypeScript configuration
        ts_config_exists = Path("tsconfig.json").exists()

        return {
            "status": lint_status,
            "eslint_errors": errors,
            "eslint_warnings": warnings,
            "typescript_config": ts_config_exists,
            "prettier_config": Path(".prettierrc").exists(),
            "biome_config": Path("biome.json").exists(),
            "lint_output_sample": lint_output[:500] if lint_output else ""
        }

    def check_security_status(self) -> dict[str, Any]:
        """Check security status"""
        print("🔒 Checking security status...")

        try:
            # Run npm audit
            result = subprocess.run(
                ["npm", "audit", "--json"],
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.stdout:
                audit_data = json.loads(result.stdout)
                vulnerabilities = audit_data.get("metadata", {}).get("vulnerabilities", {})
                total_vulns = vulnerabilities.get("total", 0)

                return {
                    "status": "pass" if total_vulns == 0 else "fail",
                    "total_vulnerabilities": total_vulns,
                    "critical": vulnerabilities.get("critical", 0),
                    "high": vulnerabilities.get("high", 0),
                    "moderate": vulnerabilities.get("moderate", 0),
                    "low": vulnerabilities.get("low", 0),
                    "audit_available": True
                }
        except Exception as e:
            return {
                "status": "error",
                "message": str(e),
                "audit_available": False
            }

    def check_dependencies(self) -> dict[str, Any]:
        """Check dependency health"""
        print("📦 Checking dependencies...")

        package_json_path = Path("package.json")
        if not package_json_path.exists():
            return {"status": "fail", "message": "package.json not found"}

        with open(package_json_path) as f:
            package_data = json.load(f)

        dependencies = package_data.get("dependencies", {})
        dev_dependencies = package_data.get("devDependencies", {})

        return {
            "status": "pass",
            "total_dependencies": len(dependencies),
            "dev_dependencies": len(dev_dependencies),
            "package_name": package_data.get("name", "unknown"),
            "version": package_data.get("version", "unknown"),
            "node_version_required": package_data.get("engines", {}).get("node", "unknown"),
            "scripts_count": len(package_data.get("scripts", {}))
        }

    async def run_comprehensive_check(self) -> dict[str, Any]:
        """Run all health checks"""
        print("🏥 Running comprehensive system health check...\n")

        checks = {
            "error_boundaries": self.check_error_boundaries(),
            "routes": self.check_route_health(),
            "testing": self.check_testing_coverage(),
            "code_quality": self.check_code_quality(),
            "security": self.check_security_status(),
            "dependencies": self.check_dependencies()
        }

        # Calculate overall health score
        health_scores = []
        for check_name, check_result in checks.items():
            if check_result.get("status") == "pass":
                health_scores.append(100)
            elif check_result.get("status") == "partial":
                # Use coverage percentage if available
                score = check_result.get("coverage", check_result.get("coverage_percentage", 50))
                health_scores.append(score)
            else:
                health_scores.append(0)

        overall_score = sum(health_scores) / len(health_scores) if health_scores else 0
        overall_status = "healthy" if overall_score >= 80 else "unhealthy" if overall_score < 50 else "warning"

        return {
            "timestamp": time.time(),
            "duration_seconds": time.time() - self.start_time,
            "overall": {
                "status": overall_status,
                "score": overall_score,
                "checks_passed": sum(1 for c in checks.values() if c.get("status") == "pass"),
                "total_checks": len(checks)
            },
            "checks": checks,
            "recommendations": self.generate_recommendations(checks)
        }

    def generate_recommendations(self, checks: dict[str, Any]) -> list[str]:
        """Generate actionable recommendations"""
        recommendations = []

        # Error boundary recommendations
        error_boundary = checks.get("error_boundaries", {})
        if error_boundary.get("coverage", 0) < 100:
            missing = error_boundary.get("missing_features", [])
            recommendations.append(f"🛡️ Improve error boundary coverage: implement {', '.join(missing[:3])}")

        # Code quality recommendations
        code_quality = checks.get("code_quality", {})
        if code_quality.get("eslint_errors", 0) > 0:
            recommendations.append(f"🔧 Fix {code_quality['eslint_errors']} ESLint errors")

        # Security recommendations
        security = checks.get("security", {})
        if security.get("total_vulnerabilities", 0) > 0:
            recommendations.append(f"🔒 Fix {security['total_vulnerabilities']} security vulnerabilities")

        # Testing recommendations
        testing = checks.get("testing", {})
        if testing.get("coverage_percentage", 0) < 80:
            recommendations.append("🧪 Increase test coverage to at least 80%")

        if not recommendations:
            recommendations.append("✅ All systems are healthy!")

        return recommendations

    def print_results(self, results: dict[str, Any]):
        """Print formatted health check results"""
        overall = results["overall"]

        print("\n" + "="*60)
        print("🏥 SYSTEM HEALTH CHECK RESULTS")
        print("="*60)

        # Overall status
        status_emoji = "🟢" if overall["status"] == "healthy" else "🟡" if overall["status"] == "warning" else "🔴"
        print(f"{status_emoji} Overall Status: {overall['status'].upper()}")
        print(f"📊 Health Score: {overall['score']:.1f}/100")
        print(f"✅ Checks Passed: {overall['checks_passed']}/{overall['total_checks']}")
        print(f"⏱️ Duration: {results['duration_seconds']:.2f}s")

        # Individual checks
        print("\n📋 Check Details:")
        for check_name, check_result in results["checks"].items():
            status = check_result.get("status", "unknown")
            emoji = "✅" if status == "pass" else "⚠️" if status == "partial" else "❌"

            print(f"   {emoji} {check_name.replace('_', ' ').title()}: {status}")

            # Additional details
            if check_name == "error_boundaries":
                coverage = check_result.get("coverage", 0)
                print(f"      Coverage: {coverage:.1f}%")
            elif check_name == "routes":
                total = check_result.get("total_routes", 0)
                print(f"      Total Routes: {total}")
            elif check_name == "code_quality":
                errors = check_result.get("eslint_errors", 0)
                warnings = check_result.get("eslint_warnings", 0)
                print(f"      Errors: {errors}, Warnings: {warnings}")
            elif check_name == "security":
                vulns = check_result.get("total_vulnerabilities", 0)
                print(f"      Vulnerabilities: {vulns}")

        # Recommendations
        print("\n💡 Recommendations:")
        for rec in results["recommendations"]:
            print(f"   {rec}")

async def main():
    checker = SystemHealthChecker()

    try:
        results = await checker.run_comprehensive_check()
        checker.print_results(results)

        # Save detailed results
        with open("health-check-results.json", "w") as f:
            json.dump(results, f, indent=2)

        print("\n📄 Detailed results saved to health-check-results.json")

        # Exit with appropriate code
        exit_code = 0 if results["overall"]["status"] == "healthy" else 1
        sys.exit(exit_code)

    except Exception as e:
        print(f"💥 Health check failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
