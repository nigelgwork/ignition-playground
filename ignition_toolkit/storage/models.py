"""
SQLAlchemy database models
"""

from datetime import UTC, datetime

from sqlalchemy import JSON, Boolean, Column, DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


def utcnow():
    """Return current UTC time"""
    return datetime.now(UTC)


class ExecutionModel(Base):
    """
    Stores playbook execution history

    Tracks each playbook run with timestamps, status, and results.
    """

    __tablename__ = "executions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    execution_id = Column(
        String(255), unique=True, nullable=False, index=True
    )  # UUID from frontend
    playbook_name = Column(String(255), nullable=False)
    playbook_version = Column(String(50), nullable=True)
    status = Column(String(50), nullable=False)  # pending, running, completed, failed, paused
    started_at = Column(DateTime, default=utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)
    config_data = Column(JSON, nullable=True)  # Runtime parameter values
    execution_metadata = Column(JSON, nullable=True)  # Additional execution metadata

    # Relationships
    step_results = relationship(
        "StepResultModel", back_populates="execution", cascade="all, delete-orphan"
    )

    # Indexes for performance
    __table_args__ = (
        Index("idx_executions_status", "status"),
        Index("idx_executions_started_at", "started_at"),
        Index("idx_executions_playbook_name", "playbook_name"),
        Index(
            "idx_executions_status_started", "status", "started_at"
        ),  # Composite index for filtered queries
    )

    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "execution_id": self.execution_id,
            "playbook_name": self.playbook_name,
            "playbook_version": self.playbook_version,
            "status": self.status,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "error_message": self.error_message,
            "config_data": self.config_data,
            "execution_metadata": self.execution_metadata,
            "step_results": [step.to_dict() for step in self.step_results],
        }


class StepResultModel(Base):
    """
    Stores individual step execution results within a playbook run
    """

    __tablename__ = "step_results"

    id = Column(Integer, primary_key=True, autoincrement=True)
    execution_id = Column(Integer, ForeignKey("executions.id"), nullable=False)
    step_id = Column(String(255), nullable=False)
    step_name = Column(String(255), nullable=False)
    status = Column(String(50), nullable=False)  # pending, running, completed, failed, skipped
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    output = Column(JSON, nullable=True)  # Step output data
    error_message = Column(Text, nullable=True)
    artifacts = Column(JSON, nullable=True)  # Screenshot paths, log files, etc.

    # Relationships
    execution = relationship("ExecutionModel", back_populates="step_results")

    # Indexes for performance
    __table_args__ = (
        Index("idx_step_results_execution_id", "execution_id"),
        Index("idx_step_results_status", "status"),
    )

    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "execution_id": self.execution_id,
            "step_id": self.step_id,
            "step_name": self.step_name,
            "status": self.status,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "output": self.output,
            "error_message": self.error_message,
            "artifacts": self.artifacts,
        }


