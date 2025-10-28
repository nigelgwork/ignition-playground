# ========================================
# Ignition Automation Toolkit - Makefile
# ========================================
# Comprehensive development and deployment commands
#
# Quick Start:
#   make help          # Show all available commands
#   make install       # Set up development environment
#   make dev           # Start development server
#   make test          # Run tests

.PHONY: help
help: ## Show this help message
	@echo "=========================================="
	@echo "Ignition Automation Toolkit - Commands"
	@echo "=========================================="
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'
	@echo ""

# ========================================
# Installation & Setup
# ========================================

.PHONY: install
install: ## Install project in development mode
	@echo "Installing Ignition Toolkit..."
	python -m venv venv || true
	./venv/bin/pip install --upgrade pip
	./venv/bin/pip install -e .
	@echo "✅ Installation complete"

.PHONY: install-dev
install-dev: ## Install with development dependencies
	@echo "Installing development dependencies..."
	./venv/bin/pip install -e ".[dev]"
	./venv/bin/playwright install chromium
	@echo "✅ Development environment ready"

.PHONY: install-playwright
install-playwright: ## Install Playwright browsers
	@echo "Installing Playwright browsers..."
	./venv/bin/playwright install chromium
	@echo "✅ Playwright browsers installed"

.PHONY: init
init: ## Initialize toolkit (create .env, credential vault, database)
	@echo "Initializing Ignition Toolkit..."
	@if [ ! -f .env ]; then cp .env.example .env; echo "✅ Created .env"; fi
	@./venv/bin/ignition-toolkit init || echo "⚠️  Init failed - run 'make install' first"
	@echo "✅ Initialization complete"

.PHONY: requirements
requirements: ## Generate requirements.txt from pyproject.toml
	@echo "Generating requirements.txt..."
	./venv/bin/pip install pip-tools
	./venv/bin/pip-compile pyproject.toml -o requirements.txt --resolver=backtracking
	@echo "✅ requirements.txt generated"

# ========================================
# Development
# ========================================

.PHONY: dev
dev: ## Start development server (backend + frontend hot reload)
	@echo "Starting development environment..."
	@./start_server.sh

.PHONY: dev-backend
dev-backend: ## Start backend only (for frontend testing)
	@echo "Starting backend server..."
	@export PLAYWRIGHT_BROWSERS_PATH=./data/.playwright-browsers && \
	./venv/bin/uvicorn ignition_toolkit.api.app:app --host 0.0.0.0 --port 5000 --reload

.PHONY: dev-frontend
dev-frontend: ## Start frontend dev server only
	@echo "Starting frontend dev server..."
	@cd frontend && npm install && npm run dev

.PHONY: stop
stop: ## Stop all running servers
	@echo "Stopping servers..."
	@./stop_server.sh || pkill -f "uvicorn.*ignition" || echo "No servers running"
	@echo "✅ Servers stopped"

.PHONY: restart
restart: stop dev ## Restart development server

.PHONY: status
status: ## Check server status
	@./check_server.sh

# ========================================
# Testing
# ========================================

.PHONY: test
test: ## Run all tests
	@echo "Running tests..."
	./venv/bin/pytest tests/ -v

.PHONY: test-unit
test-unit: ## Run unit tests only
	@echo "Running unit tests..."
	./venv/bin/pytest tests/ -v -m "not integration"

.PHONY: test-integration
test-integration: ## Run integration tests only
	@echo "Running integration tests..."
	./venv/bin/pytest tests/ -v -m integration

.PHONY: test-watch
test-watch: ## Run tests in watch mode
	@echo "Running tests in watch mode..."
	./venv/bin/pytest-watch tests/

.PHONY: test-cov
test-cov: ## Run tests with coverage report
	@echo "Running tests with coverage..."
	./venv/bin/pytest tests/ --cov=ignition_toolkit --cov-report=html --cov-report=term
	@echo "✅ Coverage report: htmlcov/index.html"

.PHONY: test-fast
test-fast: ## Run fast tests only (skip slow integration tests)
	@echo "Running fast tests..."
	./venv/bin/pytest tests/ -v -k "not slow"

# ========================================
# Code Quality
# ========================================

.PHONY: lint
lint: ## Run all linters (ruff, mypy)
	@echo "Running linters..."
	./venv/bin/ruff check ignition_toolkit/
	./venv/bin/mypy ignition_toolkit/

