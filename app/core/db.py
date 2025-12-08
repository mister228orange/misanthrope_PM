# src/misanthrope_pm/core/database.py
from datetime import datetime
from typing import Optional, List
from pathlib import Path
from enum import Enum

from sqlmodel import SQLModel, Field, create_engine, Session, select
from pydantic import BaseModel


# --- Database Engine Setup ---
def get_engine(db_path: Path):
    """Create a SQLAlchemy engine for a SQLite database file."""
    sqlite_url = f"sqlite:///{db_path.absolute()}"
    # echo=True logs all SQL statements (useful for debugging)
    return create_engine(sqlite_url, echo=False)


# --- Enums (for consistent data) ---
class TaskCategory(str, Enum):
    BUG = "bug"
    FEATURE = "feature"
    REFACTOR = "refactor"
    INFRA = "infrastructure"
    DOCS = "documentation"
    TEST = "test"


# --- SQLModel Table Definitions ---
class ProjectDB(SQLModel, table=True):
    """Stores metadata for each tracked project."""
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True, unique=True)  # Project identifier
    repo_path: str  # Path to the git repository
    data_path: str  # Path where this project's data is stored
    description: Optional[str] = None
    added_at: datetime = Field(default_factory=datetime.utcnow)
    last_analyzed_at: Optional[datetime] = None


class ContributorDB(SQLModel, table=True):
    """Represents a git contributor across potentially many projects."""
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)  # Git author name
    email: str = Field(index=True)  # Git author email
    first_seen: datetime
    last_seen: datetime


class TaskDB(SQLModel, table=True):
    """A completed development task."""
    id: Optional[int] = Field(default=None, primary_key=True)
    project_id: int = Field(foreign_key="projectdb.id")
    external_id: Optional[str] = Field(index=True)  # e.g., JIRA ticket ID

    title: str
    description: Optional[str] = None
    category: TaskCategory

    # Time tracking
    estimated_hours: Optional[float] = None
    actual_hours: Optional[float] = None

    # Dates
    created_date: Optional[datetime] = None
    started_date: Optional[datetime] = None
    completed_date: datetime = Field(index=True)

    # Metadata
    complexity_score: Optional[float] = None  # 1.0 (easy) to 5.0 (hard)
    prediction_confidence: Optional[float] = None  # For ML predictions

    # Relationships (these are "conceptual" with SQLModel)
    # project: ProjectDB = Relationship(back_populates="tasks") # If using relationships


class CommitDB(SQLModel, table=True):
    """A git commit with detailed metrics."""
    id: Optional[int] = Field(default=None, primary_key=True)
    project_id: int = Field(foreign_key="projectdb.id")
    contributor_id: int = Field(foreign_key="contributordb.id")

    # Git metadata
    hash: str = Field(index=True, unique=True)
    author_date: datetime = Field(index=True)
    commit_date: Optional[datetime] = None

    # Commit content
    message: str
    title: str = Field(index=True)

    # Metrics
    insertions: int = Field(default=0)
    deletions: int = Field(default=0)
    files_changed: int = Field(default=0)

    # Tags/classification
    is_merge: bool = Field(default=False)
    tags: Optional[str] = None  # JSON string or comma-separated

    # Derived fields for fast querying
    day: datetime = Field(index=True)  # Date-only part of author_date


class DailyStatsDB(SQLModel, table=True):
    """Pre-aggregated daily productivity metrics."""
    id: Optional[int] = Field(default=None, primary_key=True)
    project_id: int = Field(foreign_key="projectdb.id")
    date: datetime = Field(index=True)

    # Aggregated metrics
    commits_count: int = Field(default=0)
    insertions_total: int = Field(default=0)
    deletions_total: int = Field(default=0)
    tasks_completed: int = Field(default=0)

    # Calculated fields
    net_changes: int = Field(default=0)  # insertions - deletions
    avg_commit_size: float = Field(default=0.0)

    class Config:
        table_name = "daily_stats"  # Explicit table name


class TaskPredictionDB(SQLModel, table=True):
    """Stored predictions for task estimates."""
    id: Optional[int] = Field(default=None, primary_key=True)
    project_id: int = Field(foreign_key="projectdb.id")

    # Task details
    task_text: str
    predicted_category: TaskCategory

    # Predictions
    estimated_hours_predicted: float
    estimated_hours_actual: Optional[float] = None  # For model training
    complexity_score: float  # 1.0 to 5.0
    confidence: float  # 0.0 to 1.0

    # Metadata
    predicted_at: datetime = Field(default_factory=datetime.utcnow)
    model_version: str


# --- Pydantic Models (for API/validation) ---
class ProjectCreate(BaseModel):
    """Schema for creating a new project."""
    name: str
    repo_path: str
    description: Optional[str] = None


class ContributorStats(BaseModel):
    """Schema for contributor statistics."""
    name: str
    email: str
    commit_count: int
    total_insertions: int
    total_deletions: int
    first_commit: datetime
    last_commit: datetime
    active_days: int
    avg_daily_commits: float
    avg_daily_commits: float


# --- Database Initialization ---
def create_tables(engine):
    """Create all tables defined in SQLModel metadata."""
    SQLModel.metadata.create_all(engine)