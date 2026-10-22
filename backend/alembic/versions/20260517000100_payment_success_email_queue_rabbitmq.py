"""Add payment success email queue trigger support."""

from alembic import op

revision = "20260517000100"
down_revision = "20250510120000"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    from app.database.session import Base

    Base.metadata.create_all(bind=bind, tables=[Base.metadata.tables["email_queue"]])

    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_email_queue_status_created
        ON email_queue (status, created_at DESC);
        """
    )

    op.execute(
        """
        UPDATE payments
        SET status = CASE
          WHEN status = 'completed' THEN 'Success'
          WHEN status = 'pending' THEN 'Pending'
          WHEN status = 'processing' THEN 'Processing'
          WHEN status = 'failed' THEN 'Failed'
          ELSE status
        END;
        """
    )

    op.execute(
        """
        CREATE OR REPLACE FUNCTION fn_payment_confirms_order()
        RETURNS TRIGGER AS $$
        BEGIN
          IF NEW.status = 'Success' THEN
             IF TG_OP = 'INSERT' THEN
               UPDATE orders SET status = 'confirmed' WHERE id = NEW.order_id AND status = 'pending';
             ELSIF TG_OP = 'UPDATE' AND (OLD.status IS DISTINCT FROM NEW.status)
                  AND NEW.status = 'Success' THEN
               UPDATE orders SET status = 'confirmed' WHERE id = NEW.order_id;
             END IF;
          END IF;
          RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;

        DROP TRIGGER IF EXISTS trg_payment_insert_completed ON payments;
        CREATE TRIGGER trg_payment_insert_completed
        AFTER INSERT ON payments
        FOR EACH ROW
        EXECUTE PROCEDURE fn_payment_confirms_order();

        DROP TRIGGER IF EXISTS trg_payment_update_completed ON payments;
        CREATE TRIGGER trg_payment_update_completed
        AFTER UPDATE OF status ON payments
        FOR EACH ROW
        EXECUTE PROCEDURE fn_payment_confirms_order();
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

        DROP TRIGGER IF EXISTS trg_payment_success_email_queue_insert ON payments;
        CREATE TRIGGER trg_payment_success_email_queue_insert
        AFTER INSERT ON payments
        FOR EACH ROW
        EXECUTE PROCEDURE fn_enqueue_payment_success_email();

        DROP TRIGGER IF EXISTS trg_payment_success_email_queue_update ON payments;
        CREATE TRIGGER trg_payment_success_email_queue_update
        AFTER UPDATE OF status ON payments
        FOR EACH ROW
        EXECUTE PROCEDURE fn_enqueue_payment_success_email();
        """
    )

    op.execute(
        """
        CREATE OR REPLACE VIEW v_top_selling_products AS
        SELECT
          p.id AS product_id,
          p.name,
          SUM(oi.quantity)::BIGINT AS units_sold,
          SUM(oi.quantity * oi.unit_price)::NUMERIC(14,2) AS revenue
        FROM order_items oi
        JOIN orders o ON o.id = oi.order_id
        JOIN payments pay ON pay.order_id = o.id AND pay.status = 'Success'
        JOIN products p ON p.id = oi.product_id
        GROUP BY p.id, p.name
        ORDER BY units_sold DESC;

        CREATE OR REPLACE VIEW v_monthly_sales AS
        SELECT
          date_trunc('month', o.created_at) AS month,
          COALESCE(SUM(o.total), 0)::NUMERIC(14,2) AS total_sales,
          COUNT(DISTINCT o.id)::BIGINT AS order_count
        FROM orders o
        JOIN payments p ON p.order_id = o.id AND p.status = 'Success'
        GROUP BY date_trunc('month', o.created_at)
        ORDER BY month;

        CREATE OR REPLACE VIEW v_active_customers AS
        SELECT
          u.id AS user_id,
          u.email,
          COUNT(o.id) AS order_count,
          COALESCE(SUM(o.total), 0)::NUMERIC(14,2) AS lifetime_value
        FROM users u
        JOIN orders o ON o.user_id = u.id
        JOIN payments p ON p.order_id = o.id AND p.status = 'Success'
        GROUP BY u.id, u.email
        HAVING COUNT(o.id) >= 1;
        """
    )


def downgrade() -> None:
    op.execute(
        """
        DROP TRIGGER IF EXISTS trg_payment_success_email_queue_update ON payments;
        DROP TRIGGER IF EXISTS trg_payment_success_email_queue_insert ON payments;
        DROP FUNCTION IF EXISTS fn_enqueue_payment_success_email();
        """
    )

    op.execute(
        """
        CREATE OR REPLACE FUNCTION fn_payment_confirms_order()
        RETURNS TRIGGER AS $$
        BEGIN
          IF NEW.status = 'completed' THEN
             IF TG_OP = 'INSERT' THEN
               UPDATE orders SET status = 'confirmed' WHERE id = NEW.order_id AND status = 'pending';
             ELSIF TG_OP = 'UPDATE' AND (OLD.status IS DISTINCT FROM NEW.status)
                  AND NEW.status = 'completed' THEN
               UPDATE orders SET status = 'confirmed' WHERE id = NEW.order_id;
             END IF;
          END IF;
          RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
        """
    )

    op.execute(
        """
        CREATE OR REPLACE VIEW v_top_selling_products AS
        SELECT
          p.id AS product_id,
          p.name,
          SUM(oi.quantity)::BIGINT AS units_sold,
          SUM(oi.quantity * oi.unit_price)::NUMERIC(14,2) AS revenue
        FROM order_items oi
        JOIN orders o ON o.id = oi.order_id
        JOIN payments pay ON pay.order_id = o.id AND pay.status = 'completed'
        JOIN products p ON p.id = oi.product_id
        GROUP BY p.id, p.name
        ORDER BY units_sold DESC;

        CREATE OR REPLACE VIEW v_monthly_sales AS
        SELECT
          date_trunc('month', o.created_at) AS month,
          COALESCE(SUM(o.total), 0)::NUMERIC(14,2) AS total_sales,
          COUNT(DISTINCT o.id)::BIGINT AS order_count
        FROM orders o
        JOIN payments p ON p.order_id = o.id AND p.status = 'completed'
        GROUP BY date_trunc('month', o.created_at)
        ORDER BY month;

        CREATE OR REPLACE VIEW v_active_customers AS
        SELECT
          u.id AS user_id,
          u.email,
          COUNT(o.id) AS order_count,
          COALESCE(SUM(o.total), 0)::NUMERIC(14,2) AS lifetime_value
        FROM users u
        JOIN orders o ON o.user_id = u.id
        JOIN payments p ON p.order_id = o.id AND p.status = 'completed'
        GROUP BY u.id, u.email
        HAVING COUNT(o.id) >= 1;
        """
    )

    op.execute("DROP INDEX IF EXISTS ix_email_queue_status_created;")
    op.drop_table("email_queue")
