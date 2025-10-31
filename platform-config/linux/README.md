# Linux Platform Configuration

This directory contains Linux-specific configuration files for building portable distributions of Ignition Automation Toolkit.

## Files

### requirements.txt
Python packages specific to Linux platform (installed via pip):
- `python-xlib` - X11 protocol client library for desktop automation
- `pyatspi` - AT-SPI accessibility interface for UI element inspection

### system-deps.txt
System-level packages required on Linux (installed via apt-get):
- `xdotool` - Command-line X11 automation tool
- `imagemagick` - Image processing utilities
- `default-jre` - Java Runtime Environment (required for Ignition Designer)
- `libatspi2.0-dev` - AT-SPI development libraries
- `python3-gi` - Python GObject introspection bindings
- `libx11-dev` - X11 development headers

### launcher.sh.template
Template for the Linux launcher script. Variables will be substituted during build:
- `{PYTHON_VERSION}` - Python version (e.g., "3.10")
- `{TOOLKIT_VERSION}` - Toolkit version (e.g., "4.0.2")

## Installation Instructions

### Debian/Ubuntu
```bash
# Install system dependencies
xargs -a system-deps.txt sudo apt-get install -y

# Python dependencies are automatically installed during portable build
```

### Red Hat/CentOS/Fedora
```bash
# Convert package names to yum equivalents
# Note: Package names may differ slightly
sudo yum install xdotool ImageMagick java-11-openjdk python3-gobject libX11-devel
```

## WSL2 Considerations

When using WSL2, additional steps are required for GUI support:
1. Install an X server on Windows (e.g., VcXsrv, X410)
2. Set DISPLAY environment variable: `export DISPLAY=:0`
3. Configure X server to allow connections from WSL2

See `/docs/deployment/wsl2_deployment.md` for detailed instructions.

## Build Process

The `scripts/build/build_linux.py` script uses these configuration files to:
1. Create a Python virtual environment
2. Install common dependencies from `platform-config/common/requirements.txt`
3. Install Linux-specific dependencies from `requirements.txt`
4. Generate launcher script from template
5. Package everything into a portable archive

## Testing

To verify system dependencies are installed:
```bash
python3 scripts/check_system_deps.py --platform linux
```
