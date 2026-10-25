"""Add Razorpay payment identifiers."""

from alembic import op
import sqlalchemy as sa

revision = "ef8f8270a82f"
down_revision = "20260517000300"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "payments",
        sa.Column("razorpay_order_id", sa.String(length=100), nullable=True),
    )

    op.add_column(
        "payments",
        sa.Column("razorpay_payment_id", sa.String(length=100), nullable=True),
    )

    op.create_index(
        "ix_payments_razorpay_order_id",
        "payments",
        ["razorpay_order_id"],
        unique=True,
    )

    op.create_index(
        "ix_payments_razorpay_payment_id",
        "payments",
        ["razorpay_payment_id"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_payments_razorpay_payment_id",
        table_name="payments",
    )
    op.drop_index(
        "ix_payments_razorpay_order_id",
        table_name="payments",
    )

    op.drop_column("payments", "razorpay_payment_id")
    op.drop_column("payments", "razorpay_order_id")