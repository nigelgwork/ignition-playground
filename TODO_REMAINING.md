# Remaining Work - Quick Implementation Guide

## 🎯 Priority 1: Add Sidebar Navigation

The Executions and Credentials buttons need to work. Here's how to implement:

### File to Edit: `/frontend/index.html`

Add this JavaScript after line ~950 (after theme toggle code):

```javascript
// Navigation system
document.querySelectorAll('.nav-item').forEach(item => {
    item.addEventListener('click', function() {
        // Remove active from all
        document.querySelectorAll('.nav-item').forEach(nav => nav.classList.remove('active'));
        // Add active to clicked
        this.classList.add('active');

        // Get page name
        const page = this.querySelector('span:not(.material-icons)').textContent.toLowerCase();

        // Show appropriate content
        if (page === 'playbooks') {
            document.querySelector('.card:nth-child(1)').style.display = 'block';
            document.querySelector('.card:nth-child(2)').style.display = 'block';
        } else if (page === 'executions') {
            alert('Executions page - coming soon! For now check the "Recent Executions" section on the Playbooks page.');
        } else if (page === 'credentials') {
            showCredentialsPage();
        }
    });
});
```

## 🎯 Priority 2: Credentials Management

### Option A: Quick CLI Method (RECOMMENDED FOR NOW)

```bash
# In terminal
cd /git/ignition-playground
source venv/bin/activate

# Add Gateway credential
ignition-toolkit credential add gateway_admin
# Enter username: admin
# Enter password: password

# List credentials
ignition-toolkit credential list

# Delete credential
ignition-toolkit credential delete gateway_admin
```

### Option B: Add Credentials UI Page (More work)

Create a new function in index.html:

```javascript
function showCredentialsPage() {
    const main = document.querySelector('.main-content');
    main.innerHTML = `
        <div class="card elevation-1">
            <h2 class="card-title">🔑 Credentials Management</h2>
            <div style="margin-bottom: 20px;">
                <button class="btn btn-primary" onclick="showAddCredentialModal()">
                    <span class="material-icons">add</span>
                    Add Credential
                </button>
            </div>
            <div id="credentialsList">Loading...</div>
        </div>
    `;
    loadCredentials();
}

async function loadCredentials() {
    // TODO: Implement API endpoint to list credentials
    // For now, show message to use CLI
    document.getElementById('credentialsList').innerHTML = `
        <div class="empty-state">
            <span class="material-icons">info</span>
            <h3>Use CLI to Manage Credentials</h3>
            <p>Run: <code>ignition-toolkit credential add gateway_admin</code></p>
        </div>
    `;
}
```

## 🎯 Priority 3: API Endpoint for Credentials

### File: `/ignition_toolkit/api/app.py`

Add these endpoints after the playbook endpoints:

```python
@app.get("/api/credentials")
async def list_credentials():
    """List all credentials (without passwords)"""
    vault = CredentialVault()
    credentials = vault.list_credentials()
    return [{"name": c.name, "username": c.username, "description": c.description} for c in credentials]

@app.post("/api/credentials")
async def add_credential(name: str, username: str, password: str, description: str = ""):
    """Add new credential"""
    vault = CredentialVault()
    from ignition_toolkit.credentials import Credential
    vault.save_credential(Credential(name=name, username=username, password=password, description=description))
    return {"message": "Credential added successfully"}

@app.delete("/api/credentials/{name}")
async def delete_credential(name: str):
    """Delete credential"""
    vault = CredentialVault()
    success = vault.delete_credential(name)
    if success:
        return {"message": "Credential deleted"}
    raise HTTPException(status_code=404, detail="Credential not found")
```

## ✅ What's Already Working

1. ✅ Server running on port 5000
2. ✅ Version 1.0.1 displaying correctly
3. ✅ No more flickering
4. ✅ Manual refresh button works
5. ✅ Collapsible sections (Gateway/Designer/Perspective)
6. ✅ Configure buttons open modal
7. ✅ Modal has parameter inputs
8. ✅ Execute button triggers API call

## 🚀 Quick Start for Testing

1. **Add a credential via CLI:**
   ```bash
   ignition-toolkit credential add gateway_admin
   ```

2. **Open browser:**
   ```
   http://localhost:5000
   ```

3. **Click "Configure" on any Gateway playbook**

4. **Enter values:**
   - Gateway URL: `http://localhost:8088` (or your Gateway IP)
   - Credential: Select `gateway_admin` from dropdown

5. **Click "Execute"**

6. **Watch "Recent Executions" section for progress**

## 📋 Server Commands

```bash
# Start server
cd /git/ignition-playground
source venv/bin/activate
ignition-toolkit serve --host 0.0.0.0 --port 5000

# Check if running
curl http://localhost:5000/health

# View logs
tail -f /tmp/server.log
```

## 🎨 UI Customization

All styles are in the `<style>` section of `/frontend/index.html`. Key CSS variables:

```css
--primary-color: #58a6ff;
--success-color: #3fb950;
--error-color: #f85149;
--background: #01050d;
--surface: #161b22;
```

## 📦 Backup Files

- `/frontend/index.html.old` - Previous version
- `/frontend/index.html.backup` - Earlier backup

To restore: `mv index.html.old index.html`

---

**Last Updated:** 2025-10-24
**Status:** Server running, basic features working, credentials UI pending
**Access:** http://localhost:5000
