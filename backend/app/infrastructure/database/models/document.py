import uuid
from datetime import datetime

from sqlalchemy import String, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.database.models.base import Base


class GeneratedDocumentModel(Base):
    __tablename__ = "generated_documents"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    repository_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("repositories.id"), nullable=False
    )
    type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # readme | docs | contributing | architecture
    content: Mapped[str] = mapped_column(nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), default="draft"
    )  # draft | approved | committed
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    repository = relationship("RepositoryModel", back_populates="documents")
