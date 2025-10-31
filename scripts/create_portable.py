#!/usr/bin/env python3
"""
Create Portable Archive

Creates a self-contained portable archive of the Ignition Automation Toolkit
that can be extracted and run anywhere without installation.

Usage:
    python scripts/create_portable.py [--format tar|zip|both]

Output:
    - ignition-toolkit-portable-v{version}.tar.gz (Linux/macOS)
    - ignition-toolkit-portable-v{version}.zip (Windows)
"""

import argparse
import os
import shutil
import subprocess
import sys
import tarfile
import zipfile
from datetime import datetime
from pathlib import Path


def get_version() -> str:
    """Get version from pyproject.toml or environment"""
    version = os.getenv("APP_VERSION", "4.0.0-dev")

    # Try to read from pyproject.toml using simple regex
    pyproject = Path(__file__).parent.parent / "pyproject.toml"
    if pyproject.exists():
        import re
        content = pyproject.read_text()
        match = re.search(r'^version\s*=\s*"([^"]+)"', content, re.MULTILINE)
        if match:
            version = match.group(1)

    return version


def get_project_root() -> Path:
    """Get project root directory"""
    return Path(__file__).parent.parent.resolve()


def create_launcher_scripts(output_dir: Path):
    """Create launcher scripts for Linux and Windows"""

    # Linux/macOS launcher
    linux_launcher = output_dir / "run.sh"
    linux_launcher.write_text("""#!/bin/bash
# Ignition Automation Toolkit - Portable Launcher (Linux/macOS)

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${SCRIPT_DIR}"

echo "========================================"
echo "Ignition Automation Toolkit"
echo "========================================"
echo ""

# Check if venv exists
if [ ! -d "venv" ]; then
    echo "🔧 First run detected - setting up virtual environment..."
    echo ""

    # Check Python version
    if ! command -v python3 &> /dev/null; then
        echo "❌ ERROR: python3 not found. Please install Python 3.10 or later."
        exit 1
    fi

    PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
    echo "✓ Found Python ${PYTHON_VERSION}"

    # Create venv
    echo "✓ Creating virtual environment..."
    python3 -m venv venv

    # Activate venv
    source venv/bin/activate

    # Upgrade pip
    echo "✓ Upgrading pip..."
    pip install --upgrade pip > /dev/null 2>&1

    # Install dependencies
    echo "✓ Installing dependencies..."
    pip install -e . > /dev/null 2>&1

    # Install Playwright browsers
    echo "✓ Installing Playwright browsers..."
    export PLAYWRIGHT_BROWSERS_PATH="${SCRIPT_DIR}/data/.playwright-browsers"
    playwright install chromium > /dev/null 2>&1

    echo ""
    echo "✅ Setup complete!"
    echo ""
fi

# Activate venv
source venv/bin/activate

# Set Playwright browser path
export PLAYWRIGHT_BROWSERS_PATH="${SCRIPT_DIR}/data/.playwright-browsers"

# Read port from .env or default
if [ -f ".env" ]; then
    PORT=$(grep "^API_PORT=" .env | cut -d'=' -f2)
    PORT=${PORT:-5000}
else
    PORT=5000
fi

echo "🚀 Starting Ignition Automation Toolkit..."
echo ""
echo "📍 Access the web interface at: http://localhost:${PORT}"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Start server
exec ./venv/bin/uvicorn ignition_toolkit.api.app:app --host 0.0.0.0 --port ${PORT}
""")
    linux_launcher.chmod(0o755)

    # Windows launcher
    windows_launcher = output_dir / "run.bat"
    windows_launcher.write_text("""@echo off
REM Ignition Automation Toolkit - Portable Launcher (Windows)

setlocal enabledelayedexpansion

cd /d "%~dp0"

echo ========================================
echo Ignition Automation Toolkit
echo ========================================
echo.

REM Check if venv exists
if not exist "venv" (
    echo Setting up virtual environment...
    echo.

    REM Check Python
    python --version >nul 2>&1
    if errorlevel 1 (
        echo ERROR: Python not found. Please install Python 3.10 or later.
        pause
        exit /b 1
    )

    echo Creating virtual environment...
    python -m venv venv

    REM Activate venv
    call venv\\Scripts\\activate.bat

    echo Upgrading pip...
    python -m pip install --upgrade pip >nul 2>&1

    echo Installing dependencies...
    pip install -e . >nul 2>&1

    echo Installing Playwright browsers...
    set PLAYWRIGHT_BROWSERS_PATH=%CD%\\data\\.playwright-browsers
    playwright install chromium >nul 2>&1

    echo.
    echo Setup complete!
    echo.
) else (
    REM Activate venv
    call venv\\Scripts\\activate.bat
)

REM Set Playwright browser path
set PLAYWRIGHT_BROWSERS_PATH=%CD%\\data\\.playwright-browsers

REM Read port from .env or default
set PORT=5000
if exist .env (
    for /f "tokens=1,2 delims==" %%a in (.env) do (
        if "%%a"=="API_PORT" set PORT=%%b
    )
)

echo Starting Ignition Automation Toolkit...
echo.
echo Access the web interface at: http://localhost:%PORT%
echo.
echo Press Ctrl+C to stop the server
echo.

REM Start server
venv\\Scripts\\uvicorn.exe ignition_toolkit.api.app:app --host 0.0.0.0 --port %PORT%
""")

    print(f"  ✓ Created launcher scripts")


