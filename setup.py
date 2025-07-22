"""Setup configuration for the Zero project."""

# Standard library imports
from pathlib import Path

# Third-party imports
from setuptools import find_packages, setup

# Read the contents of README.md
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding="utf-8")

# Find all packages in the current directory
packages = find_packages(where=".")

setup(
    name="zero",
    version="0.1.0",
    packages=packages,
    package_dir={"": "."},
    # Include all Python files in packages including instruments
    package_data={
        "": ["*.py", "*/*.py", "*/*/*.py", "*/*/*/*.py"],
        "instruments": ["*.py", "*/*.py", "*/*/*.py"],
        "api": ["*.py"],
        "framework": ["*.py", "*/*.py"],
    },
    python_requires=">=3.13",
    install_requires=[
        # Core dependencies
        "pydantic>=1.10.0",
        "fastapi>=0.95.0",
        "uvicorn>=0.22.0",
        "python-multipart>=0.0.6",
        "python-jose[cryptography]>=3.3.0",
        "passlib[bcrypt]>=1.7.4",
        "python-dotenv>=1.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.20.0",
            "pytest-mock>=3.10.0",
            "nest_asyncio>=1.5.6",
            "mypy>=0.910",
            "ruff>=0.3.0",
            "black>=23.0.0",
            "isort>=5.12.0",
        ],
    },
    # Metadata
    author="Zero Team",
    author_email="team@zero.example.com",
    description="Zero - A Python project",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/zero",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.13",
        "Programming Language :: Python :: 3.14",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
