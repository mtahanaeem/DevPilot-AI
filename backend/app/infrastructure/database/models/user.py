import uuid
from datetime import datetime

from sqlalchemy import String, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.database.models.base import Base


class UserModel(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    github_username: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    oauth_token: Mapped[str | None] = mapped_column(String(512), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    repositories = relationship("RepositoryModel", back_populates="user", cascade="all, delete-orphan")
    resumes = relationship("ResumeModel", back_populates="user", cascade="all, delete-orphan")
    job_descriptions = relationship("JobDescriptionModel", back_populates="user", cascade="all, delete-orphan")
    skill_gap_reports = relationship("SkillGapReportModel", back_populates="user", cascade="all, delete-orphan")
    learning_plans = relationship("LearningPlanModel", back_populates="user", cascade="all, delete-orphan")
    interview_sessions = relationship("InterviewSessionModel", back_populates="user", cascade="all, delete-orphan")
    bookmarked_issues = relationship("BookmarkedIssueModel", back_populates="user", cascade="all, delete-orphan")
    notifications = relationship("NotificationModel", back_populates="user", cascade="all, delete-orphan")
    analytics_snapshots = relationship("AnalyticsSnapshotModel", back_populates="user", cascade="all, delete-orphan")
