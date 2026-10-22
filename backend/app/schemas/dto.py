from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, EmailStr, Field


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"


class RoleOut(BaseModel):
    name: str


class UserOut(BaseModel):
    id: int
    email: EmailStr
    full_name: str
    roles: list[RoleOut]

    model_config = {"from_attributes": True}


class UserRegisterIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)
    full_name: str
    seller_shop_name: str | None = None


class UserLoginIn(BaseModel):
    email: EmailStr
    password: str


class CategoryOut(BaseModel):
    id: int
    name: str
    slug: str

    model_config = {"from_attributes": True}


class ProductOut(BaseModel):
    id: int
    name: str
    slug: str
    description: str
    price: Decimal
    compare_at_price: Decimal | None = None
    category_id: int | None = None
    sku: str | None = None
    seller_user_id: int | None = None

    model_config = {"from_attributes": True}


class ProductDetailOut(ProductOut):
    avg_rating: float | None = None
    stock: int


class ProductCreateIn(BaseModel):
    name: str = Field(min_length=2, max_length=300)
    description: str | None = ""
    price: Decimal = Field(ge=0)
    compare_at_price: Decimal | None = Field(default=None, ge=0)
    category_slug: str | None = None
    sku: str | None = None
    initial_stock: int = Field(ge=0, default=0)
    reorder_threshold: int = Field(ge=0, default=10)


class AddressIn(BaseModel):
    label: str
    line1: str
    city: str
    state: str
    postal_code: str
    country: str = "IN"
    is_default: bool = False


class AddressOut(AddressIn):
    id: int

    model_config = {"from_attributes": True}


class CartLineOut(BaseModel):
    product_id: int
    quantity: int
    price_snapshot: Decimal


class CartOut(BaseModel):
    lines: list[CartLineOut]
    subtotal: Decimal


class CheckoutIn(BaseModel):
    address_id: int
    coupon_code: str | None = None
    simulate_failure: bool = False


class OrderOut(BaseModel):
    id: int
    status: str
    total: Decimal
    created_at: datetime

    model_config = {"from_attributes": True}


class PaymentOut(BaseModel):
    id: int
    status: str
    simulated_ref: str | None

    model_config = {"from_attributes": True}


class CheckoutResponse(BaseModel):
    order: OrderOut
    payment: PaymentOut


class OrderSummaryOut(OrderOut):
    payment_id: int | None = None
    payment_status: str | None = None
    simulated_ref: str | None = None


class ReviewCreateIn(BaseModel):
    rating: int = Field(ge=1, le=5)
    title: str = Field(min_length=2, max_length=160)
    body: str | None = ""


class ReviewOut(BaseModel):
    id: int
    product_id: int
    user_id: int
    rating: int
    title: str
    body: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class NotificationOut(BaseModel):
    id: int
    title: str
    body: str | None
    is_read: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class ChatIn(BaseModel):
    message: str = Field(min_length=1, max_length=2000)


class AnalyticsRow(BaseModel):
    data: list[dict]


class AdminUserUpdateRoleIn(BaseModel):
    role_names: list[str] = Field(description="Allowed: admin seller customer")


class ProductModerationIn(BaseModel):
    status: str = Field(pattern="^(approved|rejected|pending)$")


class SqlAuditOut(BaseModel):
    id: int
    action: str
    table_name: str
    entity_id: int | None
    created_at: datetime
    payload_preview: str | None = None


class DashboardStatsOut(BaseModel):
    total_users: int
    total_products: int
    total_orders: int
    revenue_completed: Decimal
