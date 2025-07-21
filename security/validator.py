"""
Secure code validation module for Gary-Zero.

This module provides AST-based code validation to prevent execution of dangerous code,
implementing a whitelist approach for allowed imports and blocking unsafe functions.
"""

import ast
import logging
from typing import Set, List, Dict, Any, Optional
from pydantic import BaseModel, Field
from enum import Enum

logger = logging.getLogger(__name__)

class SecurityLevel(str, Enum):
    """Security levels for code execution."""
    STRICT = "strict"
    MODERATE = "moderate"
    PERMISSIVE = "permissive"

class ValidationResult(BaseModel):
    """Result of code validation."""
    is_valid: bool
    security_level: SecurityLevel
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    blocked_items: List[str] = Field(default_factory=list)

class CodeValidationRequest(BaseModel):
    """Request model for code validation."""
    code: str = Field(..., min_length=1, max_length=50000)
    security_level: SecurityLevel = SecurityLevel.STRICT
    allowed_modules: Optional[List[str]] = None

class SecurityError(Exception):
    """Custom exception for security validation errors."""
    pass

class SecureCodeValidator:
    """
    AST-based code validator for secure code execution.
    
    This validator parses submitted code using Python's AST to detect and block
    dangerous calls, unauthorized imports, and potentially unsafe operations.
    """
    
    def __init__(self, security_level: SecurityLevel = SecurityLevel.STRICT):
        self.security_level = security_level
        
        # Dangerous functions that should be blocked
        self.blocked_functions = {
            'eval', 'exec', 'compile', '__import__', 'globals', 'locals',
            'vars', 'dir', 'hasattr', 'getattr', 'setattr', 'delattr',
            'input', 'raw_input', 'reload', 'exit', 'quit'
        }
        
        # Dangerous modules that should be blocked
        self.blocked_modules = {
            'os', 'sys', 'subprocess', 'multiprocessing', 'threading',
            'importlib', 'imp', 'pkgutil', 'inspect', 'gc', 'ctypes',
            'platform', 'socket', 'urllib', 'http', 'ftplib', 'telnetlib',
            'smtplib', 'imaplib', 'poplib', 'pickle', 'shelve', 'marshal',
            'tempfile', 'shutil', 'glob', 'fnmatch', 'sqlite3', 'dbm'
        }
        
        # Allowed modules based on security level
        self.allowed_modules = {
            SecurityLevel.STRICT: {
                'math', 'datetime', 'time', 'random', 'string', 'itertools',
                'functools', 'operator', 'collections', 'heapq', 'bisect',
                'array', 'weakref', 'copy', 'json', 'csv', 'base64',
                'hashlib', 'hmac', 'uuid', 're', 'decimal', 'fractions'
            },
            SecurityLevel.MODERATE: {
                'math', 'datetime', 'time', 'random', 'string', 'itertools',
                'functools', 'operator', 'collections', 'heapq', 'bisect',
                'array', 'weakref', 'copy', 'json', 'csv', 'base64',
                'hashlib', 'hmac', 'uuid', 're', 'decimal', 'fractions',
                'requests', 'urllib3', 'http.client', 'pathlib', 'textwrap',
                'difflib', 'pprint', 'reprlib', 'enum', 'types', 'typing'
            },
            SecurityLevel.PERMISSIVE: {
                'math', 'datetime', 'time', 'random', 'string', 'itertools',
                'functools', 'operator', 'collections', 'heapq', 'bisect',
                'array', 'weakref', 'copy', 'json', 'csv', 'base64',
                'hashlib', 'hmac', 'uuid', 're', 'decimal', 'fractions',
                'requests', 'urllib3', 'http.client', 'pathlib', 'textwrap',
                'difflib', 'pprint', 'reprlib', 'enum', 'types', 'typing',
                'numpy', 'pandas', 'matplotlib', 'seaborn', 'sklearn',
                'scipy', 'sympy', 'statsmodels', 'networkx', 'beautifulsoup4',
                'lxml', 'pillow', 'opencv-python'
            }
        }
        
        # Dangerous attributes that should be blocked
        self.blocked_attributes = {
            '__globals__', '__locals__', '__dict__', '__class__', '__bases__',
            '__subclasses__', '__mro__', '__code__', '__func__', '__self__',
            '__module__', '__qualname__', '__annotations__', '__doc__'
        }
    
    def validate_code(self, request: CodeValidationRequest) -> ValidationResult:
        """
        Validate Python code for security issues.
        
        Args:
            request: Code validation request containing code and security settings
            
        Returns:
            ValidationResult with validation status and details
        """
        result = ValidationResult(
            is_valid=True,
            security_level=request.security_level
        )
        
        try:
            # Parse the code using AST
            tree = ast.parse(request.code)
            
            # Perform security checks
            self._check_imports(tree, result, request)
            self._check_function_calls(tree, result)
            self._check_attribute_access(tree, result)
            self._check_dangerous_operations(tree, result)
            
        except SyntaxError as e:
            result.is_valid = False
            result.errors.append(f"Syntax error: {str(e)}")
        except Exception as e:
            result.is_valid = False
            result.errors.append(f"Validation error: {str(e)}")
            logger.error(f"Code validation failed: {e}")
        
        # Final validation check
        if result.errors or result.blocked_items:
            result.is_valid = False
        
        return result
    
    def _check_imports(self, tree: ast.AST, result: ValidationResult, request: CodeValidationRequest):
        """Check for unauthorized imports."""
        allowed = request.allowed_modules or self.allowed_modules[request.security_level]
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    module_name = alias.name.split('.')[0]  # Get top-level module
                    if module_name in self.blocked_modules:
                        result.blocked_items.append(f"Blocked import: {alias.name}")
                    elif module_name not in allowed:
                        result.blocked_items.append(f"Unauthorized import: {alias.name}")
            
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    module_name = node.module.split('.')[0]  # Get top-level module
                    if module_name in self.blocked_modules:
                        result.blocked_items.append(f"Blocked import from: {node.module}")
                    elif module_name not in allowed:
                        result.blocked_items.append(f"Unauthorized import from: {node.module}")
    
    def _check_function_calls(self, tree: ast.AST, result: ValidationResult):
        """Check for dangerous function calls."""
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                # Check direct function calls
                if isinstance(node.func, ast.Name) and node.func.id in self.blocked_functions:
                    result.blocked_items.append(f"Blocked function: {node.func.id}")
                
                # Check method calls on dangerous modules
                elif isinstance(node.func, ast.Attribute):
                    if isinstance(node.func.value, ast.Name):
                        # Check for os.system, subprocess.call, etc.
                        if (node.func.value.id in self.blocked_modules and 
                            hasattr(node.func, 'attr')):
                            result.blocked_items.append(
                                f"Blocked method: {node.func.value.id}.{node.func.attr}"
                            )
    
    def _check_attribute_access(self, tree: ast.AST, result: ValidationResult):
        """Check for access to dangerous attributes."""
        for node in ast.walk(tree):
            if isinstance(node, ast.Attribute):
                if node.attr in self.blocked_attributes:
                    result.blocked_items.append(f"Blocked attribute access: {node.attr}")
    
    def _check_dangerous_operations(self, tree: ast.AST, result: ValidationResult):
        """Check for other dangerous operations."""
        for node in ast.walk(tree):
            # Check for exec/eval in string literals (updated for Python 3.14 compatibility)
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                if any(dangerous in node.value.lower() for dangerous in ['exec(', 'eval(', '__import__']):
                    result.warnings.append("Potentially dangerous string content detected")
            
            # Check for file operations
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                if node.func.id in ['open', 'file']:
                    result.warnings.append("File operation detected")
            
            # Check for network operations (in allowed modules)
            if (isinstance(node, ast.Call) and 
                isinstance(node.func, ast.Attribute) and
                isinstance(node.func.value, ast.Name)):
                if (node.func.value.id == 'requests' and 
                    node.func.attr in ['get', 'post', 'put', 'delete']):
                    result.warnings.append("Network operation detected")

# Global validator instance
_validator = SecureCodeValidator()

def validate_code(code: str, security_level: SecurityLevel = SecurityLevel.STRICT) -> ValidationResult:
    """
    Validate code using the global validator instance.
    
    Args:
        code: Python code to validate
        security_level: Security level for validation
        
    Returns:
        ValidationResult with validation details
    """
    request = CodeValidationRequest(
        code=code,
        security_level=security_level
    )
    return _validator.validate_code(request)

def is_code_safe(code: str, security_level: SecurityLevel = SecurityLevel.STRICT) -> bool:
    """
    Quick check if code is safe for execution.
    
    Args:
        code: Python code to check
        security_level: Security level for validation
        
    Returns:
        True if code is safe, False otherwise
    """
    result = validate_code(code, security_level)
    return result.is_valid