#!/usr/bin/env python3
"""
Cross-platform task runner - Replaces Makefile for Windows compatibility

Usage:
    python tasks.py <task> [args]

Available tasks:
    install        - Install project in development mode
    install-dev    - Install with development dependencies
    init           - Initialize toolkit (credential vault, database)
    dev            - Start development server
    stop           - Stop all servers
    status         - Check server status
    test           - Run all tests
    test-cov       - Run tests with coverage
    lint           - Run linters
    format         - Format code
    format-check   - Check code formatting
    build          - Build frontend
    clean          - Clean build artifacts
    help           - Show this help
"""
import sys
import subprocess
import shutil
from pathlib import Path


def run(cmd, **kwargs):
    """Run a command and return exit code"""
    if isinstance(cmd, str):
        print(f"Running: {cmd}")
    else:
        print(f"Running: {' '.join(str(c) for c in cmd)}")
    result = subprocess.run(cmd, **kwargs)
    return result.returncode


def get_venv_bin(executable):
    """Get path to venv executable (cross-platform)"""
    venv_dir = Path("venv")
    if sys.platform == "win32":
        return str(venv_dir / "Scripts" / f"{executable}.exe")
    else:
        return str(venv_dir / "bin" / executable)


def task_install():
    """Install project in development mode"""
    print("=" * 60)
    print("Installing Ignition Toolkit...")
    print("=" * 60)

    # Create venv if needed
    venv_dir = Path("venv")
    if not venv_dir.exists():
        print("\nCreating virtual environment...")
        run([sys.executable, "-m", "venv", "venv"])

    # Upgrade pip
    pip = get_venv_bin("pip")
    print("\nUpgrading pip...")
    run([pip, "install", "--upgrade", "pip"])

    # Install package
    print("\nInstalling package in development mode...")
    run([pip, "install", "-e", "."])

    print("\n✅ Installation complete")
    print("\nNext steps:")
    print("  python tasks.py install-dev  # Install dev dependencies")
    print("  python tasks.py init         # Initialize toolkit")
    return 0


def task_install_dev():
    """Install with development dependencies"""
    print("=" * 60)
    print("Installing development dependencies...")
    print("=" * 60)

    pip = get_venv_bin("pip")
    playwright = get_venv_bin("playwright")

    print("\nInstalling dev dependencies...")
    run([pip, "install", "-e", ".[dev]"])

    print("\nInstalling Playwright browsers...")
    run([playwright, "install", "chromium"])

    print("\n✅ Development environment ready")
    return 0


def task_init():
    """Initialize toolkit"""
    print("=" * 60)
    print("Initializing Ignition Toolkit...")
    print("=" * 60)

    # Create .env if needed
    env_file = Path(".env")
    env_example = Path(".env.example")
    if not env_file.exists() and env_example.exists():
        env_file.write_text(env_example.read_text())
        print("✅ Created .env from .env.example")
    elif not env_file.exists():
        print("⚠️  No .env.example found, skipping .env creation")

    # Run init command
    cli = get_venv_bin("ignition-toolkit")

    print("\nInitializing credential vault and database...")
    result = run([cli, "init"])

    if result == 0:
        print("\n✅ Initialization complete")
        print("\nNext steps:")
        print("  python tasks.py dev  # Start development server")
    else:
        print("\n❌ Initialization failed")
        print("Make sure you ran: python tasks.py install")

    return result


def task_dev():
    """Start development server"""
    print("=" * 60)
    print("Starting development server...")
    print("=" * 60)

    cli = get_venv_bin("ignition-toolkit")

    print("\nStarting server on http://0.0.0.0:5000")
    print("Press CTRL+C to stop\n")

    return run([cli, "server", "start"])


def task_stop():
    """Stop all servers"""
    print("=" * 60)
    print("Stopping servers...")
    print("=" * 60)

    cli = get_venv_bin("ignition-toolkit")
    return run([cli, "server", "stop"])


def task_status():
    """Check server status"""
    cli = get_venv_bin("ignition-toolkit")
    return run([cli, "server", "status"])


def task_test():
    """Run all tests"""
    print("=" * 60)
    print("Running tests...")
    print("=" * 60)

    pytest = get_venv_bin("pytest")
    return run([pytest, "tests/", "-v"])


def task_test_cov():
    """Run tests with coverage"""
    print("=" * 60)
    print("Running tests with coverage...")
    print("=" * 60)

    pytest = get_venv_bin("pytest")
    result = run([
        pytest, "tests/",
        "--cov=ignition_toolkit",
        "--cov-report=html",
        "--cov-report=term"
    ])

    if result == 0:
        print("\n✅ Coverage report generated: htmlcov/index.html")

    return result


