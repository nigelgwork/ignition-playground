#!/usr/bin/env python3
"""
System Dependency Checker

Validates that all required system dependencies are installed before
running the Ignition Automation Toolkit.

Usage:
    python scripts/check_system_deps.py [--platform {linux,windows,auto}]
    python scripts/check_system_deps.py --fix  # Suggest fix commands

Exit codes:
    0 - All dependencies satisfied
    1 - Missing required dependencies
    2 - Platform not supported or detection failed
"""

import argparse
import platform
import shutil
import subprocess
import sys
from pathlib import Path


class Colors:
    """ANSI color codes for terminal output"""
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'

    @classmethod
    def disable(cls):
        """Disable colors (for Windows or when piping)"""
        cls.GREEN = ''
        cls.YELLOW = ''
        cls.RED = ''
        cls.BLUE = ''
        cls.BOLD = ''
        cls.END = ''


def detect_platform():
    """Detect current platform"""
    system = platform.system().lower()

    if system == "windows" or system.startswith("win"):
        return "windows"
    elif system == "linux":
        # Check if WSL2
        try:
            with open("/proc/version", "r") as f:
                if "microsoft" in f.read().lower():
                    return "wsl2"
        except:
            pass
        return "linux"
    elif system == "darwin":
        return "macos"
    else:
        return "unknown"


def check_command(command, name=None):
    """Check if a command exists in PATH"""
    if name is None:
        name = command

    exists = shutil.which(command) is not None
    return {
        "name": name,
        "command": command,
        "exists": exists,
        "type": "command"
    }


def check_python_version():
    """Check Python version is 3.10+"""
    version = sys.version_info
    meets_requirement = version.major == 3 and version.minor >= 10

    return {
        "name": "Python 3.10+",
        "command": f"python{version.major}.{version.minor}",
        "exists": meets_requirement,
        "type": "version",
        "current": f"{version.major}.{version.minor}.{version.micro}",
        "required": "3.10+"
    }


