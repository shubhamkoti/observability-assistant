from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.database.session import get_db
from app.models import Product, User, WishlistItem
from app.schemas.dto import ProductOut

router = APIRouter()


@router.get("/", response_model=list[ProductOut])
def list_wishlist(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    stmt = select(Product).join(WishlistItem, WishlistItem.product_id == Product.id).where(WishlistItem.user_id == user.id)
    return db.scalars(stmt).all()


@router.post("/{product_id}", status_code=201)
def add_wish(product_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    prod = db.execute(select(Product).where(Product.id == product_id)).scalar_one_or_none()
    if not prod:
        raise HTTPException(404, "Product not found")
    db.add(WishlistItem(user_id=user.id, product_id=product_id))
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        return {"detail": "already present"}
    return {"detail": "added"}


@router.delete("/{product_id}", status_code=204)
def rm_wish(product_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    db.execute(delete(WishlistItem).where(WishlistItem.user_id == user.id, WishlistItem.product_id == product_id))
    db.commit()
    return