.PHONY: format
format: ## Format code with black and ruff
	@echo "Formatting code..."
	./venv/bin/black ignition_toolkit/ tests/
	./venv/bin/ruff check ignition_toolkit/ tests/ --fix

.PHONY: format-check
format-check: ## Check code formatting
	@echo "Checking code formatting..."
	./venv/bin/black --check ignition_toolkit/ tests/
	./venv/bin/ruff check ignition_toolkit/ tests/

.PHONY: complexity
complexity: ## Check code complexity with radon
	@echo "Checking code complexity..."
	./venv/bin/radon cc ignition_toolkit/ -a -s

.PHONY: security
security: ## Run security checks with bandit
	@echo "Running security checks..."
	./venv/bin/bandit -r ignition_toolkit/ -ll

# ========================================
# CI/CD Pipeline
# ========================================

.PHONY: ci
ci: ## Run full CI/CD pipeline locally (all stages)
	@echo "Running full CI/CD pipeline..."
	./ci_test_local.sh all

.PHONY: ci-lint
ci-lint: ## Run CI/CD lint stage only
	@echo "Running CI/CD lint stage..."
	./ci_test_local.sh lint

.PHONY: ci-test
ci-test: ## Run CI/CD test stage only
	@echo "Running CI/CD test stage..."
	./ci_test_local.sh test

.PHONY: ci-build
ci-build: ## Run CI/CD build stage only
	@echo "Running CI/CD build stage..."
	./ci_test_local.sh build

.PHONY: ci-security
ci-security: ## Run CI/CD security stage only
	@echo "Running CI/CD security stage..."
	./ci_test_local.sh security

.PHONY: pre-release
pre-release: format ci ## Run before release (format + full CI/CD)
	@echo "✅ Pre-release checks complete!"
	@echo "If all passed, you're ready to:"
	@echo "  1. Run: make bump-patch (or bump-minor/bump-major)"
	@echo "  2. Commit changes"
	@echo "  3. Tag release: git tag v\$$(cat VERSION)"
	@echo "  4. Push: git push && git push --tags"

# ========================================
# Docker
# ========================================

.PHONY: docker-build
docker-build: ## Build Docker image
	@echo "Building Docker image..."
	docker build -t ignition-toolkit:latest .
	@echo "✅ Docker image built"

.PHONY: docker-up
docker-up: ## Start services with docker-compose (production)
	@echo "Starting Docker services (production)..."
	docker-compose up -d
	@echo "✅ Services started"

.PHONY: docker-up-dev
docker-up-dev: ## Start services with docker-compose (dev profile)
	@echo "Starting Docker services (development)..."
	docker-compose --profile dev up -d
	@echo "✅ Services started"

.PHONY: docker-up-postgres
docker-up-postgres: ## Start services with PostgreSQL
	@echo "Starting Docker services (with PostgreSQL)..."
	docker-compose --profile postgres up -d
	@echo "✅ Services started"

.PHONY: docker-down
docker-down: ## Stop Docker services
	@echo "Stopping Docker services..."
	docker-compose down
	@echo "✅ Services stopped"

.PHONY: docker-down-volumes
docker-down-volumes: ## Stop Docker services and remove volumes
	@echo "Stopping Docker services and removing volumes..."
	docker-compose down -v
	@echo "⚠️  All data removed"

.PHONY: docker-logs
docker-logs: ## Show Docker logs
	docker-compose logs -f

.PHONY: docker-shell
docker-shell: ## Open shell in backend container
	docker-compose exec backend bash

.PHONY: docker-rebuild
docker-rebuild: docker-down docker-build docker-up ## Rebuild and restart Docker services

# ========================================
# Database
# ========================================

.PHONY: db-reset
db-reset: ## Reset database (delete and reinitialize)
	@echo "Resetting database..."
	@rm -f data/toolkit.db
	@./venv/bin/python -c "from ignition_toolkit.storage import get_database; get_database()"
	@echo "✅ Database reset"

.PHONY: db-backup
db-backup: ## Backup database
	@echo "Backing up database..."
	@mkdir -p data/backups
	@cp data/toolkit.db data/backups/toolkit_$(shell date +%Y%m%d_%H%M%S).db
	@echo "✅ Database backed up"

.PHONY: db-shell
db-shell: ## Open SQLite shell
	sqlite3 data/toolkit.db

