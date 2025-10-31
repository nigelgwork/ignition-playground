# Windows Platform Configuration

This directory contains Windows-specific configuration files for building portable distributions of Ignition Automation Toolkit.

## Files

### requirements.txt
Python packages specific to Windows platform (installed via pip):
- `pywinauto` - Windows UI Automation API wrapper for desktop automation

### system-deps.txt
System-level dependencies required on Windows:
- **PowerShell 5.0+** (included in Windows 10+)
- **.NET Framework 4.5+** (included in Windows 10+)
- **Java Runtime Environment 11+** (required for Ignition Designer)

### launcher.bat.template
Template for the Windows launcher batch script. Variables will be substituted during build:
- `{PYTHON_VERSION}` - Python version (e.g., "3.10")
- `{TOOLKIT_VERSION}` - Toolkit version (e.g., "4.0.2")

## Installation Instructions

### Prerequisites Check
Open PowerShell and run:
```powershell
# Check PowerShell version
$PSVersionTable.PSVersion

# Check .NET Framework
Get-ItemProperty "HKLM:SOFTWARE\Microsoft\NET Framework Setup\NDP\v4\Full" | Select-Object Version

# Check Java
java -version
```

### Installing Java
If Java is not installed:
1. Download from [Adoptium](https://adoptium.net/) or [Oracle](https://www.oracle.com/java/technologies/downloads/)
2. Install Java 11 or higher
3. Verify installation: `java -version`

### Python Dependencies
Python dependencies are automatically installed during the portable build process. No manual installation required.

## Build Process

The `scripts/build/build_windows.py` script uses these configuration files to:
1. Create a Python virtual environment
2. Install common dependencies from `platform-config/common/requirements.txt`
3. Install Windows-specific dependencies from `requirements.txt`
4. Generate launcher batch script from template
5. Package everything into a portable archive (.zip)

## Running the Portable Distribution

1. Extract the `.zip` archive to any directory
2. Double-click `run.bat` to launch the toolkit
3. The launcher will:
   - Check system prerequisites
   - Activate the Python virtual environment
   - Start the Ignition Toolkit server
   - Open your default browser to the web interface

## System Requirements

- **Operating System**: Windows 10 or higher (64-bit)
- **Python**: Bundled in portable distribution (no installation required)
- **RAM**: 2GB minimum, 4GB recommended
- **Disk Space**: 500MB for toolkit + space for playbooks and execution history
- **Network**: Required for connecting to Ignition Gateway

## Testing

To verify system dependencies before running:
```powershell
python scripts\check_system_deps.py --platform windows
```

## Troubleshooting

### PowerShell Execution Policy
If you encounter "script execution is disabled" errors:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Firewall Warnings
The toolkit runs a local web server (default port 5000). You may see Windows Firewall prompts - allow access for localhost connections.

### Java Not Found
If Designer automation fails with "Java not found":
1. Install Java (see above)
2. Add Java to PATH: `setx PATH "%PATH%;C:\Program Files\Java\jdk-11\bin"`
3. Restart PowerShell
