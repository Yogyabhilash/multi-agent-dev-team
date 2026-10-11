
"""add task workflow and approvals

Revision ID: 0314a98a9fc7
Revises: fcaa232f487d
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# Revision identifiers used by Alembic.
revision: str = "0314a98a9fc7"
down_revision: Union[str, Sequence[str], None] = "fcaa232f487d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add task workflow fields and approval requests."""

    # Add columns with server defaults so existing task rows remain valid.
    op.add_column(
        "tasks",
        sa.Column(
            "priority",
            sa.Integer(),
            server_default="3",
            nullable=False,
        ),
    )

    op.add_column(
        "tasks",
        sa.Column(
            "dependencies",
            sa.JSON(),
            server_default=sa.text("'[]'"),
            nullable=False,
        ),
    )

    op.add_column(
        "tasks",
        sa.Column("result", sa.Text(), nullable=True),
    )

    op.add_column(
        "tasks",
        sa.Column("error_message", sa.Text(), nullable=True),
    )

    op.add_column(
        "tasks",
        sa.Column(
            "approval_status",
            sa.String(length=30),
            server_default="not_required",
            nullable=False,
        ),
    )

    op.add_column(
        "tasks",
        sa.Column(
            "started_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )

    op.add_column(
        "tasks",
        sa.Column(
            "completed_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )


def downgrade() -> None:
    """Remove the task workflow fields and approval requests table."""

    # Remove the new task columns in reverse order.
    op.drop_column("tasks", "completed_at")
    op.drop_column("tasks", "started_at")
    op.drop_column("tasks", "approval_status")
    op.drop_column("tasks", "error_message")
    op.drop_column("tasks", "result")
    op.drop_column("tasks", "dependencies")
    op.drop_column("tasks", "priority")
