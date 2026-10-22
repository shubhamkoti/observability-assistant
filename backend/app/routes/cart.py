from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.database.session import get_db
from app.models import User
from app.schemas.dto import CartLineOut, CartOut
from app.services.cart_service import get_or_create_cart, serialize_cart, upsert_line

router = APIRouter()


class CartUpsert(BaseModel):
    product_id: int
    quantity: int


@router.get("/", response_model=CartOut)
def get_cart(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    cart = get_or_create_cart(db, user.id)
    lines, subtotal = serialize_cart(db, cart)
    return CartOut(
        lines=[CartLineOut(**x) for x in lines],
        subtotal=subtotal,
    )


@router.post("/", response_model=CartOut)
def upsert_cart_item(body: CartUpsert, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    cart = get_or_create_cart(db, user.id)
    try:
        upsert_line(db, cart, body.product_id, body.quantity)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    db.commit()
    lines, subtotal = serialize_cart(db, cart)
    return CartOut(lines=[CartLineOut(**x) for x in lines], subtotal=subtotal)


@router.delete("/", response_model=dict)
def clear_cart(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    from sqlalchemy import delete as sql_delete

    from app.models import CartItem

    cart = get_or_create_cart(db, user.id)
    db.execute(sql_delete(CartItem).where(CartItem.cart_id == cart.id))
    db.commit()
    return {"detail": "cleared", "subtotal": Decimal("0")}
