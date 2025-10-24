# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |

## Security Considerations

### WebSocket Authentication

**Current Implementation:**
The WebSocket endpoint uses a simple API key authentication mechanism:
- API key is passed as a query parameter: `ws://localhost:5000/ws/executions?api_key=xxx`
- Default key is `dev-key-change-in-production`

**Security Concerns:**
1. **Query Parameter Exposure**: API keys in query parameters are logged by:
   - Web servers (access logs)
   - Browser history
   - Proxy servers
   - Network monitoring tools

2. **Static Key**: Single static key for all users provides no user-level access control

3. **No Expiration**: API key never expires, increasing risk if compromised

**Production Requirements:**

⚠️ **CRITICAL**: This authentication mechanism is suitable for DEVELOPMENT ONLY.

Before deploying to production, you MUST:

1. **Use HTTPS/WSS**: Never use WebSocket over plain HTTP in production
   ```python
   # Enable TLS
   uvicorn main:app --ssl-keyfile=./key.pem --ssl-certfile=./cert.pem
   ```

2. **Set Strong API Key**: Change the default API key via environment variable
   ```bash
   export WEBSOCKET_API_KEY="$(openssl rand -hex 32)"
   ```

3. **Consider JWT Migration**: For production deployments with multiple users, implement JWT authentication:
   ```python
   # Recommended approach:
   from jose import jwt, JWTError

   @app.websocket("/ws/executions")
   async def websocket_endpoint(websocket: WebSocket):
       token = websocket.query_params.get("token")
       try:
           payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
           user_id = payload.get("user_id")
           # Proceed with authenticated user
       except JWTError:
           await websocket.close(code=1008, reason="Invalid token")
   ```

4. **Rotate Keys Regularly**: If using static API keys, rotate them quarterly

### Credential Storage

Credentials are encrypted at rest using Fernet encryption (symmetric):
- Encryption key stored in `~/.ignition-toolkit/encryption.key`
- Protect this file with appropriate filesystem permissions (chmod 600)
- **Never commit credentials or encryption keys to git**

### Path Traversal Protection

Playbook paths are validated to prevent directory traversal attacks:
- Paths are resolved and checked against allowed directory
- Symlinks should be avoided (future: add explicit check)
- File size limits should be enforced (future: add 1MB limit)

### Input Validation

**Current State**: Basic validation implemented
- Playbook paths validated against directory traversal
- Gateway URLs should start with http:// or https://
- Parameter lengths limited to prevent DoS

**Recommendations**:
- Validate all user inputs
- Sanitize file paths
- Limit request sizes
- Implement rate limiting

### CORS Configuration

CORS is restricted to localhost by default:
```python
ALLOWED_ORIGINS = [
    "http://localhost:5000",
    "http://127.0.0.1:5000",
    "http://localhost:3000",  # Development frontend
    "http://127.0.0.1:3000"
]
```

⚠️ **Production Warning**: If binding to 0.0.0.0, ensure ALLOWED_ORIGINS is properly configured for your domain.

### Database Security

- SQLite database should have appropriate file permissions
- No SQL injection vectors (using SQLAlchemy ORM)
- Execution history may contain sensitive information - protect access

## Reporting a Vulnerability

If you discover a security vulnerability, please:

1. **DO NOT** open a public GitHub issue
2. Email the maintainer with details
3. Allow 48 hours for initial response
4. Coordinate disclosure timeline

## Security Checklist for Production Deployment

- [ ] Change WEBSOCKET_API_KEY from default
- [ ] Enable HTTPS/WSS (no plain HTTP/WS)
- [ ] Set appropriate CORS origins (no wildcards)
- [ ] Protect encryption.key file (chmod 600)
- [ ] Enable firewall rules (only allow necessary ports)
- [ ] Review and set appropriate file permissions on playbooks directory
- [ ] Implement rate limiting on API endpoints
- [ ] Enable logging and monitoring
- [ ] Regular security updates for dependencies
- [ ] Consider JWT authentication for multi-user deployments
- [ ] Regular backup of database and credentials

## Dependencies

Keep dependencies updated to receive security patches:
```bash
# Backend
pip install --upgrade ignition-toolkit

# Frontend
cd frontend && npm audit fix
```

## Contact

For security concerns, please contact the maintainer directly rather than opening public issues.
