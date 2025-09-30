"""
Code Generator Module

Provides automated code generation, scaffolding, and template management
for rapid development and consistent code structure.
"""

import ast
import inspect
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import logging

from dataclasses import dataclass
from string import Template

logger = logging.getLogger(__name__)


@dataclass
class GeneratedFile:
    """Represents a generated file"""
    path: str
    content: str
    template_name: str
    variables: Dict[str, Any]
    created_at: datetime


@dataclass
class ScaffoldTemplate:
    """Template for scaffolding"""
    name: str
    description: str
    files: List[Dict[str, str]]  # [{path: template_path, content: template_content}]
    variables: List[str]
    dependencies: List[str]


class TemplateEngine:
    """Template processing engine"""
    
    def __init__(self):
        self._templates: Dict[str, str] = {}
        self._template_vars: Dict[str, Dict[str, Any]] = {}
        self._built_in_templates = self._load_built_in_templates()
    
    def register_template(self, name: str, content: str, variables: Optional[Dict[str, Any]] = None):
        """Register a new template"""
        self._templates[name] = content
        self._template_vars[name] = variables or {}
        logger.info(f"Registered template: {name}")
    
    def render_template(self, name: str, variables: Dict[str, Any]) -> str:
        """Render a template with variables"""
        if name not in self._templates:
            if name in self._built_in_templates:
                template_content = self._built_in_templates[name]
            else:
                raise ValueError(f"Template '{name}' not found")
        else:
            template_content = self._templates[name]
        
        # Merge with default variables
        all_vars = self._template_vars.get(name, {}).copy()
        all_vars.update(variables)
        
        # Add common variables
        all_vars.update({
            'timestamp': datetime.now().isoformat(),
            'date': datetime.now().strftime('%Y-%m-%d'),
            'year': datetime.now().year,
            'author': os.environ.get('USER', 'Developer')
        })
        
        # Render template
        template = Template(template_content)
        return template.safe_substitute(all_vars)
    
    def get_template_variables(self, name: str) -> List[str]:
        """Get required variables for a template"""
        if name not in self._templates:
            if name in self._built_in_templates:
                content = self._built_in_templates[name]
            else:
                return []
        else:
            content = self._templates[name]
        
        # Extract variables from template
        variables = re.findall(r'\$\{?(\w+)\}?', content)
        return list(set(variables))
    
    def _load_built_in_templates(self) -> Dict[str, str]:
        """Load built-in templates"""
        return {
            'python_module': '''"""
${description}

Generated on ${timestamp}
Author: ${author}
"""

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class ${class_name}:
    """${class_description}"""
    
    def __init__(self):
        self._initialized = True
        logger.info(f"Initialized {self.__class__.__name__}")
    
    def process(self, data: Any) -> Any:
        """Process data with intelligent analysis and transformation"""
        try:
            if isinstance(data, str):
                # Process string data - could be code, configuration, etc.
                return self._process_string(data)
            elif isinstance(data, dict):
                # Process dictionary data - configurations, metadata, etc.
                return self._process_dict(data)
            elif isinstance(data, list):
                # Process list data - arrays of configurations, file lists, etc.
                return self._process_list(data)
            else:
                # For other types, convert to string and process
                return self._process_string(str(data))
        except Exception as e:
            logger.error(f"Error processing data: {e}")
            return data
    
    def _process_string(self, text: str) -> str:
        """Process string data with intelligent transformations"""
        # Basic cleanup and formatting
        processed = text.strip()
        
        # If it looks like code, apply code formatting rules
        if any(keyword in processed for keyword in ['def ', 'class ', 'import ', 'from ']):
            # Python code processing
            processed = self._format_python_code(processed)
        elif processed.startswith('{') and processed.endswith('}'):
            # JSON processing
            try:
                import json
                parsed = json.loads(processed)
                processed = json.dumps(parsed, indent=2)
            except:
                pass
        elif processed.startswith('<') and processed.endswith('>'):
            # XML/HTML processing
            processed = self._format_xml(processed)
        
        return processed
    
    def _process_dict(self, data: dict) -> dict:
        """Process dictionary data with key transformations"""
        processed = {}
        for key, value in data.items():
            # Normalize keys (snake_case)
            normalized_key = key.lower().replace(' ', '_').replace('-', '_')
            
            # Recursively process values
            if isinstance(value, (dict, list, str)):
                processed[normalized_key] = self.process(value)
            else:
                processed[normalized_key] = value
        
        return processed
    
    def _process_list(self, data: list) -> list:
        """Process list data with element transformations"""
        return [self.process(item) for item in data]
    
    def _format_python_code(self, code: str) -> str:
        """Apply basic Python code formatting"""
        lines = code.split('\n')
        formatted_lines = []
        indent_level = 0
        
        for line in lines:
            stripped = line.strip()
            if not stripped:
                formatted_lines.append('')
                continue
            
            # Adjust indent for closing brackets/statements
            if stripped.startswith((')', '}', ']', 'except:', 'elif ', 'else:', 'finally:')):
                indent_level = max(0, indent_level - 1)
            
            # Add proper indentation
            formatted_lines.append('    ' * indent_level + stripped)
            
            # Increase indent for opening statements
            if stripped.endswith((':')) and any(stripped.startswith(kw) for kw in ['if ', 'for ', 'while ', 'def ', 'class ', 'try:', 'except:', 'with ', 'elif ', 'else:', 'finally:']):
                indent_level += 1
        
        return '\n'.join(formatted_lines)
    
    def _format_xml(self, xml: str) -> str:
        """Apply basic XML formatting"""
        try:
            import xml.dom.minidom
            dom = xml.dom.minidom.parseString(xml)
            return dom.toprettyxml(indent="  ")
        except:
            # If XML parsing fails, return original
            return xml


def ${function_name}(${parameters}) -> ${return_type}:
    """${function_description}"""
    # TODO: Implement function logic
    pass


if __name__ == "__main__":
    # Example usage
    instance = ${class_name}()
    result = instance.process("example")
    print(f"Result: {result}")
''',
            
            'test_module': '''"""
Test module for ${module_name}

Generated on ${timestamp}
Author: ${author}
"""

import pytest
import unittest
from unittest.mock import Mock, patch

from ${module_path} import ${class_name}, ${function_name}


class Test${class_name}(unittest.TestCase):
    """Test cases for ${class_name}"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.instance = ${class_name}()
    
    def tearDown(self):
        """Clean up after tests"""
        pass
    
    def test_initialization(self):
        """Test class initialization"""
        self.assertIsNotNone(self.instance)
        self.assertTrue(hasattr(self.instance, '_initialized'))
    
    def test_process_basic(self):
        """Test basic processing"""
        result = self.instance.process("test_data")
        self.assertIsNotNone(result)
    
    @patch('${module_path}.logger')
    def test_process_with_logging(self, mock_logger):
        """Test processing with logging"""
        self.instance.process("test_data")
        mock_logger.info.assert_called()


class Test${function_name}Functions(unittest.TestCase):
    """Test cases for standalone functions"""
    
    def test_${function_name}_basic(self):
        """Test ${function_name} basic functionality"""
        # TODO: Implement test
        pass
    
    def test_${function_name}_edge_cases(self):
        """Test ${function_name} edge cases"""
        # TODO: Implement edge case tests
        pass


if __name__ == "__main__":
    unittest.main()
''',
            
            'fastapi_endpoint': '''"""
FastAPI endpoint for ${endpoint_name}

Generated on ${timestamp}
Author: ${author}
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/${api_prefix}", tags=["${tags}"])


class ${model_name}Request(BaseModel):
    """Request model for ${endpoint_name}"""
    ${request_fields}


class ${model_name}Response(BaseModel):
    """Response model for ${endpoint_name}"""
    ${response_fields}


@router.get("/")
async def list_${resource_name}() -> List[${model_name}Response]:
    """List all ${resource_name}"""
    try:
        # TODO: Implement list logic
        return []
    except Exception as e:
        logger.error(f"Error listing ${resource_name}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{id}")
async def get_${resource_name}(id: str) -> ${model_name}Response:
    """Get ${resource_name} by ID"""
    try:
        # TODO: Implement get logic
        raise HTTPException(status_code=404, detail="${model_name} not found")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting ${resource_name} {id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/")
async def create_${resource_name}(request: ${model_name}Request) -> ${model_name}Response:
    """Create new ${resource_name}"""
    try:
        # TODO: Implement create logic
        return ${model_name}Response()
    except Exception as e:
        logger.error(f"Error creating ${resource_name}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.put("/{id}")
async def update_${resource_name}(id: str, request: ${model_name}Request) -> ${model_name}Response:
    """Update ${resource_name}"""
    try:
        # TODO: Implement update logic
        return ${model_name}Response()
    except Exception as e:
        logger.error(f"Error updating ${resource_name} {id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/{id}")
async def delete_${resource_name}(id: str):
    """Delete ${resource_name}"""
    try:
        # TODO: Implement delete logic
        return {"message": "${model_name} deleted successfully"}
    except Exception as e:
        logger.error(f"Error deleting ${resource_name} {id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
''',
            
            'docker_file': '''# Dockerfile for ${project_name}
# Generated on ${timestamp}

FROM python:${python_version}-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    build-essential \\
    curl \\
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd --create-home --shell /bin/bash ${app_user}
RUN chown -R ${app_user}:${app_user} /app
USER ${app_user}

# Expose port
EXPOSE ${port}

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \\
    CMD curl -f http://localhost:${port}/health || exit 1

# Run application
CMD ["python", "${main_file}"]
''',
            
            'github_workflow': '''name: ${workflow_name}

on:
  push:
    branches: [ ${main_branch} ]
  pull_request:
    branches: [ ${main_branch} ]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [${python_versions}]
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python $${{ matrix.python-version }}
      uses: actions/setup-python@v3
      with:
        python-version: $${{ matrix.python-version }}
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install -r requirements-dev.txt
    
    - name: Lint with flake8
      run: |
        flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
        flake8 . --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics
    
    - name: Test with pytest
      run: |
        pytest --cov=${package_name} --cov-report=xml
    
    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
        fail_ci_if_error: true
''',
            
            'makefile': '''# Makefile for ${project_name}
# Generated on ${timestamp}

.PHONY: help install dev test lint format clean build deploy

help:  ## Show this help
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "\\033[36m%-20s\\033[0m %s\\n", $$1, $$2}' $(MAKEFILE_LIST)

install:  ## Install dependencies
	pip install -r requirements.txt

dev:  ## Install development dependencies
	pip install -r requirements-dev.txt
	pre-commit install

test:  ## Run tests
	pytest tests/ -v --cov=${package_name}

lint:  ## Run linting
	flake8 ${package_name}/ tests/
	mypy ${package_name}/
	black --check ${package_name}/ tests/

format:  ## Format code
	black ${package_name}/ tests/
	isort ${package_name}/ tests/

clean:  ## Clean build artifacts
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	find . -type d -name __pycache__ -delete
	find . -type f -name "*.pyc" -delete

build:  ## Build package
	python setup.py sdist bdist_wheel

deploy:  ## Deploy to production
	# TODO: Implement deployment logic
	@echo "Deploying ${project_name}..."

dev-server:  ## Start development server
	python ${main_file} --dev

prod-server:  ## Start production server
	gunicorn --bind 0.0.0.0:${port} ${wsgi_module}:app
'''
        }


