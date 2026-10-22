"""Initial relational schema plus triggers, indexes, views, SQL function."""

from alembic import op

revision = "20250510120000"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    from app.database.session import Base

    Base.metadata.create_all(bind=bind)

    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_orders_status_created ON orders (status, created_at DESC);
        CREATE INDEX IF NOT EXISTS ix_inventory_qty ON inventory (quantity);
        CREATE INDEX IF NOT EXISTS ix_order_items_product ON order_items (product_id);
        """
    )

    op.execute(
        """
        CREATE OR REPLACE FUNCTION fn_reduce_inventory_after_order_item()
        RETURNS TRIGGER AS $$
        BEGIN
          UPDATE inventory
          SET quantity = quantity - NEW.quantity
          WHERE product_id = NEW.product_id;
          RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;

        DROP TRIGGER IF EXISTS trg_after_order_item_insert ON order_items;
        CREATE TRIGGER trg_after_order_item_insert
        AFTER INSERT ON order_items
        FOR EACH ROW
        EXECUTE PROCEDURE fn_reduce_inventory_after_order_item();
        """
    )

    op.execute(
        """
        CREATE OR REPLACE FUNCTION fn_low_stock_alert()
        RETURNS TRIGGER AS $$
        DECLARE seller_uid INTEGER;
        BEGIN
          SELECT p.seller_user_id INTO seller_uid FROM products p WHERE p.id = NEW.product_id;
          IF seller_uid IS NOT NULL
             AND NEW.quantity IS NOT NULL
             AND NEW.reorder_threshold IS NOT NULL
             AND NEW.quantity < NEW.reorder_threshold THEN
            INSERT INTO notifications (user_id, title, body, is_read)
            VALUES (
              seller_uid,
              'Low inventory',
              concat(
                'Product ID ', NEW.product_id::text,
                ' stock ', NEW.quantity::text,
                ' < threshold ',
                NEW.reorder_threshold::text
              ),
              false
            );
          END IF;
          RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;

        DROP TRIGGER IF EXISTS trg_inventory_low_stock ON inventory;
        CREATE TRIGGER trg_inventory_low_stock
        AFTER UPDATE OF quantity ON inventory
        FOR EACH ROW
        EXECUTE PROCEDURE fn_low_stock_alert();
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
        CREATE OR REPLACE FUNCTION fn_audit_product_delete()
        RETURNS TRIGGER AS $$
        BEGIN
          INSERT INTO sql_audit_log (action, table_name, entity_id, actor_user_id, payload)
          VALUES (
            'PRODUCT_DELETE',
            'products',
            OLD.id,
            NULL,
            row_to_json(OLD)::TEXT
          );
          RETURN OLD;
        END;
        $$ LANGUAGE plpgsql;

        DROP TRIGGER IF EXISTS trg_before_product_delete_audit ON products;
        CREATE TRIGGER trg_before_product_delete_audit
        BEFORE DELETE ON products
        FOR EACH ROW
        EXECUTE PROCEDURE fn_audit_product_delete();
        """
    )

    op.execute(
        """
        CREATE OR REPLACE FUNCTION fn_order_item_subtotal(p_order_id INTEGER, p_product_id INTEGER)
        RETURNS NUMERIC AS $$
        DECLARE result NUMERIC;
        BEGIN
          SELECT (oi.quantity * oi.unit_price) INTO result
          FROM order_items oi
          WHERE oi.order_id = p_order_id AND oi.product_id = p_product_id;
          RETURN COALESCE(result, 0);
        END;
        $$ LANGUAGE plpgsql;

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


def downgrade() -> None:
    op.execute(
        """
        DROP VIEW IF EXISTS v_active_customers;
        DROP VIEW IF EXISTS v_monthly_sales;
        DROP VIEW IF EXISTS v_top_selling_products;
        DROP FUNCTION IF EXISTS fn_order_item_subtotal(INTEGER, INTEGER);
        """
    )
    op.execute(
        """
        DROP TRIGGER IF EXISTS trg_before_product_delete_audit ON products;
        DROP FUNCTION IF EXISTS fn_audit_product_delete();

        DROP TRIGGER IF EXISTS trg_payment_update_completed ON payments;
        DROP TRIGGER IF EXISTS trg_payment_insert_completed ON payments;
        DROP FUNCTION IF EXISTS fn_payment_confirms_order();

        DROP TRIGGER IF EXISTS trg_inventory_low_stock ON inventory;
        DROP FUNCTION IF EXISTS fn_low_stock_alert();

        DROP TRIGGER IF EXISTS trg_after_order_item_insert ON order_items;
        DROP FUNCTION IF EXISTS fn_reduce_inventory_after_order_item();
        """
    )
    bind = op.get_bind()
    from app.database.session import Base

    Base.metadata.drop_all(bind=bind)
