"""Add DB defaults for email_queue trigger inserts."""

from alembic import op

revision = "20260517000200"
down_revision = "20260517000100"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        ALTER TABLE email_queue
        ALTER COLUMN status SET DEFAULT 'pending',
        ALTER COLUMN created_at SET DEFAULT CURRENT_TIMESTAMP;
        """
    )

    op.execute(
        """
        UPDATE email_queue
        SET created_at = CURRENT_TIMESTAMP
        WHERE created_at IS NULL;
        """
    )

    op.execute(
        """
        CREATE OR REPLACE FUNCTION fn_enqueue_payment_success_email()
        RETURNS TRIGGER AS $$
        DECLARE customer_email TEXT;
        DECLARE customer_id INTEGER;
        BEGIN
          IF NEW.status = 'Success'
             AND (TG_OP = 'INSERT' OR OLD.status IS DISTINCT FROM NEW.status) THEN
            SELECT u.id, u.email
            INTO customer_id, customer_email
            FROM orders o
            JOIN users u ON u.id = o.user_id
            WHERE o.id = NEW.order_id;

            INSERT INTO email_queue (
              user_id,
              order_id,
              payment_id,
              recipient_email,
              subject,
              body,
              status,
              created_at
            )
            VALUES (
              customer_id,
              NEW.order_id,
              NEW.id,
              customer_email,
              'Payment confirmation',
              CONCAT(
                'Your payment for order #',
                NEW.order_id::text,
                ' was successful. Reference: ',
                COALESCE(NEW.simulated_ref, 'N/A')
              ),
              'pending',
              CURRENT_TIMESTAMP
            )
            ON CONFLICT (payment_id) DO NOTHING;
          END IF;
          RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
        """
    )


def downgrade() -> None:
    op.execute(
        """
        CREATE OR REPLACE FUNCTION fn_enqueue_payment_success_email()
        RETURNS TRIGGER AS $$
        DECLARE customer_email TEXT;
        DECLARE customer_id INTEGER;
        BEGIN
          IF NEW.status = 'Success'
             AND (TG_OP = 'INSERT' OR OLD.status IS DISTINCT FROM NEW.status) THEN
            SELECT u.id, u.email
            INTO customer_id, customer_email
            FROM orders o
            JOIN users u ON u.id = o.user_id
            WHERE o.id = NEW.order_id;

            INSERT INTO email_queue (
              user_id,
              order_id,
              payment_id,
              recipient_email,
              subject,
              body,
              status
            )
            VALUES (
              customer_id,
              NEW.order_id,
              NEW.id,
              customer_email,
              'Payment confirmation',
              CONCAT(
                'Your payment for order #',
                NEW.order_id::text,
                ' was successful. Reference: ',
                COALESCE(NEW.simulated_ref, 'N/A')
              ),
              'pending'
            )
            ON CONFLICT (payment_id) DO NOTHING;
          END IF;
          RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
        """
    )

    op.execute(
        """
        ALTER TABLE email_queue
        ALTER COLUMN status DROP DEFAULT,
        ALTER COLUMN created_at DROP DEFAULT;
        """
    )
