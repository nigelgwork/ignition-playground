"""
Configuration management

Centralized settings using Pydantic BaseSettings for type-safe configuration
with environment variable support.
"""

import os
from pathlib import Path
from typing import List

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Application settings with environment variable support

    Settings can be overridden via environment variables:
    - DATABASE_PATH=/custom/path/db.sqlite
    - API_PORT=8000
    - ENVIRONMENT=development
    """

    # Database
    database_path: Path = Path("./data/toolkit.db")

    # Credentials
    vault_path: Path = Path.home() / ".ignition-toolkit" / "credentials.vault"

    # API
    api_host: str = "0.0.0.0"
    api_port: int = 5000
    api_workers: int = 1
    cors_origins: List[str] = ["*"]
    websocket_api_key: str = "dev-key-change-in-production"

    # Environment
    environment: str = "production"
    log_level: str = "INFO"
    log_format: str = "json"

    # Playwright browser automation
    playwright_headless: bool = True
    playwright_browser: str = "chromium"
    playwright_timeout: int = 30000

    # Feature flags
    enable_ai: bool = False
    enable_browser_recording: bool = True
    enable_screenshot_streaming: bool = True

    # Execution
    max_concurrent_executions: int = 10
    execution_timeout_seconds: int = 3600  # 1 hour

    # Frontend
    frontend_dir: Path = Path("frontend/dist")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Singleton pattern for settings
_settings: Settings | None = None


def get_settings() -> Settings:
    """
    Get application settings (singleton)

    Returns:
        Settings instance
    """
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


def is_dev_mode() -> bool:
    """
    Check if running in development mode

    Returns:
        bool: True if environment is development
    """
    settings = get_settings()
    return settings.environment.lower() in ("development", "dev")
