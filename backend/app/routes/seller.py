from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_roles
from app.database.session import get_db
from app.models import Inventory, Order, OrderItem, Product, User

router = APIRouter(dependencies=[Depends(require_roles("seller"))])


class InventoryPatch(BaseModel):
    quantity: int | None = Field(default=None, ge=0)
    reorder_threshold: int | None = Field(default=None, ge=0)
    price: Decimal | None = Field(default=None, ge=0)


@router.get("/orders")
def seller_orders(db: Session = Depends(get_db), seller: User = Depends(get_current_user)):
    subq = (
        select(OrderItem.order_id)
        .join(Product, Product.id == OrderItem.product_id)
        .where(Product.seller_user_id == seller.id)
        .distinct()
    )
    stmt = select(Order).where(Order.id.in_(subq)).order_by(Order.created_at.desc())
    orders = db.scalars(stmt).all()
    return [
        {
            "id": o.id,
            "user_id": o.user_id,
            "status": o.status,
            "total": str(o.total),
            "created_at": o.created_at.isoformat(),
        }
        for o in orders
    ]


@router.get("/analytics/sales")
def seller_sales(db: Session = Depends(get_db), seller: User = Depends(get_current_user)):
    revenue = db.scalar(
        select(func.coalesce(func.sum(OrderItem.quantity * OrderItem.unit_price), 0))
        .join(Product, Product.id == OrderItem.product_id)
        .join(Order, Order.id == OrderItem.order_id)
        .where(Product.seller_user_id == seller.id)
    )
    units = db.scalar(
        select(func.coalesce(func.sum(OrderItem.quantity), 0))
        .join(Product, Product.id == OrderItem.product_id)
        .where(Product.seller_user_id == seller.id)
    )
    return {"revenue": str(revenue or 0), "units_sold": int(units or 0)}


@router.patch("/products/{product_id}")
def patch_product(
    product_id: int,
    body: InventoryPatch,
    db: Session = Depends(get_db),
    seller: User = Depends(get_current_user),
):
    prod = db.execute(select(Product).where(Product.id == product_id)).scalar_one_or_none()
    if not prod or prod.seller_user_id != seller.id:
        raise HTTPException(404, "Product not found")
    if body.price is not None:
        prod.price = body.price
    inv = db.execute(select(Inventory).where(Inventory.product_id == product_id)).scalar_one_or_none()
    if inv is None:
        raise HTTPException(400, "Inventory row missing")
    if body.quantity is not None:
        inv.quantity = body.quantity
    if body.reorder_threshold is not None:
        inv.reorder_threshold = body.reorder_threshold
    db.commit()
    return {"detail": "updated"}
