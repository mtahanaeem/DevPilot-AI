"""Add owner column to repositories.

Revision ID: 002
Revises: 001
Create Date: 2026-07-15
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("repositories", sa.Column("owner", sa.String(255), nullable=False, server_default=sa.text("''")))


def downgrade() -> None:
    op.drop_column("repositories", "owner")
