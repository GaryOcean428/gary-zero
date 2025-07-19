#!/usr/bin/env python3
"""
Environment validation script for Gary-Zero production deployment
Validates all critical environment variables and configuration
"""

import os
import sys
from typing import Dict, List, Tuple, Any

# Add project root to path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

try:
    from framework.helpers import dotenv
    dotenv.load_dotenv()
except ImportError:
    print("⚠️  Warning: Could not import dotenv helper, using os.environ directly")
    dotenv = None

class EnvironmentValidator:
    """Validates environment configuration for production deployment"""
    
    def __init__(self):
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.info: List[str] = []
    
    def get_env_value(self, key: str, default: str = None) -> str:
        """Get environment variable value using dotenv helper if available"""
        if dotenv:
            return dotenv.get_dotenv_value(key, default)
        return os.environ.get(key, default)
    
    def validate_langchain_config(self) -> None:
        """Validate LangChain Anthropic configuration"""
        stream_usage = self.get_env_value("LANGCHAIN_ANTHROPIC_STREAM_USAGE", "true")
        
        if stream_usage.lower() == "false":
            self.info.append("✅ LangChain Anthropic streaming disabled (production hotfix active)")
        else:
            self.warnings.append("⚠️  LangChain Anthropic streaming enabled - may cause TypeError in production")
        
        # Check for Anthropic API key
        anthropic_key = self.get_env_value("ANTHROPIC_API_KEY")
        if not anthropic_key:
            self.warnings.append("⚠️  ANTHROPIC_API_KEY not set")
        elif anthropic_key.startswith("sk-"):
            self.info.append("✅ Anthropic API key configured")
        else:
            self.errors.append("❌ Invalid Anthropic API key format")
    
    def validate_feature_flags(self) -> None:
        """Validate development feature flags"""
        dev_features = self.get_env_value("ENABLE_DEV_FEATURES", "true").lower() == "true"
        vscode_integration = self.get_env_value("VSCODE_INTEGRATION_ENABLED", "true").lower() == "true"
        chat_auto_resize = self.get_env_value("CHAT_AUTO_RESIZE_ENABLED", "true").lower() == "true"
        node_env = self.get_env_value("NODE_ENV", "development")
        
        if node_env == "production":
            if not dev_features:
                self.info.append("✅ Development features disabled in production")
            else:
                self.warnings.append("⚠️  Development features enabled in production environment")
                
            if not vscode_integration:
                self.info.append("✅ VS Code integration disabled in production")
            else:
                self.warnings.append("⚠️  VS Code integration enabled in production (may impact performance)")
        
        if chat_auto_resize:
            self.info.append("✅ Chat input auto-resize enabled")
        else:
            self.warnings.append("⚠️  Chat input auto-resize disabled (reduced UX)")
    
    def validate_web_config(self) -> None:
        """Validate web server configuration"""
        host = self.get_env_value("WEB_UI_HOST", "localhost")
        port = self.get_env_value("WEB_UI_PORT", "50001")
        auth_login = self.get_env_value("AUTH_LOGIN")
        auth_password = self.get_env_value("AUTH_PASSWORD")
        
        if host == "0.0.0.0":
            self.info.append("✅ Web UI configured for external access")
        elif host == "localhost":
            self.warnings.append("⚠️  Web UI restricted to localhost only")
        
        try:
            port_num = int(port)
            if 1024 <= port_num <= 65535:
                self.info.append(f"✅ Web UI port {port_num} configured")
            else:
                self.warnings.append(f"⚠️  Web UI port {port_num} outside recommended range")
        except ValueError:
            self.errors.append(f"❌ Invalid Web UI port: {port}")
        
        if auth_login and auth_password:
            self.info.append("✅ Basic authentication configured")
        else:
            self.warnings.append("⚠️  Basic authentication not configured")
    
    def validate_railway_config(self) -> None:
        """Validate Railway-specific configuration"""
        railway_port = self.get_env_value("PORT")
        railway_env = self.get_env_value("RAILWAY_ENVIRONMENT")
        
        if railway_port:
            self.info.append(f"✅ Railway PORT configured: {railway_port}")
        else:
            self.warnings.append("⚠️  Railway PORT not set (may cause deployment issues)")
        
        if railway_env:
            self.info.append(f"✅ Railway environment: {railway_env}")
    
    def validate_security_config(self) -> None:
        """Validate security configuration"""
        jwt_secret = self.get_env_value("JWT_SECRET")
        api_key = self.get_env_value("API_KEY")
        
        if jwt_secret and len(jwt_secret) >= 32:
            self.info.append("✅ JWT secret configured with adequate length")
        elif jwt_secret:
            self.warnings.append("⚠️  JWT secret too short (< 32 characters)")
        else:
            self.warnings.append("⚠️  JWT secret not configured")
        
        if api_key:
            self.info.append("✅ API key configured")
        else:
            self.warnings.append("⚠️  API key not configured")
    
    def run_validation(self) -> Dict[str, Any]:
        """Run all validation checks"""
        print("🔍 Validating Gary-Zero environment configuration...\n")
        
        # Run all validation checks
        self.validate_langchain_config()
        self.validate_feature_flags()
        self.validate_web_config()
        self.validate_railway_config()
        self.validate_security_config()
        
        # Print results
        if self.errors:
            print("❌ ERRORS:")
            for error in self.errors:
                print(f"  {error}")
            print()
        
        if self.warnings:
            print("⚠️  WARNINGS:")
            for warning in self.warnings:
                print(f"  {warning}")
            print()
        
        if self.info:
            print("ℹ️  INFO:")
            for info in self.info:
                print(f"  {info}")
            print()
        
        # Summary
        total_issues = len(self.errors) + len(self.warnings)
        if self.errors:
            print(f"❌ Validation FAILED: {len(self.errors)} errors, {len(self.warnings)} warnings")
        elif self.warnings:
            print(f"⚠️  Validation PASSED with warnings: {len(self.warnings)} warnings")
        else:
            print("✅ Validation PASSED: All configurations look good!")
        
        return {
            "status": "failed" if self.errors else "warning" if self.warnings else "passed",
            "errors": self.errors,
            "warnings": self.warnings,
            "info": self.info,
            "total_issues": total_issues
        }

def main():
    """Main validation function"""
    validator = EnvironmentValidator()
    result = validator.run_validation()
    
    # Exit with appropriate code
    if result["status"] == "failed":
        sys.exit(1)
    elif result["status"] == "warning":
        sys.exit(2)  # Non-critical warnings
    else:
        sys.exit(0)  # Success

if __name__ == "__main__":
    main()