"""Bulk seed for products and inventory."""

import random
import string
from decimal import Decimal
from sqlalchemy import select
import os
import sys

# Add the project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database.session import SessionLocal
from app.models import (
    Category,
    Inventory,
    Product,
    SellerProfile,
    User,
)

ADJECTIVES = ["Premium", "Smart", "Ultra", "Classic", "Modern", "Eco", "Pro", "Essential", "Deluxe", "Vintage"]
NOUNS = ["Gadget", "Device", "Widget", "Tool", "Accessory", "Gear", "Item", "Solution", "Pack", "Kit"]
CATEGORIES = ["Electronics", "Fashion", "Home", "Garden", "Sports", "Toys", "Books"]

def generate_product_name():
    adj = random.choice(ADJECTIVES)
    noun = random.choice(NOUNS)
    model = "".join(random.choices(string.ascii_uppercase + string.digits, k=4))
    return f"{adj} {noun} {model}"

def slugify(name):
    return name.lower().replace(" ", "-") + "-" + "".join(random.choices(string.digits, k=6))

def run(count: int = 2000) -> None:
    db = SessionLocal()
    try:
        # Ensure we have a seller
        seller = db.execute(select(SellerProfile)).scalars().first()
        if not seller:
            # Create a default seller if none exists
            # This requires a user first
            user = db.execute(select(User).where(User.email == "seller@example.com")).scalar_one_or_none()
            if not user:
                # We can't easily hash password here without app context or repeating logic
                # For simplicity, assume seed.py has run or we use a raw insert if needed
                print("Error: No seller found. Please run seed.py first.")
                return
            seller = SellerProfile(user_id=user.id, shop_name="Bulk Seed Shop")
            db.add(seller)
            db.flush()

        # Ensure we have categories
        category_ids = []
        for cat_name in CATEGORIES:
            slug = cat_name.lower()
            cat = db.execute(select(Category).where(Category.slug == slug)).scalar_one_or_none()
            if not cat:
                cat = Category(name=cat_name, slug=slug, description=f"{cat_name} category")
                db.add(cat)
                db.flush()
            category_ids.append(cat.id)

        print(f"Seeding {count} products...")
        for i in range(count):
            name = generate_product_name()
            slug = slugify(name)
            cat_id = random.choice(category_ids)
            
            p = Product(
                seller_user_id=seller.user_id,
                category_id=cat_id,
                name=name,
                slug=slug,
                description=f"This is a high-quality {name} designed for maximum efficiency.",
                price=Decimal(f"{random.uniform(9.99, 999.99):.2f}"),
                compare_at_price=Decimal(f"{random.uniform(1000, 2000):.2f}") if random.random() > 0.7 else None,
                sku=f"SKU-{slug.upper()}",
                moderation_status="approved",
            )
            db.add(p)
            db.flush()  # To get p.id
            
            inv = Inventory(
                product_id=p.id,
                quantity=random.randint(0, 500),
                reorder_threshold=random.randint(5, 20)
            )
            db.add(inv)
            
            if i % 100 == 0:
                db.commit()
                print(f"Inserted {i} products...")

        db.commit()
        print(f"Successfully seeded {count} products.")
    except Exception as e:
        db.rollback()
        print(f"Error during seeding: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    run(200000)
