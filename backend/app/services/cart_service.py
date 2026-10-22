from decimal import Decimal

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models import Cart, CartItem, Product


def get_or_create_cart(db: Session, user_id: int) -> Cart:
    cart = db.execute(select(Cart).where(Cart.user_id == user_id)).scalar_one_or_none()
    if cart is None:
        cart = Cart(user_id=user_id)
        db.add(cart)
        db.flush()
    return cart


def serialize_cart(db: Session, cart: Cart) -> tuple[list[dict], Decimal]:
    items = db.execute(select(CartItem).where(CartItem.cart_id == cart.id)).scalars().all()
    lines: list[dict] = []
    subtotal = Decimal("0")
    for ci in items:
        prod = db.execute(select(Product).where(Product.id == ci.product_id)).scalar_one_or_none()
        if not prod:
            continue
        line_total = Decimal(prod.price) * Decimal(ci.quantity)
        subtotal += line_total
        lines.append({"product_id": prod.id, "quantity": ci.quantity, "price_snapshot": prod.price})
    return lines, subtotal


def upsert_line(db: Session, cart: Cart, product_id: int, quantity: int) -> None:
    prod = db.execute(select(Product).where(Product.id == product_id, Product.is_active.is_(True))).scalar_one_or_none()
    if not prod or prod.moderation_status != "approved":
        raise ValueError("Product unavailable")
    line = db.execute(
        select(CartItem).where(CartItem.cart_id == cart.id, CartItem.product_id == product_id)
    ).scalar_one_or_none()
    if quantity <= 0:
        if line:
            db.execute(delete(CartItem).where(CartItem.id == line.id))
        return
    if line:
        line.quantity = quantity
    else:
        db.add(CartItem(cart_id=cart.id, product_id=product_id, quantity=quantity))
