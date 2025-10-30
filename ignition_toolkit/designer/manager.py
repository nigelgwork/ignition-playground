"""
Designer manager - Desktop application automation for Ignition Designer

Handles Designer lifecycle, platform-specific automation, and operations.
Mirrors the BrowserManager pattern for consistency.
"""

import asyncio
import logging
import platform
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from ignition_toolkit.designer.detector import detect_designer_installation, get_java_command

logger = logging.getLogger(__name__)


class DesignerManager:
    """
    Manage Ignition Designer desktop application lifecycle

    Follows the same pattern as BrowserManager for consistency.
    Handles platform-specific automation via platform_windows/platform_linux modules.

    Example:
        async with DesignerManager() as manager:
            await manager.launch(
                gateway_url="http://localhost:8088",
                username="admin",
                password="password"
            )
            await manager.open_project("MyProject")
    """

    def __init__(
        self,
        install_path: Path | None = None,
        screenshots_dir: Path | None = None,
        downloads_dir: Path | None = None,
    ):
        """
        Initialize Designer manager

        Args:
            install_path: Custom Designer installation path (auto-detected if None)
            screenshots_dir: Directory for saving screenshots
            downloads_dir: Directory for JNLP/launcher downloads
        """
        self.install_path = install_path or detect_designer_installation()
        self.screenshots_dir = screenshots_dir or Path("./data/screenshots")
        self.screenshots_dir.mkdir(parents=True, exist_ok=True)
        self.downloads_dir = downloads_dir or Path("./data/downloads")
        self.downloads_dir.mkdir(parents=True, exist_ok=True)

        # Platform detection
        self.system = platform.system()
        logger.info(f"Designer manager initialized on {self.system}")

        # Platform-specific automation
        self.platform_automation = None

        # Process tracking
        self._process: subprocess.Popen | None = None
        self._launcher_file: Path | None = None

    async def __aenter__(self):
        """Async context manager entry"""
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.stop()

    async def start(self) -> None:
        """
        Start Designer manager

        Initializes platform-specific automation modules.
        """
        logger.info("Starting Designer manager...")

        # Initialize platform-specific automation
        if self.system == "Windows":
            from ignition_toolkit.designer.platform_windows import WindowsDesignerAutomation
            self.platform_automation = WindowsDesignerAutomation()
        elif self.system == "Linux":
            from ignition_toolkit.designer.platform_linux import LinuxDesignerAutomation
            self.platform_automation = LinuxDesignerAutomation()
        else:
            raise RuntimeError(f"Unsupported platform: {self.system}")

        logger.info("Designer manager started")

    async def stop(self) -> None:
        """
        Stop Designer manager

        Closes Designer if running and cleans up resources.
        """
        logger.info("Stopping Designer manager...")

        # Close Designer if running
        if self.platform_automation:
            try:
                self.platform_automation.close_designer()
            except Exception as e:
                logger.warning(f"Error closing Designer: {e}")

        # Terminate process if still running
        if self._process:
            try:
                self._process.terminate()
                # Wait up to 5 seconds for graceful shutdown
                try:
                    self._process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    logger.warning("Designer did not terminate gracefully, killing...")
                    self._process.kill()
            except Exception as e:
                logger.warning(f"Error terminating Designer process: {e}")
            finally:
                self._process = None

        # Clean up launcher file
        if self._launcher_file and self._launcher_file.exists():
            try:
                self._launcher_file.unlink()
            except Exception as e:
                logger.warning(f"Could not delete launcher file: {e}")

        logger.info("Designer manager stopped")

    async def launch_via_file(self, launcher_file: Path, wait_for_window: bool = True) -> bool:
        """
        Launch Designer using a downloaded launcher file

        This is called after browser automation has downloaded the JNLP or native launcher.

        Args:
            launcher_file: Path to downloaded launcher file (.jnlp or .exe)
            wait_for_window: Wait for Designer window to appear

        Returns:
            True if launch successful, False otherwise
        """
        logger.info(f"Launching Designer from file: {launcher_file}")

        if not launcher_file.exists():
            raise FileNotFoundError(f"Launcher file not found: {launcher_file}")

        self._launcher_file = launcher_file

        try:
            # Determine launch method based on file type and platform
            if launcher_file.suffix == ".jnlp":
                # JNLP file - use javaws
                await self._launch_jnlp(launcher_file)
            elif launcher_file.suffix == ".exe":
                # Windows executable
                await self._launch_exe(launcher_file)
            else:
                # Try to execute directly
                await self._launch_direct(launcher_file)

            # Wait for Designer window to appear
            if wait_for_window and self.platform_automation:
                logger.info("Waiting for Designer window to appear...")
                success = await asyncio.to_thread(
                    self.platform_automation.find_designer_window,
                    timeout=60
                )
                if not success:
                    logger.error("Designer window did not appear")
                    return False

            logger.info("Designer launched successfully")
            return True

        except Exception as e:
            logger.error(f"Error launching Designer: {e}")
            return False

    async def _launch_jnlp(self, jnlp_file: Path) -> None:
        """Launch Designer via JNLP file"""
        java_cmd = get_java_command()
        logger.info(f"Launching JNLP with: {java_cmd}")

        # Try javaws first (Java Web Start)
        try:
            self._process = await asyncio.create_subprocess_exec(
                "javaws", str(jnlp_file),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            logger.info("Designer process started with javaws")
        except FileNotFoundError:
            # Fall back to java -jar
            logger.warning("javaws not found, trying java -jar")
            self._process = await asyncio.create_subprocess_exec(
                java_cmd, "-jar", str(jnlp_file),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            logger.info("Designer process started with java -jar")

    async def _launch_exe(self, exe_file: Path) -> None:
        """Launch Designer via Windows executable"""
        logger.info(f"Launching executable: {exe_file}")
        self._process = await asyncio.create_subprocess_exec(
            str(exe_file),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        logger.info("Designer process started")

    async def _launch_direct(self, file_path: Path) -> None:
        """Launch Designer directly (generic)"""
        logger.info(f"Launching file directly: {file_path}")

        # Make executable (Linux)
        if self.system == "Linux":
            file_path.chmod(0o755)

        self._process = await asyncio.create_subprocess_exec(
            str(file_path),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        logger.info("Designer process started")

    async def login(self, username: str, password: str, timeout: int = 30) -> bool:
        """
        Perform Designer login

        Waits for login dialog to appear and fills credentials.

        Args:
            username: Designer username
            password: Designer password
            timeout: Maximum time to wait for login (seconds)

        Returns:
            True if login successful, False otherwise
        """
        if not self.platform_automation:
            raise RuntimeError("Platform automation not initialized")

        logger.info(f"Performing Designer login for user: {username}")

        # Wait for login dialog
        logger.info("Waiting for login dialog...")
        found = await asyncio.to_thread(
            self.platform_automation.find_login_dialog,
            timeout=timeout
        )
        if not found:
            logger.error("Login dialog did not appear")
            return False

        # Fill credentials
        logger.info("Filling login credentials...")
        success = await asyncio.to_thread(
            self.platform_automation.fill_login_credentials,
            username,
            password
        )
        if not success:
            logger.error("Failed to fill login credentials")
            return False

        # Wait for login to complete
        logger.info("Waiting for login to complete...")
        success = await asyncio.to_thread(
            self.platform_automation.wait_for_login_completion,
            timeout=timeout
        )
        if not success:
            logger.error("Login did not complete successfully")
            return False

        logger.info("Login successful")
        return True

    async def open_project(self, project_name: str, timeout: int = 30) -> bool:
        """
        Open specific project in Designer

        Args:
            project_name: Name of project to open
            timeout: Maximum time to wait (seconds)

        Returns:
            True if successful, False otherwise
        """
        if not self.platform_automation:
            raise RuntimeError("Platform automation not initialized")

        logger.info(f"Opening project: {project_name}")

        # Wait for project selector
        found = await asyncio.to_thread(
            self.platform_automation.find_project_selector,
            timeout=timeout
        )
        if not found:
            logger.error("Project selector did not appear")
            return False

        # Select project
        success = await asyncio.to_thread(
            self.platform_automation.select_project,
            project_name,
            timeout=timeout
        )
        if not success:
            logger.error(f"Failed to select project: {project_name}")
            return False

        logger.info(f"Project opened: {project_name}")
        return True

    async def close(self) -> bool:
        """
        Close Designer application

        Returns:
            True if successful, False otherwise
        """
        if not self.platform_automation:
            raise RuntimeError("Platform automation not initialized")

        logger.info("Closing Designer...")
        success = await asyncio.to_thread(self.platform_automation.close_designer)
        return success

    async def screenshot(self, name: str) -> Path:
        """
        Take screenshot of Designer window

        Args:
            name: Screenshot name (without extension)

        Returns:
            Path to screenshot file
        """
        if not self.platform_automation:
            raise RuntimeError("Platform automation not initialized")

        screenshot_path = self.screenshots_dir / f"{name}.png"
        logger.info(f"Taking Designer screenshot: {screenshot_path}")

        success = await asyncio.to_thread(
            self.platform_automation.take_screenshot,
            str(screenshot_path)
        )

        if not success:
            raise RuntimeError(f"Failed to capture screenshot: {name}")

        return screenshot_path

    async def wait_for_window(self, timeout: int = 30) -> bool:
        """
        Wait for Designer window to appear

        Args:
            timeout: Maximum time to wait (seconds)

        Returns:
            True if window found, False otherwise
        """
        if not self.platform_automation:
            raise RuntimeError("Platform automation not initialized")

        return await asyncio.to_thread(
            self.platform_automation.find_designer_window,
            timeout=timeout
        )
