from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.database.session import get_db
from app.models import Notification, Order, OrderItem, Payment, Product, Review, User
from app.schemas.dto import ReviewCreateIn, ReviewOut
from app.services import mongo_logs

router = APIRouter()


@router.post("/product/{product_id}", response_model=ReviewOut)
def create_review(
    product_id: int,
    body: ReviewCreateIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    prod = db.execute(select(Product).where(Product.id == product_id)).scalar_one_or_none()
    if not prod:
        raise HTTPException(404, "Product not found")

    purchased = db.execute(
        select(OrderItem.id)
        .join(Order, Order.id == OrderItem.order_id)
        .join(Payment, Payment.order_id == Order.id)
        .where(
            Order.user_id == user.id,
            OrderItem.product_id == product_id,
            Payment.status == "Success",
        )
        .limit(1)
    ).first()
    if purchased is None:
        raise HTTPException(400, "Purchase required before reviewing")

    existing = db.execute(
        select(Review).where(Review.product_id == product_id, Review.user_id == user.id)
    ).scalar_one_or_none()
    if existing:
        raise HTTPException(400, "Review already submitted")

    review = Review(
        product_id=product_id,
        user_id=user.id,
        rating=body.rating,
        title=body.title,
        body=body.body,
    )
    seller_id = prod.seller_user_id
    note = Notification(
        user_id=seller_id,
        title="New review",
        body=f"Product {prod.name} received {body.rating} stars",
        is_read=False,
    )
    db.add(review)
    db.add(note)
    db.commit()
    db.refresh(note)
    db.refresh(review)
    mongo_logs.log_notification_event(note.id, seller_id, {"product_id": product_id, "review_id": review.id})
    return review


@router.get("/product/{product_id}", response_model=list[ReviewOut])
def list_product_reviews(product_id: int, db: Session = Depends(get_db)):
    stmt = select(Review).where(Review.product_id == product_id).order_by(Review.created_at.desc())
    return db.scalars(stmt).all()
