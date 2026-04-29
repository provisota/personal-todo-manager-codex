"""Use case-insensitive list names

Revision ID: 0002_case_insensitive_list_names
Revises: 0001_initial
Create Date: 2026-04-29
"""

from alembic import op
import sqlalchemy as sa

revision = "0002_case_insensitive_list_names"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_index("ix_project_lists_user_lower_name", table_name="project_lists")
    op.create_index(
        "ix_project_lists_user_lower_name",
        "project_lists",
        ["user_id", sa.text("lower(name)")],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("ix_project_lists_user_lower_name", table_name="project_lists")
    op.create_index(
        "ix_project_lists_user_lower_name",
        "project_lists",
        ["user_id", "name"],
        unique=True,
    )
