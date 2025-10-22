## Getting Started with Ignition Automation Toolkit

This guide will help you get up and running with the Ignition Automation Toolkit.

## Installation

### Prerequisites

- Python 3.10 or higher
- Linux or WSL2
- Ignition Gateway (for Gateway automation)

### Install Package

```bash
# Clone repository
cd /git/ignition-playground

# Install in development mode
pip install -e .

# Install Playwright browsers (for browser automation)
playwright install chromium

# Verify installation
ignition-toolkit --version
```

## Quick Start

### 1. Initialize

```bash
# Initialize credential vault and directories
ignition-toolkit init
```

This creates:
- `~/.ignition-toolkit/` - Credential vault
- `./data/` - Database and artifacts
- `./playbooks/` - Playbook library

### 2. Add Credentials

```bash
# Add Gateway credential
ignition-toolkit credential add gateway_admin \
  --username admin \
  --password your_password \
  --description "Gateway Admin Credential"

# List credentials
ignition-toolkit credential list
```

### 3. List Available Playbooks

```bash
ignition-toolkit playbook list
```

### 4. Run a Playbook

```bash
# Run health check playbook
ignition-toolkit playbook run \
  playbooks/examples/simple_health_check.yaml \
  --param gateway_url=http://localhost:8088 \
  --param gateway_credential=gateway_admin
```

### 5. Start Web UI

```bash
# Start the web server
ignition-toolkit serve --port 5000

# Open browser to http://localhost:5000
```

## Next Steps

- [Playbook Syntax](playbook_syntax.md) - Learn to write playbooks
- [Gateway API](gateway_api.md) - Gateway operations reference
- [Browser Automation](browser_automation.md) - Web automation guide
- [Credentials](credentials.md) - Credential management

## Common Tasks

### Run Playbook with Parameters

```bash
ignition-toolkit playbook run my_playbook.yaml \
  --param param1=value1 \
  --param param2=value2
```

### Export Playbook for Sharing

```bash
ignition-toolkit playbook export \
  playbooks/gateway/module_upgrade.yaml \
  --output shared/module_upgrade.json
```

### Import Shared Playbook

```bash
ignition-toolkit playbook import \
  module_upgrade.json \
  --output-dir ./playbooks/imported
```

## Troubleshooting

### Package Import Errors

```bash
pip install -e . --force-reinstall
```

### Playwright Issues

```bash
playwright install --force chromium
```

### Database Issues

```bash
rm -f ./data/toolkit.db
# Restart - will recreate
```

## Getting Help

- Check the documentation in `docs/`
- Review example playbooks in `playbooks/`
- See `TESTING_GUIDE.md` for validation steps
