"""ACID checkout: sorted row locks, validations, transactional writes, rollback on any failure."""

from __future__ import annotations

import logging
from decimal import Decimal

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models import (
    Address,
    Cart,
    CartItem,
    Coupon,
    Inventory,
    Order,
    OrderItem,
    Payment,
    PaymentStatus,
    Product,
)
from app.models.orm import OrderStatus

logger = logging.getLogger(__name__)


class CheckoutError(RuntimeError):
    pass


class OrderCheckoutService:
    def __init__(self, db: Session):
        self.db = db

    def checkout(
        self,
        *,
        user_id: int,
        cart: Cart,
        address_id: int,
        simulate_failure: bool = False,
        coupon_code: str | None = None,
    ) -> tuple[Order, Payment]:
        order: Order | None = None
        payment: Payment | None = None

        try:
            cart_items = self.db.execute(
                select(CartItem).where(CartItem.cart_id == cart.id)
            ).scalars().all()
            if not cart_items:
                raise CheckoutError("Cart is empty")

            address = (
                self.db.execute(select(Address).where(Address.id == address_id, Address.user_id == user_id))
                .scalar_one_or_none()
            )
            if not address:
                raise CheckoutError("Invalid shipping address")

            coupon: Coupon | None = None
            if coupon_code:
                code = coupon_code.strip().upper()
                coupon = self.db.execute(
                    select(Coupon).where(Coupon.code == code, Coupon.is_active.is_(True))
                ).scalar_one_or_none()
                if not coupon:
                    raise CheckoutError("Invalid coupon")

            sorted_items = sorted(cart_items, key=lambda x: x.product_id)
            totals = Decimal("0")
            lines: list[tuple[Product, int, Decimal]] = []

            for ci in sorted_items:
                inv_row = self.db.scalars(
                    select(Inventory).where(Inventory.product_id == ci.product_id).with_for_update()
                ).one_or_none()
                if inv_row is None:
                    raise CheckoutError(f"Inventory record missing for product {ci.product_id}")

                prod = self.db.scalars(
                    select(Product).where(
                        Product.id == ci.product_id,
                        Product.is_active.is_(True),
                        Product.moderation_status == "approved",
                    )
                ).one_or_none()
                if prod is None:
                    raise CheckoutError("Unavailable product")

                if inv_row.quantity < ci.quantity:
                    raise CheckoutError("Insufficient inventory")

                price = Decimal(prod.price)
                totals += price * Decimal(ci.quantity)
                lines.append((prod, ci.quantity, price))

            subtotal = totals
            if coupon:
                if subtotal < coupon.min_order_amount:
                    raise CheckoutError("Order below coupon minimum")
                discount = Decimal("0")
                if coupon.percent_off:
                    discount += (subtotal * coupon.percent_off) / Decimal("100")
                if coupon.amount_off:
                    discount += coupon.amount_off
                totals = max(Decimal("0"), subtotal - discount)

            if simulate_failure:
                raise CheckoutError("Simulated payment failure – entire transaction rolled back")

            order = Order(
                user_id=user_id,
                address_id=address_id,
                status=OrderStatus.pending.value,
                total=totals,
                coupon_id=coupon.id if coupon else None,
            )
            self.db.add(order)
            self.db.flush()

            for prod, qty, price in lines:
                self.db.add(
                    OrderItem(order_id=order.id, product_id=prod.id, quantity=qty, unit_price=price)
                )

            payment = Payment(
                order_id=order.id,
                provider="simulated",
                status=PaymentStatus.pending.value,
                simulated_ref="pending",
            )
            self.db.add(payment)
            self.db.flush()

            payment.simulated_ref = f"SIM-{order.id}-{payment.id}"
            self.db.execute(delete(CartItem).where(CartItem.cart_id == cart.id))
            self.db.commit()
        except Exception as exc:
            self.db.rollback()
            logger.exception("Checkout failed for user %s: %s", user_id, exc)
            raise

        self.db.refresh(order)
        self.db.refresh(payment)
        return order, payment
