#!/bin/bash
# Local CI/CD Pipeline Test Script
# Mimics GitHub Actions / GitLab CI without requiring remote runners
#
# Usage: ./ci_test_local.sh [stage]
#   Stages: setup, lint, test, build, security, integration, all
#   Default: all

set -e  # Exit on error
set -u  # Exit on undefined variable

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Project paths
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_ROOT"

# Log file
LOG_FILE="ci_test_local.log"
echo "=== Local CI/CD Test Started: $(date) ===" > "$LOG_FILE"

# Helper functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1" | tee -a "$LOG_FILE"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1" | tee -a "$LOG_FILE"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1" | tee -a "$LOG_FILE"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1" | tee -a "$LOG_FILE"
}

run_stage() {
    local stage_name=$1
    local stage_cmd=$2

    echo ""
    log_info "========================================"
    log_info "Running stage: $stage_name"
    log_info "========================================"

    if eval "$stage_cmd"; then
        log_success "$stage_name completed successfully"
        return 0
    else
        log_error "$stage_name failed"
        return 1
    fi
}

# ============================================================================
# Python Backend Stages
# ============================================================================

stage_python_setup() {
    log_info "Setting up Python environment..."

    # Check if virtual environment exists
    if [ ! -d "venv" ]; then
        log_warning "Virtual environment not found, creating..."
        python3 -m venv venv
    fi

    source venv/bin/activate
    pip install --upgrade pip >> "$LOG_FILE" 2>&1
    pip install -e . >> "$LOG_FILE" 2>&1
    pip install black ruff mypy pytest pytest-asyncio pytest-cov pip-audit bandit radon >> "$LOG_FILE" 2>&1
    log_success "Python environment ready"
}

stage_python_lint() {
    log_info "Running Python linting..."
    source venv/bin/activate

    # Black formatting check
    log_info "  → Checking code formatting with Black..."
    black --check ignition_toolkit/ tests/ 2>&1 | tee -a "$LOG_FILE" || {
        log_warning "Black formatting issues found (run 'black ignition_toolkit/ tests/' to fix)"
        return 1
    }

    # Ruff linting
    log_info "  → Running Ruff linter..."
    ruff check ignition_toolkit/ tests/ 2>&1 | tee -a "$LOG_FILE" || {
        log_warning "Ruff linting issues found"
        return 1
    }

    log_success "Python linting passed"
}

stage_python_typecheck() {
    log_info "Running Python type checking..."
    source venv/bin/activate

    log_info "  → Running MyPy type checker..."
    mypy ignition_toolkit/ --ignore-missing-imports 2>&1 | tee -a "$LOG_FILE" || {
        log_warning "MyPy type checking found issues (non-blocking)"
    }
}

stage_python_complexity() {
    log_info "Analyzing Python code complexity..."
    source venv/bin/activate

    log_info "  → Running Radon complexity analysis..."
    radon cc ignition_toolkit/ -a -nc 2>&1 | tee -a "$LOG_FILE" || true
}

stage_python_test() {
    log_info "Running Python tests..."
    source venv/bin/activate

    pytest tests/ -v --tb=short -x --cov=ignition_toolkit --cov-report=term --cov-report=html 2>&1 | tee -a "$LOG_FILE"
    log_success "Python tests passed"
}

stage_python_security() {
    log_info "Running Python security scans..."
    source venv/bin/activate

    # Bandit security scanner
    log_info "  → Running Bandit security scanner..."
    bandit -r ignition_toolkit/ -ll 2>&1 | tee -a "$LOG_FILE" || {
        log_warning "Bandit found potential security issues (non-blocking)"
    }

    # Dependency audit
    log_info "  → Auditing Python dependencies..."
    pip-audit 2>&1 | tee -a "$LOG_FILE" || {
        log_warning "Dependency vulnerabilities found (non-blocking)"
    }
}

# ============================================================================
# Frontend Stages
# ============================================================================

stage_frontend_setup() {
    log_info "Setting up Frontend environment..."
    cd frontend

    if [ ! -d "node_modules" ]; then
        log_info "Installing npm dependencies..."
        npm ci >> "../$LOG_FILE" 2>&1
    else
        log_info "npm dependencies already installed"
    fi

    cd ..
    log_success "Frontend environment ready"
}