# ========================================
# Credentials
# ========================================

.PHONY: cred-list
cred-list: ## List all credentials
	./venv/bin/ignition-toolkit credential list

.PHONY: cred-add
cred-add: ## Add a new credential (interactive)
	./venv/bin/ignition-toolkit credential add

.PHONY: cred-backup
cred-backup: ## Backup credential vault
	@echo "Backing up credentials..."
	@mkdir -p ~/.ignition-toolkit/backups
	@cp ~/.ignition-toolkit/credentials.enc ~/.ignition-toolkit/backups/credentials_$(shell date +%Y%m%d_%H%M%S).enc
	@echo "✅ Credentials backed up"

# ========================================
# Playbooks
# ========================================

.PHONY: playbook-list
playbook-list: ## List all playbooks
	@echo "Available playbooks:"
	@find playbooks -name "*.yaml" -o -name "*.yml" | sort

.PHONY: playbook-validate
playbook-validate: ## Validate all playbooks
	@echo "Validating playbooks..."
	@for file in $$(find playbooks -name "*.yaml" -o -name "*.yml"); do \
		echo "Checking $$file..."; \
		./venv/bin/python -c "import yaml; yaml.safe_load(open('$$file'))" || exit 1; \
	done
	@echo "✅ All playbooks valid"

# ========================================
# Cleanup
# ========================================

.PHONY: clean
clean: ## Clean build artifacts and cache
	@echo "Cleaning..."
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete
	@find . -type f -name "*.pyo" -delete
	@find . -type f -name "*.coverage" -delete
	@rm -rf .pytest_cache htmlcov .mypy_cache .ruff_cache
	@rm -rf build dist *.egg-info
	@echo "✅ Cleaned"

.PHONY: clean-all
clean-all: clean docker-down-volumes ## Clean everything including Docker volumes
	@echo "Deep cleaning..."
	@rm -rf venv
	@rm -rf data/*.db
	@rm -rf data/screenshots/*
	@rm -rf frontend/node_modules
	@rm -rf frontend/dist
	@echo "⚠️  Everything cleaned - run 'make install' to start fresh"

# ========================================
# Build & Release
# ========================================

.PHONY: build
build: ## Build frontend for production
	@echo "Building frontend..."
	@cd frontend && npm install && npm run build
	@echo "✅ Frontend built"

.PHONY: build-all
build-all: build docker-build ## Build frontend and Docker image

.PHONY: version
version: ## Show current version
	@cat VERSION

.PHONY: bump-patch
bump-patch: ## Bump patch version (x.x.X)
	@./update_version.sh patch

.PHONY: bump-minor
bump-minor: ## Bump minor version (x.X.0)
	@./update_version.sh minor

.PHONY: bump-major
bump-major: ## Bump major version (X.0.0)
	@./update_version.sh major

# ========================================
# Utilities
# ========================================

.PHONY: logs
logs: ## Show application logs
	@tail -f logs/*.log 2>/dev/null || echo "No logs found in logs/"

.PHONY: verify-ux
verify-ux: ## Verify UX functionality
	@./verify_ux.sh

.PHONY: info
info: ## Show environment information
	@echo "=========================================="
	@echo "Environment Information"
	@echo "=========================================="
	@echo "Python version: $$(./venv/bin/python --version 2>&1)"
	@echo "Pip version: $$(./venv/bin/pip --version)"
	@echo "Node version: $$(node --version 2>/dev/null || echo 'Not installed')"
	@echo "npm version: $$(npm --version 2>/dev/null || echo 'Not installed')"
	@echo "Docker version: $$(docker --version 2>/dev/null || echo 'Not installed')"
	@echo "Working directory: $$(pwd)"
	@echo "=========================================="

.PHONY: deps-check
deps-check: ## Check for outdated dependencies
	@echo "Checking for outdated dependencies..."
	./venv/bin/pip list --outdated

.PHONY: deps-upgrade
deps-upgrade: ## Upgrade all dependencies
	@echo "Upgrading dependencies..."
	./venv/bin/pip install --upgrade pip
	./venv/bin/pip-compile --upgrade pyproject.toml -o requirements.txt
	./venv/bin/pip install -r requirements.txt
	@echo "✅ Dependencies upgraded"

# ========================================
# Default target
# ========================================

.DEFAULT_GOAL := help
