import uuid
from datetime import datetime

from sqlalchemy import String, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.database.models.base import Base


class SocialPostModel(Base):
    __tablename__ = "social_posts"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    repository_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("repositories.id"), nullable=False
    )
    platform: Mapped[str] = mapped_column(String(20), nullable=False)  # linkedin | twitter
    content: Mapped[str] = mapped_column(nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="draft")  # draft | published
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    repository = relationship("RepositoryModel", back_populates="social_posts")