stage_frontend_lint() {
    log_info "Running Frontend linting..."
    cd frontend

    # ESLint
    log_info "  → Running ESLint..."
    npm run lint 2>&1 | tee -a "../$LOG_FILE"

    # TypeScript type check
    log_info "  → Running TypeScript compiler..."
    npx tsc -b 2>&1 | tee -a "../$LOG_FILE"

    cd ..
    log_success "Frontend linting passed"
}

stage_frontend_build() {
    log_info "Building Frontend..."
    cd frontend

    npm run build 2>&1 | tee -a "../$LOG_FILE"

    cd ..
    log_success "Frontend build successful"
}

stage_frontend_security() {
    log_info "Running Frontend security audit..."
    cd frontend

    npm audit --audit-level=high 2>&1 | tee -a "../$LOG_FILE" || {
        log_warning "npm audit found vulnerabilities (non-blocking)"
    }

    cd ..
}

# ============================================================================
# Docker Stage
# ============================================================================

stage_docker_build() {
    log_info "Building Docker image..."

    if ! command -v docker &> /dev/null; then
        log_warning "Docker not installed, skipping Docker build"
        return 0
    fi

    docker build -t ignition-toolkit:test . 2>&1 | tee -a "$LOG_FILE"
    log_success "Docker image built successfully"
}

stage_docker_security() {
    log_info "Scanning Docker image for vulnerabilities..."

    if ! command -v trivy &> /dev/null; then
        log_warning "Trivy not installed, skipping Docker security scan"
        log_info "Install with: curl -sfL https://raw.githubusercontent.com/aquasecurity/trivy/main/contrib/install.sh | sh -s -- -b /usr/local/bin"
        return 0
    fi

    trivy image --severity HIGH,CRITICAL ignition-toolkit:test 2>&1 | tee -a "$LOG_FILE" || {
        log_warning "Docker vulnerabilities found (non-blocking)"
    }
}

# ============================================================================
# Integration Tests
# ============================================================================

stage_integration_test() {
    log_info "Running integration tests..."
    source venv/bin/activate

    pytest tests/test_integration.py -v -m integration 2>&1 | tee -a "$LOG_FILE" || {
        log_warning "No integration tests found or tests failed (non-blocking)"
    }
}

# ============================================================================
# Main Execution
# ============================================================================

run_all_stages() {
    local failed=0

    # Setup
    run_stage "Python Setup" "stage_python_setup" || ((failed++))
    run_stage "Frontend Setup" "stage_frontend_setup" || ((failed++))

    # Lint
    run_stage "Python Lint" "stage_python_lint" || ((failed++))
    run_stage "Python Type Check" "stage_python_typecheck" || true  # Non-blocking
    run_stage "Python Complexity" "stage_python_complexity" || true  # Non-blocking
    run_stage "Frontend Lint" "stage_frontend_lint" || ((failed++))

    # Test
    run_stage "Python Tests" "stage_python_test" || ((failed++))

    # Build
    run_stage "Frontend Build" "stage_frontend_build" || ((failed++))
    run_stage "Docker Build" "stage_docker_build" || true  # Non-blocking if Docker not available

    # Security
    run_stage "Python Security" "stage_python_security" || true  # Non-blocking
    run_stage "Frontend Security" "stage_frontend_security" || true  # Non-blocking
    run_stage "Docker Security" "stage_docker_security" || true  # Non-blocking

    # Integration
    run_stage "Integration Tests" "stage_integration_test" || true  # Non-blocking

    # Summary
    echo ""
    log_info "========================================"
    log_info "CI/CD Pipeline Summary"
    log_info "========================================"

    if [ $failed -eq 0 ]; then
        log_success "All critical stages passed!"
        echo "Full log: $LOG_FILE"
        return 0
    else
        log_error "$failed critical stage(s) failed"
        echo "Full log: $LOG_FILE"
        return 1
    fi
}

# Parse command line arguments
STAGE="${1:-all}"

case $STAGE in
    setup)
        stage_python_setup
        stage_frontend_setup
        ;;
    lint)
        stage_python_lint
        stage_python_typecheck
        stage_frontend_lint
        ;;
    test)
        stage_python_test
        ;;
    build)
        stage_frontend_build
        stage_docker_build
        ;;
    security)
        stage_python_security
        stage_frontend_security
        stage_docker_security
        ;;
    integration)
        stage_integration_test
        ;;
    all)
        run_all_stages
        ;;
    *)
        echo "Usage: $0 [stage]"
        echo "  Stages: setup, lint, test, build, security, integration, all"
        echo "  Default: all"
        exit 1
        ;;
esac
