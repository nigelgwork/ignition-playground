"""
SQLAlchemy database models
"""

from datetime import datetime, UTC
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, JSON, Index
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
    execution_id = Column(String(255), unique=True, nullable=False, index=True)  # UUID from frontend
    playbook_name = Column(String(255), nullable=False)
    playbook_version = Column(String(50), nullable=True)
    status = Column(String(50), nullable=False)  # pending, running, completed, failed, paused
    started_at = Column(DateTime, default=utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)
    config_data = Column(JSON, nullable=True)  # Runtime parameter values
    execution_metadata = Column(JSON, nullable=True)  # Additional execution metadata

    # Relationships
    step_results = relationship("StepResultModel", back_populates="execution", cascade="all, delete-orphan")

    # Indexes for performance
    __table_args__ = (
        Index('idx_executions_status', 'status'),
        Index('idx_executions_started_at', 'started_at'),
        Index('idx_executions_playbook_name', 'playbook_name'),
        Index('idx_executions_status_started', 'status', 'started_at'),  # Composite index for filtered queries
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
        Index('idx_step_results_execution_id', 'execution_id'),
        Index('idx_step_results_status', 'status'),
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
        Index('idx_playbook_configs_playbook_name', 'playbook_name'),
        Index('idx_playbook_configs_config_name', 'config_name'),
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
