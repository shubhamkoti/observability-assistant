from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.api.deps import get_current_active_user_optional, get_current_user
from app.database.session import get_db
from app.models import Category, Inventory, Product, Review, User
from app.schemas.dto import ProductCreateIn, ProductDetailOut, ProductOut
from app.services import mongo_logs

router = APIRouter()


@router.post("/seller", response_model=ProductOut)
def seller_create_product(
    body: ProductCreateIn,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    names = {r.name for r in current.roles}
    if "seller" not in names:
        raise HTTPException(403, "Seller role required")

    slug = "-".join(body.name.lower().split())[:200]
    cat_id = None
    if body.category_slug:
        cat = db.execute(select(Category).where(Category.slug == body.category_slug)).scalar_one_or_none()
        if not cat:
            raise HTTPException(400, "Unknown category slug")
        cat_id = cat.id

    prod = Product(
        seller_user_id=current.id,
        category_id=cat_id,
        name=body.name,
        slug=f"{slug}-{current.id}",
        description=body.description or "",
        price=body.price,
        compare_at_price=body.compare_at_price,
        sku=body.sku,
        moderation_status="pending",
    )
    db.add(prod)
    db.flush()
    inv = Inventory(product_id=prod.id, quantity=body.initial_stock, reorder_threshold=body.reorder_threshold)
    db.add(inv)
    db.commit()
    db.refresh(prod)
    mongo_logs.log_audit(current.id, "PRODUCT_CREATE", {"product_id": prod.id})
    return prod


@router.get("/", response_model=list[ProductOut])
def list_products(
    q: str | None = None,
    category_id: int | None = None,
    limit: int = Query(24, le=100),
    offset: int = 0,
    db: Session = Depends(get_db),
    current: User | None = Depends(get_current_active_user_optional),
):
    stmt = select(Product).where(Product.is_active.is_(True), Product.moderation_status == "approved")
    if category_id:
        stmt = stmt.where(Product.category_id == category_id)
    if q:
        like = f"%{q}%"
        stmt = stmt.where(Product.name.ilike(like))
    stmt = stmt.order_by(Product.id.desc()).offset(offset).limit(limit)
    items = db.scalars(stmt).all()
    if current:
        mongo_logs.log_user_activity(current.id, "BROWSE_PRODUCTS", {"q": q, "category_id": category_id})
    return items


@router.get("/{product_id}", response_model=ProductDetailOut)
def product_detail(
    product_id: int,
    db: Session = Depends(get_db),
    current: User | None = Depends(get_current_active_user_optional),
):
    stmt = (
        select(Product)
        .options(joinedload(Product.inventory))
        .where(
            Product.id == product_id,
            Product.is_active.is_(True),
            Product.moderation_status == "approved",
        )
    )
    prod = db.scalars(stmt).unique().one_or_none()
    if not prod:
        raise HTTPException(404, "Product not found")

    avg_rating = db.execute(
        select(func.avg(Review.rating)).where(Review.product_id == product_id)
    ).scalar_one()
    mongo_logs.log_product_view(current.id if current else None, product_id)

    stock = prod.inventory.quantity if prod.inventory else 0
    return ProductDetailOut(
        id=prod.id,
        name=prod.name,
        slug=prod.slug,
        description=prod.description,
        price=prod.price,
        compare_at_price=prod.compare_at_price,
        category_id=prod.category_id,
        sku=prod.sku,
        seller_user_id=prod.seller_user_id,
        avg_rating=float(avg_rating) if avg_rating is not None else None,
        stock=stock,
    )
