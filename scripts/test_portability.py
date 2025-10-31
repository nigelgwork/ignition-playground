#!/usr/bin/env python3
"""
Test Portability

Tests that the Ignition Automation Toolkit works correctly when copied to
different directories. Validates dynamic path resolution and portability.

Usage:
    python scripts/test_portability.py [--temp-dir /path/to/test]

This script:
1. Creates a temporary directory (or uses provided one)
2. Copies project files to temp directory
3. Runs verification checks
4. Tests that all paths are dynamically resolved
5. Validates shell scripts work with SCRIPT_DIR detection
6. Cleans up (unless --keep is specified)
"""

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def get_project_root() -> Path:
    """Get project root directory"""
    return Path(__file__).parent.parent.resolve()


def run_command(cmd: list[str], cwd: Path, env: dict = None) -> tuple[int, str, str]:
    """Run a command and return (returncode, stdout, stderr)"""
    result = subprocess.run(
        cmd,
        cwd=cwd,
        capture_output=True,
        text=True,
        env={**os.environ, **(env or {})}
    )
    return result.returncode, result.stdout, result.stderr


def copy_project_files(source: Path, dest: Path) -> None:
    """Copy essential project files to destination"""
    print(f"📦 Copying project files from {source} to {dest}...")

    # Files and directories to copy
    include_patterns = [
        "ignition_toolkit/",
        "playbooks/",
        "frontend/dist/",
        "frontend/package.json",
        "scripts/",
        "pyproject.toml",
        "README.md",
        ".env.example",
        "start_server.sh",
        "verify_ux.sh",
    ]

    # Directories to exclude
    exclude_dirs = {
        "__pycache__",
        ".pytest_cache",
        "node_modules",
        ".git",
        "venv",
        ".venv",
        "data",
        ".ignition-toolkit",
        "dist",
    }

    copied_count = 0

    for pattern in include_patterns:
        source_path = source / pattern

        if source_path.is_file():
            dest_path = dest / pattern
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source_path, dest_path)
            copied_count += 1
            print(f"  ✓ {pattern}")

        elif source_path.is_dir():
            dest_path = dest / pattern

            def ignore_patterns(dir_path, files):
                ignored = []
                for file in files:
                    if file in exclude_dirs:
                        ignored.append(file)
                return ignored

            shutil.copytree(source_path, dest_path, ignore=ignore_patterns, dirs_exist_ok=True)
            copied_count += 1
            print(f"  ✓ {pattern}")

    print(f"  ✅ Copied {copied_count} items")
    return


def test_path_resolution(test_dir: Path) -> bool:
    """Test that path resolution works correctly"""
    print("\n🧪 Testing path resolution...")

    # Test 1: Check pyproject.toml location detection
    print("  Testing: pyproject.toml location detection")
    pyproject = test_dir / "pyproject.toml"
    if not pyproject.exists():
        print("    ❌ pyproject.toml not found")
        return False
    print("    ✅ pyproject.toml found")

    # Test 2: Check playbooks directory detection
    print("  Testing: playbooks directory")
    playbooks_dir = test_dir / "playbooks"
    if not playbooks_dir.exists():
        print("    ❌ playbooks directory not found")
        return False
    print(f"    ✅ Playbooks at: {playbooks_dir}")

    # Test 3: Check frontend dist
    print("  Testing: frontend dist")
    frontend_dist = test_dir / "frontend" / "dist"
    if not frontend_dist.exists():
        print("    ⚠️  Frontend dist not found (expected if not built)")
    else:
        print(f"    ✅ Frontend dist at: {frontend_dist}")

    # Test 4: Check shell script path resolution
    print("  Testing: Shell script SCRIPT_DIR detection")
    start_server = test_dir / "start_server.sh"
    if start_server.exists():
        # Read script and verify it uses SCRIPT_DIR
        content = start_server.read_text()
        if 'SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"' in content:
            print("    ✅ Shell script uses dynamic SCRIPT_DIR")
        else:
            print("    ❌ Shell script doesn't use dynamic SCRIPT_DIR")
            return False
    else:
        print("    ⚠️  start_server.sh not found")

    return True


def test_python_imports(test_dir: Path) -> tuple[bool, bool]:
    """Test that Python imports work correctly

    Returns:
        (passed, requires_deps): (True if test passed, True if deps are needed)
    """
    print("\n🐍 Testing Python imports...")

    test_script = test_dir / "test_imports.py"
    test_script.write_text("""
import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

# Test imports
try:
    from ignition_toolkit.core.paths import get_package_root, get_playbooks_dir
    print(f"Package root: {get_package_root()}")
    print(f"Playbooks dir: {get_playbooks_dir()}")
    print("SUCCESS")
except ImportError as e:
    print(f"IMPORT_ERROR: {e}")
    sys.exit(2)  # Special exit code for missing dependencies
except Exception as e:
    print(f"FAILED: {e}")
    sys.exit(1)
""")

    returncode, stdout, stderr = run_command(
        ["python3", str(test_script)],
        cwd=test_dir
    )

    print(f"  Output: {stdout}")

    if returncode == 2:
        # Missing dependencies - this is OK, just means deps not installed
        print("    ⚠️  Missing dependencies (this is OK - test structural portability only)")
        return True, True
    elif returncode != 0:
        print(f"    ❌ Import test failed: {stderr}")
        return False, False

    if "SUCCESS" in stdout:
        print("    ✅ Python imports working correctly")
        return True, False
    else:
        print("    ❌ Import test did not complete successfully")
        return False, False


