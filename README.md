# Ignition Automation Toolkit

> Lightweight, transferable automation platform for Ignition SCADA Gateway operations

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

## 🎯 Overview

A modern, Docker-free automation toolkit for Ignition SCADA with:

- **Gateway Automation**: REST API client for modules, projects, tags, backups
- **Playbook System**: YAML-based reusable workflows with step-by-step execution
- **Real-Time Control**: Pause, resume, skip steps during execution
- **Browser Automation**: Live Playwright viewing for web-based operations
- **Secure Credentials**: Encrypted local storage, never committed to git
- **Import/Export**: Share playbooks as JSON with colleagues
- **AI-Ready**: Integration points for AI-assisted testing steps
- **Web UI**: React-based interface for control and monitoring

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- Linux or WSL2 Ubuntu
- pip

### Installation

```bash
# Clone repository
git clone <repo-url>
cd ignition-playground

# Install in development mode
pip install -e .

# Initialize credential vault
ignition-toolkit init

# Start server
ignition-toolkit serve
```

Access the web UI at http://localhost:5000

### Your First Playbook

```bash
# Run example module upgrade playbook
ignition-toolkit run playbooks/gateway/module_upgrade.yaml \
  --config my-gateway-config
```

## 📚 Documentation

- [Getting Started Guide](docs/getting_started.md)
- [Playbook Syntax](docs/playbook_syntax.md)
- [Gateway API Reference](docs/gateway_api.md)
- [Credential Management](docs/credentials.md)
- [AI Integration](docs/ai_integration.md)

## 🏗️ Architecture

```
┌─────────────────────────────────────┐
│     Web UI (React + Material-UI)    │
│        http://localhost:5000         │
└──────────────┬──────────────────────┘
               │ WebSocket + REST API
               ▼
┌─────────────────────────────────────┐
│    FastAPI Backend                   │
│  • Playbook Engine                   │
│  • Gateway Client                    │
│  • Browser Automation                │
│  • Credential Vault                  │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  SQLite + Local File Storage         │
│  • Execution History                 │
│  • Encrypted Credentials (~/.ignition-toolkit/)
│  • Playbook Library                  │
└─────────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  External Ignition Gateway(s)        │
│        Your SCADA Systems            │
└─────────────────────────────────────┘
```

## 📁 Project Structure

```
ignition-playground/
├── ignition_toolkit/          # Main Python package
│   ├── gateway/               # Gateway REST API client
│   ├── playbook/              # Execution engine
│   ├── browser/               # Browser automation
│   ├── credentials/           # Secure credential storage
│   ├── api/                   # FastAPI server
│   └── storage/               # Data persistence
├── playbooks/                 # Playbook library (YAML)
├── frontend/                  # React UI
├── tests/                     # Test suite
└── docs/                      # Documentation
```

## 🔑 Key Features

### Playbook System

Define reusable automation workflows in YAML:

```yaml
name: "Ignition Module Upgrade"
version: "1.0"

parameters:
  - name: gateway_url
    type: string
  - name: gateway_password
    type: credential
  - name: module_file
    type: file

steps:
  - id: authenticate
    name: "Login to Gateway"
    type: gateway.login

  - id: upload
    name: "Upload Module"
    type: gateway.upload_module
    parameters:
      file: "{{ module_file }}"

  - id: restart
    name: "Restart Gateway"
    type: gateway.restart
    wait_for_ready: true
```

### Secure Credential Storage

Credentials encrypted with Fernet and stored locally:

```bash
# Add credential via CLI
ignition-toolkit credential add gateway_admin \
  --username admin \
  --password <your-password>

# Reference in playbooks
parameters:
  gateway_password: "{{ credential.gateway_admin }}"
```

### Import/Export Playbooks

Share workflows with your team:

```bash
# Export playbook to JSON
ignition-toolkit export playbooks/gateway/module_upgrade.yaml \
  --output module_upgrade.json

# Import on colleague's machine
ignition-toolkit import module_upgrade.json
```

### Real-Time Execution Control

- ⏸️ **Pause**: Stop after current step completes
- ⏭️ **Skip**: Skip current step and continue
- ▶️ **Resume**: Continue paused execution
- 🎥 **Live Browser**: Watch automation in real-time
- 📊 **WebSocket Logs**: Streaming execution updates

## 🧪 Testing

```bash
# Run all tests
pytest tests/ -v

# Test Gateway client
pytest tests/test_gateway_client.py -v

# Test playbook execution
pytest tests/test_playbook_engine.py -v
```

## 🔒 Security

- **Credentials**: Encrypted with Fernet, stored in `~/.ignition-toolkit/credentials.db`
- **Encryption Key**: Generated on first run, stored locally
- **Never in Git**: Credential vault excluded via `.gitignore`
- **Playbook Export**: Credentials replaced with references, never exported

## 🤝 Contributing

Contributions welcome! This project uses:

- **Code Style**: Black formatter, type hints everywhere
- **Testing**: pytest with >70% coverage target
- **Documentation**: Google-style docstrings

## 📄 License

MIT License - see [LICENSE](LICENSE) file

## 🙏 Acknowledgments

- [Inductive Automation](https://inductiveautomation.com/) - Ignition SCADA Platform
- Built for automation engineers and test teams

---

**Questions or Issues?** Open an issue on GitHub
