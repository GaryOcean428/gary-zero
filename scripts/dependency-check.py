#!/usr/bin/env python3
"""
Comprehensive Dependency Check Utility for Gary Zero
Checks for unused dependencies, missing dependencies, and security issues
"""

import json
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Set, Any
import re

class DependencyChecker:
    def __init__(self):
        self.project_root = Path.cwd()
        self.package_json_path = self.project_root / "package.json"
        self.results = {}
    
    def load_package_json(self) -> Dict[str, Any]:
        """Load and parse package.json"""
        if not self.package_json_path.exists():
            raise FileNotFoundError("package.json not found")
        
        with open(self.package_json_path) as f:
            return json.load(f)
    
    def find_js_files(self) -> List[Path]:
        """Find all JavaScript files in the project"""
        js_files = []
        
        # Include webui directory
        webui_dir = self.project_root / "webui"
        if webui_dir.exists():
            js_files.extend(webui_dir.rglob("*.js"))
        
        # Include framework directory  
        framework_dir = self.project_root / "framework"
        if framework_dir.exists():
            js_files.extend(framework_dir.rglob("*.js"))
        
        # Include tests
        tests_dir = self.project_root / "tests"
        if tests_dir.exists():
            js_files.extend(tests_dir.rglob("*.js"))
        
        # Include root level JS files
        js_files.extend(self.project_root.glob("*.js"))
        
        # Filter out node_modules and other excluded directories
        excluded_patterns = ["node_modules", "dist", "build", ".git", "coverage"]
        filtered_files = []
        
        for file_path in js_files:
            if not any(pattern in str(file_path) for pattern in excluded_patterns):
                filtered_files.append(file_path)
        
        return filtered_files
    
    def extract_imports(self, file_path: Path) -> Set[str]:
        """Extract import statements from a JavaScript file"""
        imports = set()
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Pattern to match various import styles
            import_patterns = [
                r"import\s+.+\s+from\s+['\"]([^'\"]+)['\"]",  # ES6 imports
                r"require\(['\"]([^'\"]+)['\"]\)",  # CommonJS require
                r"import\(['\"]([^'\"]+)['\"]\)",  # Dynamic imports
            ]
            
            for pattern in import_patterns:
                matches = re.findall(pattern, content, re.MULTILINE)
                for match in matches:
                    # Skip relative imports and absolute paths
                    if not match.startswith('.') and not match.startswith('/'):
                        # Extract package name (before first slash if exists)
                        package_name = match.split('/')[0]
                        imports.add(package_name)
            
        except Exception as e:
            print(f"Warning: Could not read {file_path}: {e}")
        
        return imports
    
    def get_used_dependencies(self) -> Set[str]:
        """Find all dependencies used in the codebase"""
        js_files = self.find_js_files()
        used_deps = set()
        
        print(f"🔍 Scanning {len(js_files)} JavaScript files for imports...")
        
        for file_path in js_files:
            file_imports = self.extract_imports(file_path)
            used_deps.update(file_imports)
        
        return used_deps
    
    def check_unused_dependencies(self) -> Dict[str, List[str]]:
        """Check for unused dependencies"""
        package_json = self.load_package_json()
        used_deps = self.get_used_dependencies()
        
        all_deps = set()
        dependencies = package_json.get("dependencies", {})
        dev_dependencies = package_json.get("devDependencies", {})
        
        all_deps.update(dependencies.keys())
        all_deps.update(dev_dependencies.keys())
        
        unused_deps = all_deps - used_deps
        
        # Filter out known exceptions (dependencies that might not show up in imports)
        known_exceptions = {
            "husky",  # Git hooks
            "lint-staged",  # Pre-commit tool
            "prettier",  # Code formatter (CLI usage)
            "bundlesize",  # Bundle size checker
            "audit-ci",  # Security audit tool
            "jscpd",  # Copy-paste detector
            "ts-unused-exports",  # TypeScript tool
            "unimported",  # Dependency checker
            "pa11y-ci",  # Accessibility checker
            "@types/node",  # TypeScript types
        }
        
        # Remove known exceptions
        unused_deps = unused_deps - known_exceptions
        
        return {
            "unused_dependencies": list(unused_deps & set(dependencies.keys())),
            "unused_dev_dependencies": list(unused_deps & set(dev_dependencies.keys()))
        }
    
    def check_missing_dependencies(self) -> List[str]:
        """Check for missing dependencies (used but not declared)"""
        package_json = self.load_package_json()
        used_deps = self.get_used_dependencies()
        
        all_declared = set()
        all_declared.update(package_json.get("dependencies", {}).keys())
        all_declared.update(package_json.get("devDependencies", {}).keys())
        
        # Filter out built-in Node.js modules and browser APIs
        builtin_modules = {
            "fs", "path", "util", "crypto", "http", "https", "url", "querystring",
            "events", "stream", "buffer", "process", "os", "child_process"
        }
        
        # Filter out relative/absolute imports and built-ins
        external_deps = used_deps - builtin_modules
        
        missing_deps = external_deps - all_declared
        
        return list(missing_deps)
    
    def run_npm_audit(self) -> Dict[str, Any]:
        """Run npm audit and return results"""
        try:
            result = subprocess.run(
                ["npm", "audit", "--json"],
                capture_output=True,
                text=True,
                cwd=self.project_root
            )
            
            if result.stdout:
                audit_data = json.loads(result.stdout)
                return {
                    "vulnerabilities": audit_data.get("vulnerabilities", {}),
                    "metadata": audit_data.get("metadata", {}),
                    "audit_summary": audit_data.get("metadata", {})
                }
        except Exception as e:
            print(f"Warning: npm audit failed: {e}")
        
        return {"error": "npm audit failed"}
    
    def check_outdated_packages(self) -> Dict[str, Any]:
        """Check for outdated packages"""
        try:
            result = subprocess.run(
                ["npm", "outdated", "--json"],
                capture_output=True,
                text=True,
                cwd=self.project_root
            )
            
            if result.stdout:
                return json.loads(result.stdout)
        except Exception as e:
            print(f"Warning: npm outdated check failed: {e}")
        
        return {}
    
    def run_comprehensive_check(self) -> Dict[str, Any]:
        """Run all dependency checks"""
        print("🔍 Running comprehensive dependency analysis...")
        
        # Check for unused dependencies
        print("   Checking for unused dependencies...")
        unused = self.check_unused_dependencies()
        
        # Check for missing dependencies
        print("   Checking for missing dependencies...")
        missing = self.check_missing_dependencies()
        
        # Run security audit
        print("   Running security audit...")
        audit = self.run_npm_audit()
        
        # Check outdated packages
        print("   Checking for outdated packages...")
        outdated = self.check_outdated_packages()
        
        package_json = self.load_package_json()
        
        return {
            "project": {
                "name": package_json.get("name", "unknown"),
                "version": package_json.get("version", "unknown")
            },
            "dependencies": {
                "total_dependencies": len(package_json.get("dependencies", {})),
                "total_dev_dependencies": len(package_json.get("devDependencies", {})),
                "unused": unused,
                "missing": missing
            },
            "security": audit,
            "outdated": outdated,
            "recommendations": self.generate_recommendations(unused, missing, audit, outdated)
        }
    
    def generate_recommendations(self, unused, missing, audit, outdated) -> List[str]:
        """Generate actionable recommendations"""
        recommendations = []
        
        # Unused dependencies
        if unused["unused_dependencies"]:
            recommendations.append(f"📦 Remove {len(unused['unused_dependencies'])} unused dependencies: {', '.join(unused['unused_dependencies'][:3])}{'...' if len(unused['unused_dependencies']) > 3 else ''}")
        
        if unused["unused_dev_dependencies"]:
            recommendations.append(f"🛠️ Remove {len(unused['unused_dev_dependencies'])} unused dev dependencies: {', '.join(unused['unused_dev_dependencies'][:3])}{'...' if len(unused['unused_dev_dependencies']) > 3 else ''}")
        
        # Missing dependencies
        if missing:
            recommendations.append(f"⚠️ Add {len(missing)} missing dependencies: {', '.join(missing[:3])}{'...' if len(missing) > 3 else ''}")
        
        # Security issues
        if "metadata" in audit and audit["metadata"].get("vulnerabilities", {}).get("total", 0) > 0:
            total_vulns = audit["metadata"]["vulnerabilities"]["total"]
            recommendations.append(f"🔒 Fix {total_vulns} security vulnerabilities with 'npm audit fix'")
        
        # Outdated packages
        if outdated:
            recommendations.append(f"📅 Update {len(outdated)} outdated packages")
        
        if not recommendations:
            recommendations.append("✅ All dependencies look good!")
        
        return recommendations
    
    def print_results(self, results: Dict[str, Any]):
        """Print formatted results"""
        print("\n" + "="*60)
        print("📦 DEPENDENCY CHECK RESULTS")
        print("="*60)
        
        # Project info
        project = results["project"]
        print(f"Project: {project['name']} v{project['version']}")
        
        # Dependencies summary
        deps = results["dependencies"]
        print(f"\n📊 Dependencies Summary:")
        print(f"   Total Dependencies: {deps['total_dependencies']}")
        print(f"   Total Dev Dependencies: {deps['total_dev_dependencies']}")
        
        # Unused dependencies
        unused = deps["unused"]
        if unused["unused_dependencies"] or unused["unused_dev_dependencies"]:
            print(f"\n⚠️ Unused Dependencies:")
            if unused["unused_dependencies"]:
                print(f"   Dependencies: {', '.join(unused['unused_dependencies'])}")
            if unused["unused_dev_dependencies"]:
                print(f"   Dev Dependencies: {', '.join(unused['unused_dev_dependencies'])}")
        
        # Missing dependencies
        if deps["missing"]:
            print(f"\n❌ Missing Dependencies:")
            for missing in deps["missing"]:
                print(f"   - {missing}")
        
        # Security audit
        security = results["security"]
        if "metadata" in security:
            vulns = security["metadata"].get("vulnerabilities", {})
            if vulns.get("total", 0) > 0:
                print(f"\n🔒 Security Issues:")
                for severity, count in vulns.items():
                    if severity != "total" and count > 0:
                        print(f"   {severity.title()}: {count}")
        
        # Recommendations
        print(f"\n💡 Recommendations:")
        for rec in results["recommendations"]:
            print(f"   {rec}")

def main():
    checker = DependencyChecker()
    
    try:
        results = checker.run_comprehensive_check()
        checker.print_results(results)
        
        # Save results
        with open("dependency-check-results.json", "w") as f:
            json.dump(results, f, indent=2)
        
        print(f"\n📄 Full results saved to dependency-check-results.json")
        
        # Exit with error if there are issues
        has_issues = (
            results["dependencies"]["unused"]["unused_dependencies"] or
            results["dependencies"]["unused"]["unused_dev_dependencies"] or
            results["dependencies"]["missing"] or
            (results["security"].get("metadata", {}).get("vulnerabilities", {}).get("total", 0) > 0)
        )
        
        sys.exit(1 if has_issues else 0)
        
    except Exception as e:
        print(f"💥 Dependency check failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()