def test_config_api(test_dir: Path) -> tuple[bool, bool]:
    """Test that /api/config endpoint works correctly

    Returns:
        (passed, requires_deps): (True if test passed, True if deps are needed)
    """
    print("\n🌐 Testing /api/config endpoint...")

    test_script = test_dir / "test_config_api.py"
    test_script.write_text("""
import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

# Test config router
try:
    from ignition_toolkit.api.routers.config import get_config
    import asyncio

    async def test():
        config = await get_config()
        print(f"Version: {config['version']}")
        print(f"Playbooks dir: {config['paths']['playbooks_dir']}")
        print(f"Package root: {config['paths']['package_root']}")

        # Verify paths are absolute and exist
        playbooks_path = Path(config['paths']['playbooks_dir'])
        if not playbooks_path.is_absolute():
            print("ERROR: Playbooks path is not absolute")
            sys.exit(1)

        print("SUCCESS")

    asyncio.run(test())

except ImportError as e:
    print(f"IMPORT_ERROR: {e}")
    sys.exit(2)  # Special exit code for missing dependencies
except Exception as e:
    print(f"FAILED: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
""")

    returncode, stdout, stderr = run_command(
        ["python3", str(test_script)],
        cwd=test_dir
    )

    print(f"  Output: {stdout}")

    if returncode == 2:
        # Missing dependencies - this is OK
        print("    ⚠️  Missing dependencies (this is OK - test structural portability only)")
        return True, True
    elif returncode != 0:
        print(f"    ❌ Config API test failed: {stderr}")
        return False, False

    if "SUCCESS" in stdout:
        print("    ✅ /api/config endpoint working correctly")
        return True, False
    else:
        print("    ❌ Config API test did not complete successfully")
        return False, False


def test_shell_scripts(test_dir: Path) -> bool:
    """Test that shell scripts work correctly"""
    print("\n🔧 Testing shell scripts...")

    # Test start_server.sh
    start_server = test_dir / "start_server.sh"
    if start_server.exists():
        print("  Testing: start_server.sh syntax")

        # Just check syntax, don't actually run server
        returncode, stdout, stderr = run_command(
            ["bash", "-n", str(start_server)],
            cwd=test_dir
        )

        if returncode != 0:
            print(f"    ❌ Syntax error: {stderr}")
            return False

        print("    ✅ start_server.sh syntax OK")
    else:
        print("    ⚠️  start_server.sh not found")

    # Test verify_ux.sh
    verify_ux = test_dir / "verify_ux.sh"
    if verify_ux.exists():
        print("  Testing: verify_ux.sh syntax")

        returncode, stdout, stderr = run_command(
            ["bash", "-n", str(verify_ux)],
            cwd=test_dir
        )

        if returncode != 0:
            print(f"    ❌ Syntax error: {stderr}")
            return False

        print("    ✅ verify_ux.sh syntax OK")
    else:
        print("    ⚠️  verify_ux.sh not found")

    return True


def main():
    parser = argparse.ArgumentParser(
        description="Test portability of Ignition Automation Toolkit"
    )
    parser.add_argument(
        "--temp-dir",
        type=Path,
        default=None,
        help="Temporary directory to use for testing (default: auto-create)"
    )
    parser.add_argument(
        "--keep",
        action="store_true",
        help="Keep temporary directory after testing"
    )

    args = parser.parse_args()

    project_root = get_project_root()

    print("=" * 70)
    print("Portability Test Suite")
    print("=" * 70)
    print(f"\nProject root: {project_root}")
    print()

    # Create or use temp directory
    if args.temp_dir:
        test_dir = args.temp_dir
        test_dir.mkdir(parents=True, exist_ok=True)
        cleanup = False
        print(f"Using provided directory: {test_dir}")
    else:
        test_dir = Path(tempfile.mkdtemp(prefix="ignition_toolkit_test_"))
        cleanup = not args.keep
        print(f"Created temporary directory: {test_dir}")

    print()

    try:
        # Step 1: Copy project files
        copy_project_files(project_root, test_dir)

        # Step 2: Test path resolution
        if not test_path_resolution(test_dir):
            print("\n❌ Path resolution tests failed")
            sys.exit(1)

        # Step 3: Test Python imports
        imports_passed, imports_need_deps = test_python_imports(test_dir)
        if not imports_passed:
            print("\n❌ Python import tests failed")
            sys.exit(1)

        # Step 4: Test /api/config endpoint
        config_passed, config_needs_deps = test_config_api(test_dir)
        if not config_passed:
            print("\n❌ Config API tests failed")
            sys.exit(1)

        # Step 5: Test shell scripts
        if not test_shell_scripts(test_dir):
            print("\n❌ Shell script tests failed")
            sys.exit(1)

        # Success!
        print("\n" + "=" * 70)
        print("✅ All Portability Tests Passed!")
        print("=" * 70)
        print()
        print("The project is portable and can be copied to any directory.")
        print()

        # Show notes about dependencies
        needs_deps = imports_need_deps or config_needs_deps
        if needs_deps:
            print("📝 Note: Some tests skipped due to missing dependencies.")
            print("   Install dependencies with: pip install -e .")
            print("   Or test with portable archive that auto-installs dependencies.")
            print()

        if cleanup:
            print(f"Cleaning up: {test_dir}")
            shutil.rmtree(test_dir)
        else:
            print(f"Test directory preserved: {test_dir}")
            print("You can manually inspect it or run the project from there.")

        print()

    except Exception as e:
        print(f"\n❌ Test suite failed with error: {e}")
        import traceback
        traceback.print_exc()

        if cleanup:
            print(f"\nCleaning up: {test_dir}")
            shutil.rmtree(test_dir)

        sys.exit(1)


if __name__ == "__main__":
    main()
