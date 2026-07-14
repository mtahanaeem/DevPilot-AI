import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.database.models.base import Base


class BookmarkedIssueModel(Base):
    __tablename__ = "bookmarked_issues"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    github_issue_id: Mapped[int] = mapped_column(nullable=False)
    repo_owner: Mapped[str] = mapped_column(String(255), nullable=False)
    repo_name: Mapped[str] = mapped_column(String(255), nullable=False)
    issue_title: Mapped[str] = mapped_column(String(500), nullable=False)
    issue_url: Mapped[str] = mapped_column(String(1000), nullable=False)
    labels: Mapped[str] = mapped_column(String(500), default="")
    score: Mapped[float | None] = mapped_column(nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="bookmarked")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    user = relationship("UserModel", back_populates="bookmarked_issues")