class CodeGenerator:
    """Main code generator with intelligent code analysis and generation"""
    
    def __init__(self):
        self._template_engine = TemplateEngine()
        self._generated_files: List[GeneratedFile] = []
    
    def generate_from_template(
        self, 
        template_name: str, 
        output_path: str, 
        variables: Dict[str, Any],
        overwrite: bool = False
    ) -> GeneratedFile:
        """Generate code from template"""
        if Path(output_path).exists() and not overwrite:
            raise FileExistsError(f"File {output_path} already exists")
        
        # Render template
        content = self._template_engine.render_template(template_name, variables)
        
        # Create directory if needed
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Write file
        with open(output_path, 'w') as f:
            f.write(content)
        
        # Track generated file
        generated_file = GeneratedFile(
            path=output_path,
            content=content,
            template_name=template_name,
            variables=variables,
            created_at=datetime.now()
        )
        
        self._generated_files.append(generated_file)
        logger.info(f"Generated file: {output_path}")
        
        return generated_file
    
    def generate_class_from_interface(
        self, 
        interface_class: type, 
        implementation_name: str,
        output_path: str
    ) -> GeneratedFile:
        """Generate class implementation from interface"""
        # Analyze interface
        methods = []
        for name, method in inspect.getmembers(interface_class, inspect.isfunction):
            if not name.startswith('_'):
                signature = inspect.signature(method)
                methods.append({
                    'name': name,
                    'params': list(signature.parameters.keys()),
                    'return_type': signature.return_annotation.__name__ if signature.return_annotation != inspect.Signature.empty else 'Any',
                    'docstring': inspect.getdoc(method) or f"Implementation of {name}"
                })
        
        # Generate implementation
        class_template = '''"""
Implementation of ${interface_name}

Generated on ${timestamp}
"""

from typing import Any
import logging

logger = logging.getLogger(__name__)


class ${implementation_name}(${interface_name}):
    """${interface_name} implementation"""
    
    def __init__(self):
        super().__init__()
        logger.info(f"Initialized {self.__class__.__name__}")
    
${method_implementations}
'''
        
        method_implementations = []
        for method in methods:
            params_str = ', '.join(method['params'])
            method_impl = f'''    def {method['name']}(self{', ' + params_str if params_str != 'self' else ''}) -> {method['return_type']}:
        """{method['docstring']}"""
        # TODO: Implement {method['name']}
        raise NotImplementedError("Method {method['name']} not implemented")
'''
            method_implementations.append(method_impl)
        
        variables = {
            'interface_name': interface_class.__name__,
            'implementation_name': implementation_name,
            'method_implementations': '\n'.join(method_implementations)
        }
        
        self._template_engine.register_template('class_implementation', class_template)
        return self.generate_from_template('class_implementation', output_path, variables)
    
    def generate_crud_api(
        self, 
        model_name: str, 
        fields: Dict[str, str],
        output_dir: str
    ) -> List[GeneratedFile]:
        """Generate complete CRUD API"""
        generated_files = []
        
        # Generate model
        model_fields = []
        for field_name, field_type in fields.items():
            model_fields.append(f"    {field_name}: {field_type}")
        
        model_content = f'''"""
{model_name} data model

Generated on {datetime.now().isoformat()}
"""

from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class {model_name}Base(BaseModel):
    """Base {model_name} model"""
{chr(10).join(model_fields)}


class {model_name}Create({model_name}Base):
    """Create {model_name} model"""
    pass


class {model_name}Update({model_name}Base):
    """Update {model_name} model"""
    pass


class {model_name}Response({model_name}Base):
    """Response {model_name} model"""
    id: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
'''
        
        model_file = GeneratedFile(
            path=f"{output_dir}/models.py",
            content=model_content,
            template_name="crud_model",
            variables={"model_name": model_name, "fields": fields},
            created_at=datetime.now()
        )
        
        # Write model file
        Path(f"{output_dir}/models.py").parent.mkdir(parents=True, exist_ok=True)
        with open(f"{output_dir}/models.py", 'w') as f:
            f.write(model_content)
        
        generated_files.append(model_file)
        
        # Generate API endpoints
        api_variables = {
            'endpoint_name': model_name.lower(),
            'model_name': model_name,
            'resource_name': model_name.lower() + 's',
            'api_prefix': model_name.lower(),
            'tags': model_name.lower(),
            'request_fields': '\n    '.join([f"{name}: {type_}" for name, type_ in fields.items()]),
            'response_fields': '\n    '.join([f"{name}: {type_}" for name, type_ in fields.items()])
        }
        
        api_file = self.generate_from_template(
            'fastapi_endpoint',
            f"{output_dir}/api.py",
            api_variables
        )
        generated_files.append(api_file)
        
        # Generate tests
        test_variables = {
            'module_name': model_name.lower(),
            'class_name': f"{model_name}API",
            'function_name': f"create_{model_name.lower()}",
            'module_path': f"{output_dir.replace('/', '.')}.api"
        }
        
        test_file = self.generate_from_template(
            'test_module',
            f"{output_dir}/test_{model_name.lower()}.py",
            test_variables
        )
        generated_files.append(test_file)
        
        return generated_files
    
    def generate_from_existing_code(self, source_file: str, output_file: str, transformations: Dict[str, Any]) -> GeneratedFile:
        """Generate code by transforming existing code"""
        with open(source_file, 'r') as f:
            source_code = f.read()
        
        # Parse source code
        tree = ast.parse(source_code)
        
        # Apply transformations
        if 'rename_class' in transformations:
            for old_name, new_name in transformations['rename_class'].items():
                source_code = source_code.replace(f"class {old_name}", f"class {new_name}")
        
        if 'add_imports' in transformations:
            imports = '\n'.join(transformations['add_imports'])
            source_code = imports + '\n\n' + source_code
        
        if 'add_methods' in transformations:
            # Insert methods before last class closing
            for class_name, methods in transformations['add_methods'].items():
                method_code = '\n'.join(methods)
                # Simple insertion logic (could be more sophisticated)
                source_code = source_code.replace(
                    f"class {class_name}",
                    f"class {class_name}"
                ) + '\n' + method_code
        
        # Write transformed code
        Path(output_file).parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, 'w') as f:
            f.write(source_code)
        
        generated_file = GeneratedFile(
            path=output_file,
            content=source_code,
            template_name="code_transformation",
            variables=transformations,
            created_at=datetime.now()
        )
        
        self._generated_files.append(generated_file)
        return generated_file
    
    def get_generated_files(self) -> List[GeneratedFile]:
        """Get list of generated files"""
        return self._generated_files
    
    def register_custom_template(self, name: str, content: str, variables: Optional[Dict[str, Any]] = None):
        """Register a custom template"""
        self._template_engine.register_template(name, content, variables)