def create_install_instructions(output_dir: Path, version: str, runtime_included: bool = False):
    """Create INSTALL.txt with setup instructions"""

    instructions = output_dir / "INSTALL.txt"

    # Different instructions for bundled runtime vs source archives
    if runtime_included:
        quick_start = """QUICK START (BUNDLED RUNTIME - NO SETUP REQUIRED)
--------------------------------------------------

1. Extract this archive to your desired location
2. Run the launcher script:
   - Linux/macOS: ./run.sh
   - Windows:     run.bat

That's it! Everything is included:
✓ Python virtual environment
✓ All dependencies installed
✓ Playwright browser (Chromium)

The server will start immediately - no installation needed."""
        requirements = """REQUIREMENTS
------------

- None! All dependencies are bundled.
- 850MB free disk space (for this archive)
- Network access to your Ignition Gateway"""
    else:
        quick_start = """QUICK START
-----------

1. Extract this archive to your desired location
2. Run the launcher script:
   - Linux/macOS: ./run.sh
   - Windows:     run.bat

The first run will:
- Create a Python virtual environment
- Install all dependencies
- Download Playwright browser (Chromium)
- Start the web server

After first run, simply run the launcher again to start the server."""
        requirements = """REQUIREMENTS
------------

- Python 3.10 or later
- 2GB free disk space (for Playwright browser)
- Network access to your Ignition Gateway"""

    instructions.write_text(f"""
================================================================================
Ignition Automation Toolkit v{version} - Installation Guide
{"[FULL RUNTIME BUNDLE]" if runtime_included else "[SOURCE DISTRIBUTION]"}
================================================================================

{quick_start}

ACCESS THE APPLICATION
----------------------

Open your browser to: http://localhost:5000

The web interface provides:
- Playbook library browser
- Real-time execution monitoring
- Credential management
- AI-assisted playbook creation (if API key configured)

{requirements}

CONFIGURATION
-------------

Edit the .env file to configure:
- API_PORT: Web server port (default: 5000)
- ANTHROPIC_API_KEY: For AI features (optional)
- IGNITION_GATEWAY_URL: Default Gateway URL

DIRECTORY STRUCTURE
-------------------

ignition-toolkit-portable/
├── run.sh                     # Linux/macOS launcher
├── run.bat                    # Windows launcher
├── INSTALL.txt                # This file
├── README.md                  # Project documentation
├── .env.example               # Configuration template
├── ignition_toolkit/          # Main Python package
├── playbooks/                 # YAML playbook library
│   ├── gateway/               # Gateway-only playbooks
│   ├── perspective/           # Perspective-only playbooks
│   └── examples/              # Example playbooks
├── frontend/                  # React web interface
│   └── dist/                  # Built frontend (served by API)
├── tests/                     # Test suite
└── docs/                      # Documentation

FIRST PLAYBOOK
--------------

1. Navigate to http://localhost:5000
2. Browse playbooks in gateway/ or perspective/ folders
3. Click "Run" on any example playbook
4. Watch real-time execution in the UI

To create your own playbooks:
1. Duplicate an existing playbook (use Duplicate button)
2. Edit the YAML file in playbooks/ directory
3. Reload the web interface to see your changes

See docs/playbook_syntax.md for YAML syntax reference.

CREDENTIALS
-----------

Never put passwords in playbook YAML files!

Instead:
1. Add credentials via web interface (Credentials page)
2. Reference them in playbooks using: {{{{ credential.gateway_admin }}}}
3. Credentials are encrypted at rest in ~/.ignition-toolkit/

SECURITY NOTES
--------------

- Server binds to 0.0.0.0 by default (accessible on network)
- To restrict to localhost only, set API_HOST=127.0.0.1 in .env
- CORS is restricted to localhost origins by default
- See docs/SECURITY.md for hardening recommendations

TROUBLESHOOTING
---------------

"Python not found":
  - Install Python 3.10+ from https://www.python.org

"Port 5000 already in use":
  - Change API_PORT in .env file
  - Or stop the process using port 5000

"Playwright browser download fails":
  - Check your internet connection
  - Manually run: venv/bin/playwright install chromium (Linux)
  - Or: venv\\Scripts\\playwright.exe install chromium (Windows)

"Can't connect to Gateway":
  - Verify Gateway is running and accessible
  - Check Gateway URL in playbook or .env
  - Ensure Gateway REST API is enabled

SUPPORT
-------

Documentation: See docs/ directory
Issues: https://github.com/yourusername/ignition-toolkit/issues
Playbook Syntax: docs/playbook_syntax.md
Getting Started: docs/getting_started.md

================================================================================
""")

    print(f"  ✓ Created INSTALL.txt")


