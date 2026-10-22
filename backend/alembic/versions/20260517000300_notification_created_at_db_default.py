"""Add DB default for notifications.created_at."""

from alembic import op

revision = "20260517000300"
down_revision = "20260517000200"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        ALTER TABLE notifications
        ALTER COLUMN created_at SET DEFAULT CURRENT_TIMESTAMP;
        """
    )


def downgrade() -> None:
    op.execute(
        """
        ALTER TABLE notifications
        ALTER COLUMN created_at DROP DEFAULT;
        """
    )