class ScaffoldGenerator:
    """Generates project scaffolds and boilerplate"""
    
    def __init__(self):
        self._code_generator = CodeGenerator()
        self._templates = self._load_scaffold_templates()
    
    def generate_project_scaffold(
        self, 
        project_name: str, 
        project_type: str,
        output_dir: str,
        options: Optional[Dict[str, Any]] = None
    ) -> List[GeneratedFile]:
        """Generate complete project scaffold"""
        options = options or {}
        generated_files = []
        
        if project_type == "fastapi":
            generated_files.extend(self._generate_fastapi_project(project_name, output_dir, options))
        elif project_type == "cli":
            generated_files.extend(self._generate_cli_project(project_name, output_dir, options))
        elif project_type == "library":
            generated_files.extend(self._generate_library_project(project_name, output_dir, options))
        else:
            raise ValueError(f"Unknown project type: {project_type}")
        
        return generated_files
    
    def _generate_fastapi_project(self, name: str, output_dir: str, options: Dict[str, Any]) -> List[GeneratedFile]:
        """Generate FastAPI project scaffold"""
        files = []
        base_dir = Path(output_dir) / name
        
        # Main application file
        main_vars = {
            'project_name': name,
            'description': options.get('description', f'{name} FastAPI application'),
            'version': options.get('version', '0.1.0'),
            'port': options.get('port', 8000)
        }
        
        main_content = f'''"""
{name} FastAPI Application

Generated on {datetime.now().isoformat()}
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="{name}",
    description="{main_vars['description']}",
    version="{main_vars['version']}"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """Root endpoint"""
    return {{"message": "Welcome to {name}", "version": "{main_vars['version']}"}}

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {{"status": "healthy", "service": "{name}"}}

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port={main_vars['port']},
        reload=True
    )
'''
        
        files.append(GeneratedFile(
            path=str(base_dir / "main.py"),
            content=main_content,
            template_name="fastapi_main",
            variables=main_vars,
            created_at=datetime.now()
        ))
        
        # Requirements file
        requirements = '''fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic==2.5.0
python-multipart==0.0.6
'''
        
        files.append(GeneratedFile(
            path=str(base_dir / "requirements.txt"),
            content=requirements,
            template_name="requirements",
            variables={},
            created_at=datetime.now()
        ))
        
        # Dockerfile
        docker_vars = {
            'project_name': name,
            'python_version': '3.11',
            'app_user': 'appuser',
            'port': main_vars['port'],
            'main_file': 'main.py'
        }
        
        docker_file = self._code_generator.generate_from_template(
            'docker_file',
            str(base_dir / "Dockerfile"),
            docker_vars
        )
        files.append(docker_file)
        
        # GitHub workflow
        workflow_vars = {
            'workflow_name': f'{name} CI/CD',
            'main_branch': 'main',
            'python_versions': '3.9, 3.10, 3.11',
            'package_name': name.replace('-', '_')
        }
        
        workflow_file = self._code_generator.generate_from_template(
            'github_workflow',
            str(base_dir / ".github/workflows/ci.yml"),
            workflow_vars
        )
        files.append(workflow_file)
        
        # Write all files
        for file in files:
            Path(file.path).parent.mkdir(parents=True, exist_ok=True)
            with open(file.path, 'w') as f:
                f.write(file.content)
        
        return files
    
    def _generate_cli_project(self, name: str, output_dir: str, options: Dict[str, Any]) -> List[GeneratedFile]:
        """Generate CLI project scaffold"""
        # Implementation for CLI project generation
        return []
    
    def _generate_library_project(self, name: str, output_dir: str, options: Dict[str, Any]) -> List[GeneratedFile]:
        """Generate library project scaffold"""
        # Implementation for library project generation
        return []
    
    def _load_scaffold_templates(self) -> Dict[str, ScaffoldTemplate]:
        """Load scaffold templates"""
        return {
            'fastapi': ScaffoldTemplate(
                name='fastapi',
                description='FastAPI web application',
                files=[],
                variables=['project_name', 'description', 'version'],
                dependencies=['fastapi', 'uvicorn']
            )
        }


# Global instances
_code_generator = CodeGenerator()
_scaffold_generator = ScaffoldGenerator()

# Convenience functions
def generate_from_template(template_name: str, output_path: str, variables: Dict[str, Any]) -> GeneratedFile:
    """Generate code from template"""
    return _code_generator.generate_from_template(template_name, output_path, variables)

def generate_project_scaffold(project_name: str, project_type: str, output_dir: str, options: Optional[Dict[str, Any]] = None) -> List[GeneratedFile]:
    """Generate project scaffold"""
    return _scaffold_generator.generate_project_scaffold(project_name, project_type, output_dir, options)

def register_template(name: str, content: str, variables: Optional[Dict[str, Any]] = None):
    """Register custom template"""
    _code_generator.register_custom_template(name, content, variables)

def generate_crud_api(model_name: str, fields: Dict[str, str], output_dir: str) -> List[GeneratedFile]:
    """Generate CRUD API"""
    return _code_generator.generate_crud_api(model_name, fields, output_dir)