def copy_project_files(output_dir: Path, project_root: Path):
    """Copy necessary project files to output directory"""

    # Files and directories to include
    include_patterns = [
        "ignition_toolkit/",
        "playbooks/",
        "frontend/dist/",
        "frontend/package.json",
        "docs/",
        "tests/",
        "pyproject.toml",
        "README.md",
        "CHANGELOG.md",
        "LICENSE",
        ".env.example",
    ]

    # Directories to exclude (won't be copied even if matched)
    exclude_dirs = {
        "__pycache__",
        ".pytest_cache",
        "node_modules",
        ".git",
        "venv",
        ".venv",
        "data",  # Will be created by user
        ".ignition-toolkit",
    }

    # File patterns to exclude
    exclude_files = {
        "*.pyc",
        "*.pyo",
        "*.db",
        ".DS_Store",
        "*.log",
    }

    print("  📦 Copying project files...")

    for pattern in include_patterns:
        source = project_root / pattern

        if source.is_file():
            dest = output_dir / pattern
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, dest)
            print(f"    ✓ {pattern}")

        elif source.is_dir():
            dest = output_dir / pattern

            def ignore_patterns(dir, files):
                ignored = []
                for file in files:
                    # Exclude specific directories
                    if file in exclude_dirs:
                        ignored.append(file)
                        continue

                    # Exclude file patterns
                    for exclude_pattern in exclude_files:
                        import fnmatch
                        if fnmatch.fnmatch(file, exclude_pattern):
                            ignored.append(file)
                            break

                return ignored

            shutil.copytree(source, dest, ignore=ignore_patterns, dirs_exist_ok=True)
            print(f"    ✓ {pattern}")

        else:
            print(f"    ⚠️  Skipping {pattern} (not found)")

    # Create .env from .env.example if it doesn't exist
    if not (output_dir / ".env").exists() and (output_dir / ".env.example").exists():
        shutil.copy2(output_dir / ".env.example", output_dir / ".env")
        print(f"    ✓ Created .env from .env.example")


def create_tarball(source_dir: Path, output_file: Path):
    """Create .tar.gz archive"""

    print(f"  📦 Creating {output_file.name}...")

    with tarfile.open(output_file, "w:gz") as tar:
        tar.add(source_dir, arcname=source_dir.name)

    size_mb = output_file.stat().st_size / (1024 * 1024)
    print(f"    ✓ Created {output_file.name} ({size_mb:.1f} MB)")


def create_zipfile(source_dir: Path, output_file: Path):
    """Create .zip archive"""

    print(f"  📦 Creating {output_file.name}...")

    with zipfile.ZipFile(output_file, "w", zipfile.ZIP_DEFLATED) as zf:
        for file in source_dir.rglob("*"):
            if file.is_file():
                arcname = file.relative_to(source_dir.parent)
                zf.write(file, arcname)

    size_mb = output_file.stat().st_size / (1024 * 1024)
    print(f"    ✓ Created {output_file.name} ({size_mb:.1f} MB)")


def get_platform_suffix() -> str:
    """Get platform suffix for archive name"""
    import platform

    system = platform.system().lower()
    machine = platform.machine().lower()

    # Normalize architecture names
    if machine in ["x86_64", "amd64"]:
        arch = "x64"
    elif machine in ["aarch64", "arm64"]:
        arch = "arm64"
    else:
        arch = machine

    # Normalize system names
    if system == "linux":
        return f"linux-{arch}"
    elif system == "darwin":
        return f"macos-{arch}"
    elif system == "windows":
        return f"windows-{arch}"
    else:
        return f"{system}-{arch}"