def check_java():
    """Check Java version"""
    try:
        result = subprocess.run(
            ["java", "-version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        # Java version output goes to stderr
        output = result.stderr

        # Parse version (look for "version" followed by number)
        import re
        match = re.search(r'version "(\d+)\.', output)
        if match:
            major_version = int(match.group(1))
            # Java 11+ required
            meets_requirement = major_version >= 11

            return {
                "name": "Java 11+",
                "command": "java",
                "exists": meets_requirement,
                "type": "version",
                "current": f"{major_version}.x",
                "required": "11+"
            }

    except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
        pass

    return {
        "name": "Java 11+",
        "command": "java",
        "exists": False,
        "type": "version"
    }


def check_linux_deps():
    """Check Linux-specific dependencies"""
    deps = []

    # System commands
    deps.append(check_command("xdotool", "xdotool (X11 automation)"))
    deps.append(check_command("convert", "ImageMagick"))
    deps.append(check_java())

    # Libraries (check via pkg-config or direct file check)
    # Note: These are typically installed with system packages
    deps.append(check_command("pkg-config", "pkg-config"))

    return deps


def check_windows_deps():
    """Check Windows-specific dependencies"""
    deps = []

    # PowerShell
    ps_check = check_command("powershell", "PowerShell")
    if ps_check["exists"]:
        try:
            # Check PowerShell version
            result = subprocess.run(
                ["powershell", "-Command", "$PSVersionTable.PSVersion.Major"],
                capture_output=True,
                text=True,
                timeout=5
            )
            version = int(result.stdout.strip())
            ps_check["exists"] = version >= 5
            ps_check["type"] = "version"
            ps_check["current"] = f"{version}.x"
            ps_check["required"] = "5.0+"
            ps_check["name"] = "PowerShell 5.0+"
        except:
            pass

    deps.append(ps_check)
    deps.append(check_java())

    return deps


def check_wsl2_deps():
    """Check WSL2-specific dependencies (combines Linux deps + WSL considerations)"""
    deps = check_linux_deps()

    # Additional WSL2-specific checks
    # Check DISPLAY variable
    import os
    display = os.environ.get("DISPLAY")
    deps.append({
        "name": "DISPLAY variable",
        "command": "$DISPLAY",
        "exists": display is not None and display != "",
        "type": "environment",
        "current": display or "not set",
        "required": "set (e.g., 172.x.x.x:0)"
    })

    return deps


def print_results(deps, platform_name, suggest_fixes=False):
    """Print dependency check results"""
    print()
    print(f"{Colors.BOLD}System Dependency Check - {platform_name}{Colors.END}")
    print("=" * 70)
    print()

    missing = []
    for dep in deps:
        status_icon = f"{Colors.GREEN}✓{Colors.END}" if dep["exists"] else f"{Colors.RED}✗{Colors.END}"
        status_text = "FOUND" if dep["exists"] else "MISSING"

        if dep["type"] == "version":
            current = dep.get("current", "not found")
            required = dep.get("required", "")
            print(f"  {status_icon} {dep['name']:<30} {status_text}")
            if not dep["exists"] and current != "not found":
                print(f"      Current: {current}, Required: {required}")
        elif dep["type"] == "environment":
            print(f"  {status_icon} {dep['name']:<30} {status_text}")
            if not dep["exists"]:
                current = dep.get("current", "not set")
                required = dep.get("required", "")
                print(f"      Current: {current}, Required: {required}")
        else:
            print(f"  {status_icon} {dep['name']:<30} {status_text}")

        if not dep["exists"]:
            missing.append(dep)

    print()

    if missing:
        print(f"{Colors.YELLOW}Missing Dependencies: {len(missing)}{Colors.END}")
        print()

        if suggest_fixes:
            print_fix_suggestions(missing, platform_name)

        return False
    else:
        print(f"{Colors.GREEN}✓ All dependencies satisfied!{Colors.END}")
        print()
        return True


def print_fix_suggestions(missing_deps, platform_name):
    """Print installation commands for missing dependencies"""
    print(f"{Colors.BOLD}Installation Instructions:{Colors.END}")
    print()

    if platform_name == "Linux":
        print("Ubuntu/Debian:")
        print("  sudo apt-get update")

        packages = []
        for dep in missing_deps:
            cmd = dep["command"]
            if cmd == "xdotool":
                packages.append("xdotool")
            elif cmd == "convert":
                packages.append("imagemagick")
            elif cmd == "java":
                packages.append("default-jre")
            elif cmd == "pkg-config":
                packages.append("pkg-config")

        if packages:
            print(f"  sudo apt-get install -y {' '.join(packages)}")

        print()
        print("RHEL/CentOS/Fedora:")
        packages_rhel = []
        for pkg in packages:
            if pkg == "imagemagick":
                packages_rhel.append("ImageMagick")
            elif pkg == "default-jre":
                packages_rhel.append("java-11-openjdk")
            else:
                packages_rhel.append(pkg)
        if packages_rhel:
            print(f"  sudo dnf install -y {' '.join(packages_rhel)}")

    elif platform_name == "Windows":
        print("PowerShell:")
        for dep in missing_deps:
            if dep["command"] == "powershell":
                print("  Download from: https://aka.ms/powershell")
            elif dep["command"] == "java":
                print("  Download Java from: https://adoptium.net/")

    elif platform_name == "WSL2":
        print("Inside WSL2:")
        print("  sudo apt-get update")

        packages = []
        for dep in missing_deps:
            if dep["type"] == "environment" and "$DISPLAY" in dep["command"]:
                continue
            cmd = dep["command"]
            if cmd == "xdotool":
                packages.append("xdotool")
            elif cmd == "convert":
                packages.append("imagemagick")
            elif cmd == "java":
                packages.append("default-jre")

        if packages:
            print(f"  sudo apt-get install -y {' '.join(packages)}")

        # DISPLAY variable
        for dep in missing_deps:
            if dep["type"] == "environment" and "$DISPLAY" in dep["command"]:
                print()
                print("Set DISPLAY variable:")
                print("  export DISPLAY=$(cat /etc/resolv.conf | grep nameserver | awk '{print $2}'):0")
                print("  echo 'export DISPLAY=$(cat /etc/resolv.conf | grep nameserver | awk '\"'\"'{print $2}'\"'\"'):0' >> ~/.bashrc")

        print()
        print("On Windows host:")
        print("  Install X server: VcXsrv (https://sourceforge.net/projects/vcxsrv/)")
        print("  Or X410 from Microsoft Store")

    print()


def main():
    parser = argparse.ArgumentParser(
        description="Check system dependencies for Ignition Automation Toolkit"
    )
    parser.add_argument(
        "--platform",
        choices=["linux", "windows", "wsl2", "auto"],
        default="auto",
        help="Target platform (default: auto-detect)"
    )
    parser.add_argument(
        "--fix",
        action="store_true",
        help="Show installation commands for missing dependencies"
    )
    parser.add_argument(
        "--no-color",
        action="store_true",
        help="Disable colored output"
    )

    args = parser.parse_args()

    # Disable colors if requested or on Windows
    if args.no_color or platform.system() == "Windows":
        Colors.disable()

    # Detect platform
    if args.platform == "auto":
        detected_platform = detect_platform()
    else:
        detected_platform = args.platform

    # Platform-specific checks
    if detected_platform == "linux":
        deps = check_linux_deps()
        platform_name = "Linux"
    elif detected_platform == "windows":
        deps = check_windows_deps()
        platform_name = "Windows"
    elif detected_platform == "wsl2":
        deps = check_wsl2_deps()
        platform_name = "WSL2"
    elif detected_platform == "macos":
        print(f"{Colors.YELLOW}Warning: macOS is not officially supported yet{Colors.END}")
        print("Using Linux dependency checks...")
        deps = check_linux_deps()
        platform_name = "macOS (experimental)"
    else:
        print(f"{Colors.RED}Error: Unknown platform: {detected_platform}{Colors.END}")
        return 2

    # Print results
    all_satisfied = print_results(deps, platform_name, suggest_fixes=args.fix)

    # Exit code
    return 0 if all_satisfied else 1


if __name__ == "__main__":
    sys.exit(main())
