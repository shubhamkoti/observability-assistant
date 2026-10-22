"""Idempotent seed for demo data (roles, permissions, users, catalog)."""

from __future__ import annotations

from decimal import Decimal

from sqlalchemy import func, select

import os
import sys

# Add the project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database.session import SessionLocal
from app.models import (
    Address,
    Category,
    Coupon,
    Inventory,
    Permission,
    Product,
    Role,
    RolePermission,
    SellerProfile,
    User,
    UserRole,
)
from app.utils.security import hash_password


def run() -> None:
    db = SessionLocal()
    try:
        if db.execute(select(Role).where(Role.name == "admin")).scalar_one_or_none() is None:
            for name in ("admin", "seller", "customer"):
                db.add(Role(name=name))
            db.flush()

        perms = [
            ("users", "read"),
            ("users", "write"),
            ("products", "moderate"),
            ("orders", "read"),
            ("analytics", "read"),
        ]
        for resource, action in perms:
            if db.execute(select(Permission).where(Permission.resource == resource, Permission.action == action)).scalar_one_or_none() is None:
                db.add(Permission(resource=resource, action=action))
        db.flush()

        admin_role = db.execute(select(Role).where(Role.name == "admin")).scalar_one()
        perm_rows = db.scalars(select(Permission)).all()
        for p in perm_rows:
            cnt = db.scalar(
                select(func.count()).select_from(RolePermission).where(
                    RolePermission.role_id == admin_role.id, RolePermission.permission_id == p.id
                )
            )
            if not cnt:
                db.add(RolePermission(role_id=admin_role.id, permission_id=p.id))

        def ensure_user(email: str, full_name: str, password: str, role_names: list[str], shop: str | None = None):
            u = db.execute(select(User).where(User.email == email)).scalar_one_or_none()
            if u:
                return u
            user = User(email=email, full_name=full_name, hashed_password=hash_password(password))
            db.add(user)
            db.flush()
            for rn in role_names:
                r = db.execute(select(Role).where(Role.name == rn)).scalar_one()
                user.roles.append(r)
            if shop:
                db.add(SellerProfile(user_id=user.id, shop_name=shop))
            return user

        admin = ensure_user("admin@example.com", "Admin User", "Admin123!", ["admin", "customer"], None)
        seller = ensure_user("seller@example.com", "Seller One", "Seller123!", ["seller", "customer"], "Demo Shop")
        buyer = ensure_user("buyer@example.com", "Buyer One", "Buyer123!", ["customer"], None)

        cats = [
            ("Electronics", "electronics"),
            ("Fashion", "fashion"),
            ("Home", "home"),
        ]
        for name, slug in cats:
            if db.execute(select(Category).where(Category.slug == slug)).scalar_one_or_none() is None:
                db.add(Category(name=name, slug=slug, description=f"{name} category"))

        db.flush()
        elec = db.execute(select(Category).where(Category.slug == "electronics")).scalar_one()

        if db.execute(select(Product).where(Product.slug == "demo-earbuds-1")).scalar_one_or_none() is None:
            p = Product(
                seller_user_id=seller.id,
                category_id=elec.id,
                name="ANC Wireless Earbuds",
                slug="demo-earbuds-1",
                description="Noise cancelling earbuds with charging case.",
                price=Decimal("79.99"),
                compare_at_price=Decimal("99.00"),
                sku="EAR-001",
                moderation_status="approved",
            )
            db.add(p)
            db.flush()
            db.add(Inventory(product_id=p.id, quantity=40, reorder_threshold=5))

        if db.execute(select(Product).where(Product.slug == "demo-smartwatch-1")).scalar_one_or_none() is None:
            p2 = Product(
                seller_user_id=seller.id,
                category_id=elec.id,
                name="Fitness Smartwatch",
                slug="demo-smartwatch-1",
                description="Heart rate, SpO2, GPS.",
                price=Decimal("129.00"),
                sku="WAT-001",
                moderation_status="approved",
            )
            db.add(p2)
            db.flush()
            db.add(Inventory(product_id=p2.id, quantity=3, reorder_threshold=5))

        if db.execute(select(Coupon).where(Coupon.code == "SAVE10")).scalar_one_or_none() is None:
            db.add(Coupon(code="SAVE10", percent_off=Decimal("10"), min_order_amount=Decimal("0"), is_active=True))

        if db.execute(select(Address).where(Address.user_id == buyer.id)).scalar_one_or_none() is None:
            db.add(
                Address(
                    user_id=buyer.id,
                    label="Home",
                    line1="221B Baker Street",
                    city="Bengaluru",
                    state="KA",
                    postal_code="560001",
                    country="IN",
                    is_default=True,
                )
            )

        db.commit()
        print("Seed complete:", admin.email, seller.email, buyer.email)
    finally:
        db.close()


if __name__ == "__main__":
    run()
