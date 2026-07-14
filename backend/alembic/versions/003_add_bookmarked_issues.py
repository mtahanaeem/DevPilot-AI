"""add bookmarked_issues table

Revision ID: 003
Revises: 002
Create Date: 2026-07-14

"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision: str = "003"
down_revision: str | None = "002"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    op.create_table(
        "bookmarked_issues",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("github_issue_id", sa.Integer(), nullable=False),
        sa.Column("repo_owner", sa.String(255), nullable=False),
        sa.Column("repo_name", sa.String(255), nullable=False),
        sa.Column("issue_title", sa.String(500), nullable=False),
        sa.Column("issue_url", sa.String(1000), nullable=False),
        sa.Column("labels", sa.String(500), server_default=""),
        sa.Column("score", sa.Float(), nullable=True),
        sa.Column("status", sa.String(20), server_default="bookmarked"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("bookmarked_issues")
