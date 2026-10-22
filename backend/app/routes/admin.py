from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import delete, func, select, text
from sqlalchemy.orm import Session, joinedload

from app.api.deps import get_current_user, require_roles
from app.database.session import get_db
from app.models import Coupon, Inventory, Notification, Order, OrderItem, Payment, Product, Role, SqlAuditLog, User, UserRole
from app.schemas.dto import AdminUserUpdateRoleIn, AnalyticsRow, DashboardStatsOut, ProductModerationIn, SqlAuditOut, UserOut

router = APIRouter(dependencies=[Depends(require_roles("admin"))])


@router.get("/analytics/dashboard", response_model=DashboardStatsOut)
def admin_dashboard(db: Session = Depends(get_db)):
    revenue = db.scalar(
        select(func.coalesce(func.sum(Order.total), 0)).where(
            Order.id.in_(
                select(Order.id)
                .join(Payment, Payment.order_id == Order.id)
                .where(Payment.status == "Success")
            )
        )
    )
    users = db.scalar(select(func.count()).select_from(User)) or 0
    products = db.scalar(select(func.count()).select_from(Product)) or 0
    orders_cnt = db.scalar(select(func.count()).select_from(Order)) or 0
    return DashboardStatsOut(
        total_users=int(users),
        total_products=int(products),
        total_orders=int(orders_cnt),
        revenue_completed=revenue or 0,
    )


@router.get("/analytics/top-products", response_model=AnalyticsRow)
def top_products(db: Session = Depends(get_db)):
    rows = db.execute(text("SELECT * FROM v_top_selling_products LIMIT 15")).mappings().all()
    return AnalyticsRow(data=[dict(r) for r in rows])


@router.get("/analytics/monthly", response_model=AnalyticsRow)
def monthly(db: Session = Depends(get_db)):
    rows = db.execute(text("SELECT * FROM v_monthly_sales ORDER BY month DESC LIMIT 24")).mappings().all()
    return AnalyticsRow(data=[dict(r) for r in rows])


@router.get("/analytics/active-customers", response_model=AnalyticsRow)
def active_customers(db: Session = Depends(get_db)):
    rows = db.execute(text("SELECT * FROM v_active_customers ORDER BY lifetime_value DESC LIMIT 50")).mappings().all()
    return AnalyticsRow(data=[dict(r) for r in rows])


@router.get("/users", response_model=list[UserOut])
def list_users(db: Session = Depends(get_db)):
    stmt = select(User).options(joinedload(User.roles)).order_by(User.id)
    return db.scalars(stmt).unique().all()


@router.patch("/users/{user_id}/roles", response_model=UserOut)
def update_roles(
    user_id: int,
    body: AdminUserUpdateRoleIn,
    db: Session = Depends(get_db),
):
    user = db.execute(select(User).where(User.id == user_id)).scalar_one_or_none()
    if not user:
        raise HTTPException(404, "User not found")
    allowed = {"admin", "seller", "customer"}
    if not set(body.role_names).issubset(allowed) or not body.role_names:
        raise HTTPException(400, "Invalid role set")
    db.execute(delete(UserRole).where(UserRole.user_id == user_id))
    for name in body.role_names:
        role = db.execute(select(Role).where(Role.name == name)).scalar_one_or_none()
        if not role:
            raise HTTPException(400, f"Unknown role {name}")
        db.add(UserRole(user_id=user_id, role_id=role.id))
    db.commit()
    stmt = select(User).options(joinedload(User.roles)).where(User.id == user_id)
    return db.scalars(stmt).unique().one()


@router.get("/products/pending", response_model=list[dict])
def pending_products(db: Session = Depends(get_db)):
    stmt = select(Product).where(Product.moderation_status == "pending").order_by(Product.id.desc())
    items = db.scalars(stmt).all()
    return [
        {
            "id": p.id,
            "name": p.name,
            "seller_user_id": p.seller_user_id,
            "moderation_status": p.moderation_status,
        }
        for p in items
    ]


@router.patch("/products/{product_id}/moderation")
def moderate_product(
    product_id: int,
    body: ProductModerationIn,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_user),
):
    prod = db.execute(select(Product).where(Product.id == product_id)).scalar_one_or_none()
    if not prod:
        raise HTTPException(404, "Product not found")
    prod.moderation_status = body.status
    prod.moderated_by_user_id = admin.id
    db.commit()
    return {"detail": "updated"}


@router.delete("/products/{product_id}")
def admin_delete_product(product_id: int, db: Session = Depends(get_db)):
    prod = db.execute(select(Product).where(Product.id == product_id)).scalar_one_or_none()
    if not prod:
        raise HTTPException(404, "Product not found")
    oc = db.scalar(select(func.count()).select_from(OrderItem).where(OrderItem.product_id == product_id)) or 0
    if oc > 0:
        raise HTTPException(400, "Product tied to historical orders; deactivate instead")
    db.execute(delete(Inventory).where(Inventory.product_id == product_id))
    db.delete(prod)
    db.commit()
    return {"detail": "deleted"}


@router.get("/orders", response_model=list[dict])
def admin_orders(limit: int = Query(50, le=200), db: Session = Depends(get_db)):
    stmt = select(Order).order_by(Order.created_at.desc()).limit(limit)
    rows = db.scalars(stmt).all()
    return [
        {
            "id": o.id,
            "user_id": o.user_id,
            "status": o.status,
            "total": str(o.total),
            "created_at": o.created_at.isoformat(),
        }
        for o in rows
    ]


@router.get("/audit/sql", response_model=list[SqlAuditOut])
def sql_audit_logs(limit: int = 100, db: Session = Depends(get_db)):
    stmt = select(SqlAuditLog).order_by(SqlAuditLog.created_at.desc()).limit(limit)
    rows = db.scalars(stmt).all()
    return [
        SqlAuditOut(
            id=r.id,
            action=r.action,
            table_name=r.table_name,
            entity_id=r.entity_id,
            created_at=r.created_at,
            payload_preview=(r.payload[:200] + "…") if r.payload and len(r.payload) > 200 else r.payload,
        )
        for r in rows
    ]


@router.post("/coupons/seed-demo")
def seed_coupon(db: Session = Depends(get_db)):
    code = "SAVE10"
    exists = db.execute(select(Coupon).where(Coupon.code == code)).scalar_one_or_none()
    if exists:
        return {"detail": "already exists", "code": code}
    c = Coupon(code=code, percent_off=10, min_order_amount=0, is_active=True)
    db.add(c)
    db.commit()
    return {"detail": "created", "code": code}


@router.post("/notify/{user_id}")
def admin_notify(user_id: int, title: str, body: str, db: Session = Depends(get_db)):
    n = Notification(user_id=user_id, title=title, body=body, is_read=False)
    db.add(n)
    db.commit()
    return {"detail": "sent"}
