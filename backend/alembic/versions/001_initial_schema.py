"""Initial schema for DevPilot AI.

Revision ID: 001
Revises:
Create Date: 2026-07-14
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("github_username", sa.String(255), unique=True, nullable=False),
        sa.Column("oauth_token", sa.String(512), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "repositories",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("github_repo_id", sa.BigInteger(), unique=True, nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.String(1024), nullable=True),
        sa.Column("language_stats", JSONB(), nullable=True, server_default=sa.text("'{}'::jsonb")),
        sa.Column("stars", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("forks", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("last_commit_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_stale", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "generated_documents",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("repository_id", UUID(as_uuid=True), sa.ForeignKey("repositories.id"), nullable=False),
        sa.Column("type", sa.String(50), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default=sa.text("'draft'")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "resumes",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("raw_text", sa.Text(), nullable=False),
        sa.Column("file_path", sa.String(1024), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "job_descriptions",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("raw_text", sa.Text(), nullable=False),
        sa.Column("source_url", sa.String(2048), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "skill_gap_reports",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("job_description_id", UUID(as_uuid=True), sa.ForeignKey("job_descriptions.id"), nullable=False),
        sa.Column("gaps", JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "learning_plans",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("items", JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "interview_sessions",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("job_description_id", UUID(as_uuid=True), sa.ForeignKey("job_descriptions.id"), nullable=False),
        sa.Column("questions", JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("answers", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "social_posts",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("repository_id", UUID(as_uuid=True), sa.ForeignKey("repositories.id"), nullable=False),
        sa.Column("platform", sa.String(20), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default=sa.text("'draft'")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "notifications",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("event_type", sa.String(50), nullable=False),
        sa.Column("channel", sa.String(20), nullable=False),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default=sa.text("'pending'")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "analytics_snapshots",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("period", sa.String(20), nullable=False),
        sa.Column("metrics", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Indexes
    op.create_index("ix_repositories_user_id", "repositories", ["user_id"])
    op.create_index("ix_repositories_github_repo_id", "repositories", ["github_repo_id"])
    op.create_index("ix_documents_repository_id", "generated_documents", ["repository_id"])
    op.create_index("ix_documents_status", "generated_documents", ["status"])
    op.create_index("ix_resumes_user_id", "resumes", ["user_id"])
    op.create_index("ix_jobs_user_id", "job_descriptions", ["user_id"])
    op.create_index("ix_notifications_user_id", "notifications", ["user_id"])
    op.create_index("ix_notifications_status", "notifications", ["status"])
    op.create_index("ix_analytics_user_id", "analytics_snapshots", ["user_id"])
    op.create_index("ix_analytics_period", "analytics_snapshots", ["period"])


def downgrade() -> None:
    op.drop_table("analytics_snapshots")
    op.drop_table("notifications")
    op.drop_table("social_posts")
    op.drop_table("interview_sessions")
    op.drop_table("learning_plans")
    op.drop_table("skill_gap_reports")
    op.drop_table("job_descriptions")
    op.drop_table("resumes")
    op.drop_table("generated_documents")
    op.drop_table("repositories")
    op.drop_table("users")
