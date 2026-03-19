"""Initial migration: create todos table

Revision ID: 0001_initial
Revises:
Create Date: 2025-03-19
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.exc import ProgrammingError

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create priority enum safely — skip if it already exists
    conn = op.get_bind()
    try:
        conn.execute(sa.text("CREATE TYPE priority AS ENUM ('low', 'medium', 'high')"))
    except ProgrammingError:
        conn.execute(sa.text("ROLLBACK"))

    # Create todos table — skip if it already exists
    try:
        op.create_table(
            "todos",
            sa.Column("id", sa.Integer(), primary_key=True, index=True),
            sa.Column("title", sa.String(255), nullable=False, index=True),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("due_date", sa.DateTime(), nullable=True),
            sa.Column(
                "priority",
                sa.Enum("low", "medium", "high", name="priority", create_type=False),
                nullable=False,
                server_default="medium",
            ),
            sa.Column("is_completed", sa.Boolean(), nullable=False, server_default="false"),
            sa.Column("tags", JSON(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        )
    except ProgrammingError:
        pass


def downgrade() -> None:
    op.drop_table("todos")
    op.execute(sa.text("DROP TYPE IF EXISTS priority"))