def task_lint():
    """Run linters"""
    print("=" * 60)
    print("Running linters...")
    print("=" * 60)

    ruff = get_venv_bin("ruff")
    mypy = get_venv_bin("mypy")

    print("\n[1/2] Running ruff...")
    exit_code = run([ruff, "check", "ignition_toolkit/"])

    print("\n[2/2] Running mypy...")
    exit_code += run([mypy, "ignition_toolkit/"])

    if exit_code == 0:
        print("\n✅ All linters passed")
    else:
        print("\n❌ Linting failed")

    return exit_code


def task_format():
    """Format code"""
    print("=" * 60)
    print("Formatting code...")
    print("=" * 60)

    black = get_venv_bin("black")
    ruff = get_venv_bin("ruff")

    print("\n[1/2] Running black...")
    run([black, "ignition_toolkit/", "tests/"])

    print("\n[2/2] Running ruff --fix...")
    run([ruff, "check", "ignition_toolkit/", "tests/", "--fix"])

    print("\n✅ Code formatted")
    return 0


def task_format_check():
    """Check code formatting"""
    print("=" * 60)
    print("Checking code formatting...")
    print("=" * 60)

    black = get_venv_bin("black")
    ruff = get_venv_bin("ruff")

    print("\n[1/2] Checking black...")
    exit_code = run([black, "--check", "ignition_toolkit/", "tests/"])

    print("\n[2/2] Checking ruff...")
    exit_code += run([ruff, "check", "ignition_toolkit/", "tests/"])

    if exit_code == 0:
        print("\n✅ Code formatting is correct")
    else:
        print("\n❌ Code formatting issues found")
        print("Run: python tasks.py format")

    return exit_code


def task_build():
    """Build frontend"""
    print("=" * 60)
    print("Building frontend...")
    print("=" * 60)

    frontend_dir = Path("frontend")

    if not frontend_dir.exists():
        print("❌ Frontend directory not found")
        return 1

    # Install dependencies
    print("\n[1/2] Installing npm dependencies...")
    result = run(["npm", "install"], cwd=frontend_dir)
    if result != 0:
        print("❌ npm install failed")
        return result

    # Build
    print("\n[2/2] Building frontend...")
    result = run(["npm", "run", "build"], cwd=frontend_dir)

    if result == 0:
        print("\n✅ Frontend built successfully")
        print("Output: frontend/dist/")
    else:
        print("\n❌ Frontend build failed")

    return result


def task_clean():
    """Clean build artifacts"""
    print("=" * 60)
    print("Cleaning build artifacts...")
    print("=" * 60)

    removed_count = 0

    # Clean Python cache
    print("\nCleaning Python cache files...")
    for pattern in ["**/__pycache__", "**/*.pyc", "**/*.pyo"]:
        for path in Path(".").glob(pattern):
            if path.is_dir():
                shutil.rmtree(path)
                removed_count += 1
            else:
                path.unlink()
                removed_count += 1

    # Clean build dirs
    print("Cleaning build directories...")
    for dir_pattern in [".pytest_cache", "htmlcov", ".mypy_cache", ".ruff_cache",
                        "build", "dist", "*.egg-info"]:
        for path in Path(".").glob(dir_pattern):
            if path.is_dir():
                print(f"  Removing: {path}")
                shutil.rmtree(path)
                removed_count += 1

    # Clean frontend build
    frontend_dist = Path("frontend/dist")
    if frontend_dist.exists():
        print(f"  Removing: {frontend_dist}")
        shutil.rmtree(frontend_dist)
        removed_count += 1

    print(f"\n✅ Cleaned {removed_count} items")
    return 0


def task_help():
    """Show help"""
    print(__doc__)
    return 0


# Task registry
TASKS = {
    "install": task_install,
    "install-dev": task_install_dev,
    "init": task_init,
    "dev": task_dev,
    "stop": task_stop,
    "status": task_status,
    "test": task_test,
    "test-cov": task_test_cov,
    "lint": task_lint,
    "format": task_format,
    "format-check": task_format_check,
    "build": task_build,
    "clean": task_clean,
    "help": task_help,
}


def main():
    if len(sys.argv) < 2:
        task_help()
        return 1

    task_name = sys.argv[1]

    if task_name not in TASKS:
        print(f"❌ Unknown task: {task_name}")
        print(f"\nAvailable tasks: {', '.join(sorted(TASKS.keys()))}")
        print(f"\nRun 'python tasks.py help' for more information")
        return 1

    return TASKS[task_name]()


if __name__ == "__main__":
    sys.exit(main())
