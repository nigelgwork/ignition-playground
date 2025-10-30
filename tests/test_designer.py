"""
Tests for Designer automation

Basic tests for Designer module functionality.
Note: Full integration tests require Designer installation and manual verification.
"""

import platform
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ignition_toolkit.designer import DesignerManager
from ignition_toolkit.designer.detector import (
    detect_designer_installation,
    get_java_command,
)


class TestDesignerDetector:
    """Tests for Designer installation detection"""

    def test_get_java_command(self):
        """Test Java command detection"""
        java_cmd = get_java_command()
        assert java_cmd is not None
        assert isinstance(java_cmd, str)
        # Should return either a path or "java"
        assert java_cmd in ["java"] or Path(java_cmd).exists() or "java" in java_cmd.lower()

    def test_detect_designer_installation(self):
        """Test Designer installation detection"""
        # This test will likely return None unless Designer is actually installed
        install_path = detect_designer_installation()
        # Should return None or a valid Path
        assert install_path is None or isinstance(install_path, Path)

    @patch("platform.system")
    def test_detect_designer_installation_windows(self, mock_system):
        """Test Windows-specific detection"""
        mock_system.return_value = "Windows"

        # Import after mocking to ensure correct system detection
        from ignition_toolkit.designer.detector import detect_designer_installation

        # Will return None unless Windows paths exist
        result = detect_designer_installation()
        assert result is None or isinstance(result, Path)

    @patch("platform.system")
    def test_detect_designer_installation_linux(self, mock_system):
        """Test Linux-specific detection"""
        mock_system.return_value = "Linux"

        from ignition_toolkit.designer.detector import detect_designer_installation

        result = detect_designer_installation()
        assert result is None or isinstance(result, Path)


class TestDesignerManager:
    """Tests for DesignerManager"""

    def test_designer_manager_init(self):
        """Test DesignerManager initialization"""
        manager = DesignerManager()
        assert manager is not None
        assert isinstance(manager.screenshots_dir, Path)
        assert isinstance(manager.downloads_dir, Path)

    def test_designer_manager_with_custom_paths(self):
        """Test DesignerManager with custom paths"""
        screenshots_dir = Path("/tmp/screenshots")
        downloads_dir = Path("/tmp/downloads")

        manager = DesignerManager(
            screenshots_dir=screenshots_dir, downloads_dir=downloads_dir
        )

        assert manager.screenshots_dir == screenshots_dir
        assert manager.downloads_dir == downloads_dir

    @pytest.mark.asyncio
    async def test_designer_manager_context_manager(self):
        """Test DesignerManager as async context manager"""
        manager = DesignerManager()

        # Mock platform automation to avoid actual initialization
        with patch.object(manager, "start") as mock_start:
            with patch.object(manager, "stop") as mock_stop:
                async with manager as mgr:
                    assert mgr is manager
                    mock_start.assert_called_once()
                mock_stop.assert_called_once()

    @pytest.mark.asyncio
    async def test_designer_manager_start_windows(self):
        """Test Designer manager start on Windows"""
        if platform.system() != "Windows":
            pytest.skip("Windows-only test")

        manager = DesignerManager()

        # This will attempt to import pywinauto
        # Skip if not installed
        try:
            await manager.start()
            assert manager.platform_automation is not None
            await manager.stop()
        except ImportError as e:
            pytest.skip(f"pywinauto not available: {e}")

    @pytest.mark.asyncio
    async def test_designer_manager_start_linux(self):
        """Test Designer manager start on Linux"""
        if platform.system() != "Linux":
            pytest.skip("Linux-only test")

        manager = DesignerManager()

        # This will attempt to import Xlib
        # Skip if not installed
        try:
            await manager.start()
            assert manager.platform_automation is not None
            await manager.stop()
        except ImportError as e:
            pytest.skip(f"Linux automation libraries not available: {e}")

    @pytest.mark.asyncio
    async def test_designer_manager_launch_via_file_not_found(self):
        """Test launch with non-existent file"""
        manager = DesignerManager()
        await manager.start()

        non_existent_file = Path("/tmp/nonexistent_launcher.jnlp")

        with pytest.raises(FileNotFoundError):
            await manager.launch_via_file(non_existent_file)

        await manager.stop()

    @pytest.mark.asyncio
    async def test_designer_manager_login_not_initialized(self):
        """Test login fails if platform automation not initialized"""
        manager = DesignerManager()
        # Don't call start()

        with pytest.raises(RuntimeError, match="Platform automation not initialized"):
            await manager.login("admin", "password")

    @pytest.mark.asyncio
    async def test_designer_manager_screenshot_not_initialized(self):
        """Test screenshot fails if platform automation not initialized"""
        manager = DesignerManager()
        # Don't call start()

        with pytest.raises(RuntimeError, match="Platform automation not initialized"):
            await manager.screenshot("test")


class TestPlatformAutomation:
    """Tests for platform-specific automation"""

    @pytest.mark.skipif(
        platform.system() != "Windows", reason="Windows-only test"
    )
    def test_windows_automation_import(self):
        """Test Windows automation module can be imported"""
        try:
            from ignition_toolkit.designer.platform_windows import (
                WindowsDesignerAutomation,
            )

            automation = WindowsDesignerAutomation()
            assert automation is not None
        except ImportError as e:
            pytest.skip(f"pywinauto not available: {e}")

    @pytest.mark.skipif(
        platform.system() != "Linux", reason="Linux-only test"
    )
    def test_linux_automation_import(self):
        """Test Linux automation module can be imported"""
        try:
            from ignition_toolkit.designer.platform_linux import LinuxDesignerAutomation

            automation = LinuxDesignerAutomation()
            assert automation is not None
        except ImportError as e:
            pytest.skip(f"Linux automation libraries not available: {e}")


# Integration tests (require actual Designer installation)
@pytest.mark.integration
@pytest.mark.slow
class TestDesignerIntegration:
    """
    Integration tests for Designer automation

    These tests require:
    - Ignition Designer installed
    - Gateway running at localhost:8088
    - Valid credentials

    Run with: pytest tests/test_designer.py -m integration
    """

    @pytest.mark.asyncio
    async def test_full_designer_launch_workflow(self):
        """
        Full test: Launch Designer, login, open project

        This test is skipped by default - enable manually for testing
        """
        pytest.skip("Manual integration test - requires Designer installation")

        manager = DesignerManager()
        await manager.start()

        try:
            # Create mock launcher file
            launcher_file = Path("/tmp/test_launcher.jnlp")
            launcher_file.write_text("<jnlp></jnlp>")  # Mock JNLP

            # Launch Designer
            success = await manager.launch_via_file(launcher_file, wait_for_window=True)
            assert success

            # Login
            success = await manager.login("admin", "password", timeout=30)
            assert success

            # Open project
            success = await manager.open_project("TestProject", timeout=30)
            assert success

            # Screenshot
            screenshot_path = await manager.screenshot("integration_test")
            assert screenshot_path.exists()

        finally:
            await manager.stop()
