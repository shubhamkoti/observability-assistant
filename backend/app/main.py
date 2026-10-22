from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Change made by me
from prometheus_fastapi_instrumentator import Instrumentator

from app.config import settings
from app.routes import (
    addresses,
    admin,
    auth,
    cart,
    categories,
    notifications,
    orders,
    products,
    recommendations,
    reviews,
    seller,
    support,
    wishlist,
)

app = FastAPI(title="E-Commerce DBMS Lab API", version="1.0.0")

origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/ready")
def ready():
    return {"status": "ready"}


app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(categories.router, prefix="/api/categories", tags=["categories"])
app.include_router(products.router, prefix="/api/products", tags=["products"])
app.include_router(cart.router, prefix="/api/cart", tags=["cart"])
app.include_router(addresses.router, prefix="/api/addresses", tags=["addresses"])
app.include_router(orders.router, prefix="/api/orders", tags=["orders"])
app.include_router(wishlist.router, prefix="/api/wishlist", tags=["wishlist"])
app.include_router(reviews.router, prefix="/api/reviews", tags=["reviews"])
app.include_router(notifications.router, prefix="/api/notifications", tags=["notifications"])
app.include_router(support.router, prefix="/api/support", tags=["support"])
app.include_router(recommendations.router, prefix="/api/recommendations", tags=["recommendations"])
app.include_router(admin.router, prefix="/api/admin", tags=["admin"])
app.include_router(seller.router, prefix="/api/seller", tags=["seller"])


# Change made by me
Instrumentator().instrument(app).expose(app)