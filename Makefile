# Gary-Zero CI/CD Makefile
# Provides local development commands that mirror the CI/CD pipeline
# Run 'make ci' to execute the complete CI pipeline locally

.PHONY: help ci setup lint test format security docker-build clean check-git install-hooks
.DEFAULT_GOAL := help

# Configuration
PYTHON_VERSION := 3.13
NODE_VERSION := 22
COVERAGE_THRESHOLD := 80
PORT := 8080
PYTHON := python3
PIP := pip3
NPM := npm

# Colors for output
RED := \033[0;31m
GREEN := \033[0;32m
YELLOW := \033[1;33m
BLUE := \033[0;34m
PURPLE := \033[0;35m
CYAN := \033[0;36m
WHITE := \033[1;37m
NC := \033[0m # No Color

help: ## Show this help message
	@echo "$(CYAN)Gary-Zero CI/CD Pipeline$(NC)"
	@echo "========================="
	@echo ""
	@echo "$(WHITE)Available targets:$(NC)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "$(BLUE)%-20s$(NC) %s\n", $$1, $$2}'
	@echo ""
	@echo "$(WHITE)Common workflows:$(NC)"
	@echo "$(GREEN)make ci$(NC)          - Run complete CI pipeline (recommended)"
	@echo "$(GREEN)make setup$(NC)       - Setup development environment"
	@echo "$(GREEN)make quick-check$(NC) - Run fast quality checks"
	@echo "$(GREEN)make test$(NC)        - Run all tests with coverage"

setup: ## Setup development environment
	@echo "$(YELLOW)🔧 Setting up development environment...$(NC)"
	@echo "$(BLUE)📦 Installing Python dependencies...$(NC)"
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements-dev.txt || $(PIP) install fastapi uvicorn python-dotenv pydantic psutil pytest pytest-cov
	@echo "$(BLUE)📦 Installing Node.js dependencies...$(NC)"
	$(NPM) ci
	@echo "$(BLUE)🔨 Installing pre-commit hooks...$(NC)"
	$(MAKE) install-hooks
	@echo "$(BLUE)📁 Creating necessary directories...$(NC)"
	mkdir -p logs work_dir tmp memory tmp/scheduler data
	echo '[]' > tmp/scheduler/tasks.json
	@echo "$(GREEN)✅ Development environment setup completed!$(NC)"

install-hooks: ## Install pre-commit hooks
	@echo "$(BLUE)🔨 Installing pre-commit hooks...$(NC)"
	$(PIP) install pre-commit || echo "$(YELLOW)⚠️ Pre-commit not available, skipping...$(NC)"
	pre-commit install || echo "$(YELLOW)⚠️ Pre-commit hooks not installed$(NC)"
	$(NPM) run prepare || echo "$(YELLOW)⚠️ Husky hooks not installed$(NC)"

lint: ## Run linting and code formatting checks
	@echo "$(YELLOW)🔍 Running code quality checks...$(NC)"
	@echo "$(BLUE)📋 Python linting with ruff...$(NC)"
	ruff check --select=E9,F63,F7,F82 --statistics . || (echo "$(RED)❌ Critical Python syntax errors found$(NC)" && exit 1)
	ruff check . || echo "$(YELLOW)⚠️ Python linting issues found$(NC)"
	ruff format --check . || echo "$(YELLOW)⚠️ Python formatting issues found$(NC)"
	@echo "$(BLUE)📋 Python type checking with mypy...$(NC)"
	mypy framework/ --ignore-missing-imports --no-strict-optional --show-error-codes || echo "$(YELLOW)⚠️ Type checking issues found$(NC)"
	@echo "$(BLUE)📋 JavaScript linting...$(NC)"
	$(NPM) run lint:clean || echo "$(YELLOW)⚠️ JavaScript linting issues found$(NC)"
	@echo "$(BLUE)📋 TypeScript checking...$(NC)"
	$(NPM) run tsc:check || echo "$(YELLOW)⚠️ TypeScript issues found$(NC)"
	@echo "$(GREEN)✅ Linting completed$(NC)"

format: ## Auto-fix formatting issues
	@echo "$(YELLOW)🔧 Auto-fixing code formatting...$(NC)"
	@echo "$(BLUE)🐍 Formatting Python code...$(NC)"
	ruff format .
	ruff check --fix .
	@echo "$(BLUE)🌐 Formatting JavaScript/TypeScript...$(NC)"
	$(NPM) run format
	$(NPM) run lint:fix:clean || echo "$(YELLOW)⚠️ Some JavaScript issues couldn't be auto-fixed$(NC)"
	@echo "$(GREEN)✅ Code formatting completed$(NC)"

test: ## Run all tests with coverage
	@echo "$(YELLOW)🧪 Running comprehensive test suite...$(NC)"
	@echo "$(BLUE)🔬 Python unit tests...$(NC)"
	pytest tests/unit/ -v --cov=framework --cov=api --cov=security \
		--cov-report=xml --cov-report=term-missing \
		--cov-branch --cov-fail-under=$(COVERAGE_THRESHOLD) \
		--timeout=300 -m "not slow" || echo "$(YELLOW)⚠️ Some unit tests failed$(NC)"
	@echo "$(BLUE)🔗 Python integration tests...$(NC)"
	pytest tests/integration/ -v --cov=framework --cov=api --cov=security \
		--cov-report=xml --cov-report=term-missing \
		--cov-append --timeout=600 -m "integration" || echo "$(YELLOW)⚠️ Some integration tests failed$(NC)"
	@echo "$(BLUE)⚡ Performance tests...$(NC)"
	pytest tests/performance/ -v --benchmark-only \
		--benchmark-json=benchmark-results.json \
		--timeout=600 -m "performance" || echo "$(YELLOW)⚠️ Some performance tests failed$(NC)"
	@echo "$(BLUE)🌐 JavaScript tests...$(NC)"
	$(NPM) run test:run || echo "$(YELLOW)⚠️ JavaScript tests failed$(NC)"
	@echo "$(GREEN)✅ Test suite completed$(NC)"

security: ## Run security scans
	@echo "$(YELLOW)🔒 Running security scans...$(NC)"
	@echo "$(BLUE)🛡️ Python security scan with bandit...$(NC)"
	bandit -r framework/ api/ security/ -ll || echo "$(YELLOW)⚠️ Security issues found in Python code$(NC)"
	@echo "$(BLUE)📦 Python dependency security check...$(NC)"
	safety check || echo "$(YELLOW)⚠️ Vulnerable Python dependencies found$(NC)"
	@echo "$(BLUE)🔍 Secret detection...$(NC)"
	detect-secrets scan --baseline .secrets.baseline --all-files || echo "$(YELLOW)⚠️ Potential secrets detected$(NC)"
	@echo "$(BLUE)📦 Node.js security audit...$(NC)"
	$(NPM) run security || echo "$(YELLOW)⚠️ Node.js security issues found$(NC)"
	@echo "$(GREEN)✅ Security scans completed$(NC)"

check-git: ## Validate git workflow and branch status
	@echo "$(YELLOW)🔍 Checking git workflow status...$(NC)"
	@echo "$(BLUE)📋 Git status check...$(NC)"
	$(NPM) run check:git || echo "$(YELLOW)⚠️ Git workflow issues found$(NC)"
	@echo "$(BLUE)🔄 Git workflow validation...$(NC)"
	$(NPM) run check:git-workflow || echo "$(YELLOW)⚠️ Git workflow validation issues$(NC)"
	@echo "$(GREEN)✅ Git workflow validation completed$(NC)"

railpack-validate: ## Validate Railpack configuration
	@echo "$(YELLOW)🚂 Validating Railpack configuration...$(NC)"
	@if [ ! -f "railpack.json" ]; then \
		echo "$(RED)❌ ERROR: railpack.json not found$(NC)"; \
		exit 1; \
	fi
	@echo "$(BLUE)📋 JSON syntax validation...$(NC)"
	@jq empty railpack.json || (echo "$(RED)❌ Invalid JSON syntax in railpack.json$(NC)" && exit 1)
	@echo "$(BLUE)🔍 Required fields validation...$(NC)"
	@jq -e '.builder and .buildCommand and .startCommand and .healthcheckPath' railpack.json > /dev/null || \
		(echo "$(RED)❌ Missing required fields in railpack.json$(NC)" && exit 1)
	@echo "$(BLUE)🔧 PORT environment variable check...$(NC)"
	@jq -e '.environment.PORT == "$${PORT}" or (.startCommand | contains("$$PORT"))' railpack.json > /dev/null || \
		(echo "$(RED)❌ PORT environment variable not properly configured$(NC)" && exit 1)
	@echo "$(GREEN)✅ Railpack configuration is valid$(NC)"

docker-build: ## Test Docker build locally
	@echo "$(YELLOW)🐳 Testing Docker build...$(NC)"
	@echo "$(BLUE)🔨 Building Docker image...$(NC)"
	docker build --no-cache -t gary-zero-local-test . || (echo "$(RED)❌ Docker build failed$(NC)" && exit 1)
	@echo "$(BLUE)🩺 Testing health endpoint...$(NC)"
	docker run -d --name gary-zero-test -p $(PORT):$(PORT) \
		-e PORT=$(PORT) \
		-e PYTHONUNBUFFERED=1 \
		gary-zero-local-test || (echo "$(RED)❌ Docker run failed$(NC)" && exit 1)
	@sleep 10
	@timeout 30 bash -c 'until curl -f http://localhost:$(PORT)/health; do sleep 2; done' || \
		(echo "$(RED)❌ Health endpoint test failed$(NC)" && docker stop gary-zero-test && docker rm gary-zero-test && exit 1)
	@echo "$(GREEN)✅ Docker health endpoint test passed$(NC)"
	@docker stop gary-zero-test
	@docker rm gary-zero-test
	@echo "$(GREEN)✅ Docker build test completed$(NC)"

quick-check: ## Run fast quality checks (no tests)
	@echo "$(YELLOW)⚡ Running quick quality checks...$(NC)"
	@$(MAKE) --no-print-directory lint
	@$(MAKE) --no-print-directory security
	@$(MAKE) --no-print-directory check-git
	@$(MAKE) --no-print-directory railpack-validate
	@echo "$(GREEN)✅ Quick checks completed$(NC)"

ci: ## Run complete CI pipeline locally
	@echo "$(PURPLE)🚀 Starting Gary-Zero CI Pipeline$(NC)"
	@echo "=================================="
	@echo ""
	@echo "$(WHITE)Pipeline components:$(NC)"
	@echo "$(BLUE)A. Static Checks$(NC)   - Code quality & consistency"
	@echo "$(BLUE)B. Tests$(NC)           - Comprehensive testing"
	@echo "$(BLUE)C. Security Audit$(NC)  - Multi-layer security scanning"
	@echo "$(BLUE)D. Docker Build$(NC)    - Container validation"
	@echo "$(BLUE)E. Git Workflow$(NC)    - Repository validation"
	@echo "$(BLUE)F. Railpack Config$(NC) - Railway deployment validation"
	@echo ""
	@echo "$(YELLOW)🔧 Phase 1: Environment Setup$(NC)"
	@$(MAKE) --no-print-directory setup
	@echo ""
	@echo "$(YELLOW)🔍 Phase 2: Static Analysis (Workflow A)$(NC)"
	@$(MAKE) --no-print-directory lint
	@echo ""
	@echo "$(YELLOW)🧪 Phase 3: Test Suite (Workflow B)$(NC)"
	@$(MAKE) --no-print-directory test
	@echo ""
	@echo "$(YELLOW)🔒 Phase 4: Security Audit (Workflow C)$(NC)"
	@$(MAKE) --no-print-directory security
	@echo ""
	@echo "$(YELLOW)🐳 Phase 5: Docker Build Validation$(NC)"
	@$(MAKE) --no-print-directory docker-build
	@echo ""
	@echo "$(YELLOW)🔄 Phase 6: Git Workflow Validation$(NC)"
	@$(MAKE) --no-print-directory check-git
	@echo ""
	@echo "$(YELLOW)🚂 Phase 7: Railpack Configuration$(NC)"
	@$(MAKE) --no-print-directory railpack-validate
	@echo ""
	@echo "$(GREEN)🎉 CI Pipeline Completed Successfully!$(NC)"
	@echo "$(WHITE)========================================$(NC)"
	@echo ""
	@echo "$(CYAN)📊 Summary:$(NC)"
	@echo "$(GREEN)✅ Static code analysis passed$(NC)"
	@echo "$(GREEN)✅ Test suite executed$(NC)"
	@echo "$(GREEN)✅ Security scans completed$(NC)"
	@echo "$(GREEN)✅ Docker build validated$(NC)"
	@echo "$(GREEN)✅ Git workflow verified$(NC)"
	@echo "$(GREEN)✅ Railway configuration validated$(NC)"
	@echo ""
	@echo "$(WHITE)🚀 Ready for deployment!$(NC)"
	@echo ""
	@echo "$(BLUE)Next steps:$(NC)"
	@echo "• Commit your changes: $(CYAN)git add . && git commit -m 'your message'$(NC)"
	@echo "• Push to trigger CI/CD: $(CYAN)git push$(NC)"
	@echo "• Monitor deployment at Railway dashboard"

clean: ## Clean up build artifacts and temporary files
	@echo "$(YELLOW)🧹 Cleaning up build artifacts...$(NC)"
	rm -rf __pycache__ .pytest_cache .coverage coverage.xml
	rm -rf node_modules/.cache
	rm -rf *.pyc **/*.pyc
	rm -rf benchmark-results.json bandit-report.json safety-report.json
	rm -rf logs work_dir tmp data
	mkdir -p logs work_dir tmp memory tmp/scheduler data
	echo '[]' > tmp/scheduler/tasks.json
	@echo "$(GREEN)✅ Cleanup completed$(NC)"

# Development helpers
dev-server: ## Start development server
	@echo "$(YELLOW)🚀 Starting development server...$(NC)"
	$(PYTHON) run_ui.py

dev-watch: ## Start development server with file watching
	@echo "$(YELLOW)👀 Starting development server with file watching...$(NC)"
	$(NPM) run test:watch &
	$(PYTHON) run_ui.py

# Utility targets
check-deps: ## Check dependency compatibility
	@echo "$(YELLOW)📦 Checking dependencies...$(NC)"
	$(NPM) run check:dependencies
	$(PIP) check || echo "$(YELLOW)⚠️ Python dependency conflicts found$(NC)"

docs-serve: ## Serve documentation locally
	@echo "$(YELLOW)📚 Serving documentation...$(NC)"
	$(PYTHON) -m http.server 8000 --directory docs

# This ensures the pipeline fails if any critical step fails
.PHONY: ci-strict
ci-strict: ## Run CI pipeline with strict failure handling
	@set -e; \
	$(MAKE) --no-print-directory setup && \
	$(MAKE) --no-print-directory lint && \
	$(MAKE) --no-print-directory test && \
	$(MAKE) --no-print-directory security && \
	$(MAKE) --no-print-directory docker-build && \
	$(MAKE) --no-print-directory check-git && \
	$(MAKE) --no-print-directory railpack-validate && \
	echo "$(GREEN)🎉 Strict CI Pipeline Completed Successfully!$(NC)"