def copy_runtime(build_dir: Path, project_root: Path):
    """Copy runtime dependencies (venv, browsers) for fully portable archive"""

    print("  📦 Copying runtime dependencies (this may take a while)...")

    # Copy venv
    venv_source = project_root / "venv"
    if venv_source.exists():
        venv_dest = build_dir / "venv"
        print(f"    → Copying Python venv... ", end="", flush=True)
        shutil.copytree(venv_source, venv_dest, symlinks=True)
        venv_size = sum(f.stat().st_size for f in venv_dest.rglob("*") if f.is_file()) / (1024 * 1024)
        print(f"✓ ({venv_size:.0f} MB)")
    else:
        print(f"    ⚠️  venv not found - archive will not be fully portable!")

    # Copy Playwright browsers
    browsers_source = project_root / "data" / ".playwright-browsers"
    if browsers_source.exists():
        browsers_dest = build_dir / "data" / ".playwright-browsers"
        browsers_dest.parent.mkdir(parents=True, exist_ok=True)
        print(f"    → Copying Playwright browsers... ", end="", flush=True)
        shutil.copytree(browsers_source, browsers_dest)
        browsers_size = sum(f.stat().st_size for f in browsers_dest.rglob("*") if f.is_file()) / (1024 * 1024)
        print(f"✓ ({browsers_size:.0f} MB)")
    else:
        print(f"    ⚠️  Playwright browsers not found - will be downloaded on first run")


def main():
    parser = argparse.ArgumentParser(
        description="Create portable archive of Ignition Automation Toolkit"
    )
    parser.add_argument(
        "--format",
        choices=["tar", "zip", "both"],
        default="both",
        help="Archive format to create (default: both)"
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Output directory for archives (default: project_root/dist)"
    )
    parser.add_argument(
        "--include-runtime",
        action="store_true",
        help="Include venv and browsers for fully portable archive (large, ~850MB)"
    )

    args = parser.parse_args()

    project_root = get_project_root()
    version = get_version()

    # Default output directory
    if args.output_dir is None:
        output_base = project_root / "dist"
    else:
        output_base = args.output_dir

    output_base.mkdir(parents=True, exist_ok=True)

    # Determine archive name suffix
    if args.include_runtime:
        platform_suffix = get_platform_suffix()
        archive_suffix = f"{platform_suffix}-full"
        build_dir_name = f"ignition-toolkit-v{version}-{platform_suffix}-full"
        archive_type = "FULL RUNTIME"
    else:
        archive_suffix = "portable"
        build_dir_name = f"ignition-toolkit-portable-v{version}"
        archive_type = "SOURCE"

    # Create temporary build directory
    build_dir = output_base / build_dir_name

    print("=" * 70)
    print(f"Creating Portable Archive - v{version}")
    print(f"Type: {archive_type}")
    if args.include_runtime:
        print(f"Platform: {get_platform_suffix()}")
        print("⚠️  Runtime included - archive will be large (~850MB)")
    print("=" * 70)
    print()

    # Clean up old build directory
    if build_dir.exists():
        print(f"🧹 Cleaning up old build directory...")
        shutil.rmtree(build_dir)

    build_dir.mkdir(parents=True)
    print(f"✓ Created build directory: {build_dir.relative_to(project_root)}")
    print()

    # Step 1: Copy project files
    print("Step 1: Copying project files")
    copy_project_files(build_dir, project_root)
    print()

    # Step 2: Copy runtime dependencies (if requested)
    if args.include_runtime:
        print("Step 2: Copying runtime dependencies")
        copy_runtime(build_dir, project_root)
        print()
        step_offset = 1
    else:
        step_offset = 0

    # Step 3 (or 2): Create launcher scripts
    print(f"Step {2 + step_offset}: Creating launcher scripts")
    create_launcher_scripts(build_dir)
    print()

    # Step 4 (or 3): Create installation instructions
    print(f"Step {3 + step_offset}: Creating installation instructions")
    create_install_instructions(build_dir, version, runtime_included=args.include_runtime)
    print()

    # Step 5 (or 4): Create archives
    print(f"Step {4 + step_offset}: Creating archives")

    if args.format in ["tar", "both"]:
        tarball = output_base / f"ignition-toolkit-v{version}-{archive_suffix}.tar.gz"
        create_tarball(build_dir, tarball)

    if args.format in ["zip", "both"]:
        zipball = output_base / f"ignition-toolkit-v{version}-{archive_suffix}.zip"
        create_zipfile(build_dir, zipball)

    print()

    # Summary
    print("=" * 70)
    print("✅ Portable Archive Created Successfully!")
    print("=" * 70)
    print()
    print(f"📦 Build directory: {build_dir}")
    print()

    if args.format in ["tar", "both"]:
        print(f"📦 Linux/macOS: {tarball}")

    if args.format in ["zip", "both"]:
        print(f"📦 Windows:     {zipball}")

    print()
    print("To test the portable archive:")
    print(f"  1. Extract to a temporary location")
    print(f"  2. Run the launcher: ./run.sh (Linux/macOS) or run.bat (Windows)")
    print(f"  3. Access web interface at http://localhost:5000")
    print()
    print("To distribute:")
    print(f"  - Share the archive file(s)")
    print(f"  - Recipients extract and run the launcher")
    print(f"  - No installation or configuration needed!")
    print()


if __name__ == "__main__":
    main()