class PlaybookConfigModel(Base):
    """
    Stores saved playbook configurations

    Allows users to save parameter sets for reuse (e.g., "Production Gateway" config)
    """

    __tablename__ = "playbook_configs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    playbook_name = Column(String(255), nullable=False)
    config_name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    parameters = Column(JSON, nullable=False)  # Saved parameter values
    created_at = Column(DateTime, default=utcnow, nullable=False)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow, nullable=False)

    # Indexes for performance
    __table_args__ = (
        Index("idx_playbook_configs_playbook_name", "playbook_name"),
        Index("idx_playbook_configs_config_name", "config_name"),
    )

    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "playbook_name": self.playbook_name,
            "config_name": self.config_name,
            "description": self.description,
            "parameters": self.parameters,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class AISettingsModel(Base):
    """
    Stores AI provider settings for the AI assist feature

    Supports multiple AI providers (OpenAI, Anthropic, Local LLMs)
    Now supports multiple credential entries with unique names
    """

    __tablename__ = "ai_settings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, unique=True)  # Unique credential name
    provider = Column(String(50), nullable=False)  # "openai", "anthropic", "gemini", "local"
    api_key = Column(Text, nullable=True)  # Encrypted API key
    api_base_url = Column(
        String(500), nullable=True
    )  # For local LLMs (e.g., http://localhost:1234/v1)
    model_name = Column(String(100), nullable=True)  # e.g., "gpt-4", "claude-3-sonnet", "llama-3"
    enabled = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, default=utcnow, nullable=False)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow, nullable=False)

    def to_dict(self) -> dict:
        """Convert to dictionary (excluding sensitive data)"""
        return {
            "id": self.id,
            "name": self.name,
            "provider": self.provider,
            "api_base_url": self.api_base_url,
            "model_name": self.model_name,
            "enabled": self.enabled,
            "has_api_key": bool(self.api_key),  # Don't expose the actual key
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class ScheduledPlaybookModel(Base):
    """
    Stores scheduled playbook configurations

    Supports cron-like schedules for automated playbook execution
    """

    __tablename__ = "scheduled_playbooks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)  # User-friendly schedule name
    playbook_path = Column(String(500), nullable=False)  # Path to playbook YAML
    schedule_type = Column(
        String(50), nullable=False
    )  # "cron", "interval", "daily", "weekly", "monthly"
    schedule_config = Column(
        JSON, nullable=False
    )  # Schedule configuration (cron expression, interval, etc.)
    parameters = Column(JSON, nullable=True)  # Playbook parameters
    gateway_url = Column(String(500), nullable=True)  # Gateway URL for execution
    credential_name = Column(String(255), nullable=True)  # Credential to use
    enabled = Column(Boolean, nullable=False, default=True)
    last_run_at = Column(DateTime, nullable=True)  # Last execution timestamp
    next_run_at = Column(DateTime, nullable=True)  # Next scheduled execution
    created_at = Column(DateTime, default=utcnow, nullable=False)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow, nullable=False)

    # Indexes for performance
    __table_args__ = (
        Index("idx_scheduled_playbooks_enabled", "enabled"),
        Index("idx_scheduled_playbooks_next_run", "next_run_at"),
    )

    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "name": self.name,
            "playbook_path": self.playbook_path,
            "schedule_type": self.schedule_type,
            "schedule_config": self.schedule_config,
            "parameters": self.parameters,
            "gateway_url": self.gateway_url,
            "credential_name": self.credential_name,
            "enabled": self.enabled,
            "last_run_at": self.last_run_at.isoformat() if self.last_run_at else None,
            "next_run_at": self.next_run_at.isoformat() if self.next_run_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class FATReportModel(Base):
    """
    Stores Factory Acceptance Test (FAT) reports

    Tracks FAT test execution results, component tests, and visual analysis.
    """

    __tablename__ = "fat_reports"

    id = Column(Integer, primary_key=True, autoincrement=True)
    execution_id = Column(Integer, ForeignKey("executions.id"), nullable=True)
    report_name = Column(String(255), nullable=False)
    page_url = Column(String(500), nullable=True)
    total_components = Column(Integer, nullable=False, default=0)
    passed_tests = Column(Integer, nullable=False, default=0)
    failed_tests = Column(Integer, nullable=False, default=0)
    skipped_tests = Column(Integer, nullable=False, default=0)
    visual_issues = Column(Integer, nullable=False, default=0)
    report_html = Column(Text, nullable=True)  # Full HTML report
    report_metadata = Column(JSON, nullable=True)  # Additional metadata
    created_at = Column(DateTime, default=utcnow, nullable=False)

    # Relationships
    component_tests = relationship(
        "FATComponentTestModel", back_populates="report", cascade="all, delete-orphan"
    )

    # Indexes for performance
    __table_args__ = (
        Index("idx_fat_reports_execution_id", "execution_id"),
        Index("idx_fat_reports_created_at", "created_at"),
    )

    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "execution_id": self.execution_id,
            "report_name": self.report_name,
            "page_url": self.page_url,
            "total_components": self.total_components,
            "passed_tests": self.passed_tests,
            "failed_tests": self.failed_tests,
            "skipped_tests": self.skipped_tests,
            "visual_issues": self.visual_issues,
            "report_metadata": self.report_metadata,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "component_tests": [test.to_dict() for test in self.component_tests],
        }


class FATComponentTestModel(Base):
    """
    Stores individual component test results within a FAT report
    """

    __tablename__ = "fat_component_tests"

    id = Column(Integer, primary_key=True, autoincrement=True)
    report_id = Column(Integer, ForeignKey("fat_reports.id"), nullable=False)
    component_id = Column(String(255), nullable=False)  # DOM element ID
    component_type = Column(String(100), nullable=True)  # button, input, etc.
    component_label = Column(String(500), nullable=True)
    test_action = Column(String(100), nullable=False)  # click, fill, verify
    expected_behavior = Column(Text, nullable=True)
    actual_behavior = Column(Text, nullable=True)
    status = Column(String(50), nullable=False)  # passed, failed, skipped
    screenshot_path = Column(String(500), nullable=True)
    error_message = Column(Text, nullable=True)
    duration_ms = Column(Integer, nullable=True)
    tested_at = Column(DateTime, default=utcnow, nullable=False)

    # Relationships
    report = relationship("FATReportModel", back_populates="component_tests")

    # Indexes for performance
    __table_args__ = (
        Index("idx_fat_component_tests_report_id", "report_id"),
        Index("idx_fat_component_tests_status", "status"),
    )

    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "report_id": self.report_id,
            "component_id": self.component_id,
            "component_type": self.component_type,
            "component_label": self.component_label,
            "test_action": self.test_action,
            "expected_behavior": self.expected_behavior,
            "actual_behavior": self.actual_behavior,
            "status": self.status,
            "screenshot_path": self.screenshot_path,
            "error_message": self.error_message,
            "duration_ms": self.duration_ms,
            "tested_at": self.tested_at.isoformat() if self.tested_at else None,
        }
