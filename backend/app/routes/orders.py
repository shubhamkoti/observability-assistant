import logging


from decimal import Decimal
from app.config import settings
from app.services.razorpay_service import (
    create_razorpay_order,
    RazorpayNotConfiguredError,
    verify_razorpay_signature,
    fetch_razorpay_payment,
)







from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.database.session import get_db
from app.models import Order, Payment, PaymentStatus, User
from app.schemas.dto import CheckoutIn, CheckoutResponse, OrderOut, OrderSummaryOut, PaymentOut , RazorpayVerifyIn
from app.services.cart_service import get_or_create_cart
from app.services.email_jobs import publish_pending_email_for_payment
from app.services.order_transaction import CheckoutError, OrderCheckoutService

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/checkout", response_model=CheckoutResponse)
def checkout(
    body: CheckoutIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    cart = get_or_create_cart(db, user.id)
    svc = OrderCheckoutService(db)
    try:
        order, payment = svc.checkout(
            user_id=user.id,
            cart=cart,
            address_id=body.address_id,
            simulate_failure=body.simulate_failure,
            coupon_code=body.coupon_code,
        )
    except CheckoutError as exc:
        db.rollback()
        raise HTTPException(400, str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        db.rollback()
        logger.exception("Unexpected checkout error for user %s: %s", user.id, exc)
        raise HTTPException(500, f"Checkout crashed: {exc}") from exc

    return CheckoutResponse(order=OrderOut.model_validate(order), payment=PaymentOut.model_validate(payment))


@router.get("/mine", response_model=list[OrderSummaryOut])
def list_mine(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    rows = db.execute(
        select(Order, Payment)
        .join(Payment, Payment.order_id == Order.id, isouter=True)
        .where(Order.user_id == user.id)
        .order_by(Order.created_at.desc())
    ).all()
    return [
        OrderSummaryOut(
            id=order.id,
            status=order.status,
            total=order.total,
            created_at=order.created_at,
            payment_id=payment.id if payment else None,
            payment_status=payment.status if payment else None,
            simulated_ref=payment.simulated_ref if payment else None,
        )
        for order, payment in rows
    ]



# Change no 1
@router.post("/{order_id}/create-razorpay-order")
def create_payment_order(
    order_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    order = db.scalars(
        select(Order).where(
            Order.id == order_id,
            Order.user_id == user.id,
        )
    ).one_or_none()

    if order is None:
        raise HTTPException(404, "Order not found")

    payment = db.scalars(
        select(Payment).where(Payment.order_id == order.id)
    ).one_or_none()

    if payment is None:
        raise HTTPException(404, "Payment not found")

    if payment.status == PaymentStatus.success.value:
        raise HTTPException(400, "Payment has already succeeded")

    if payment.status not in (
        PaymentStatus.pending.value,
        PaymentStatus.failed.value,
    ):
        raise HTTPException(400, "Payment is not available for checkout")

    try:
        razorpay_order = create_razorpay_order(
            total=order.total,
            receipt=f"order_{order.id}",
        )
    except RazorpayNotConfiguredError as exc:
        raise HTTPException(503, str(exc)) from exc
    except Exception as exc:
        logger.exception(
            "Razorpay order creation failed for order %s", order.id
        )
        raise HTTPException(502, "Could not create Razorpay order") from exc

    payment.provider = "razorpay"
    payment.status = PaymentStatus.pending.value
    payment.razorpay_order_id = razorpay_order["id"]
    payment.razorpay_payment_id = None
    payment.simulated_ref = None

    try:
        db.commit()
        db.refresh(payment)
    except Exception as exc:
        db.rollback()
        logger.exception(
            "Could not save Razorpay order for internal order %s", order.id
        )
        raise HTTPException(
            500, "Could not save payment information"
        ) from exc

    return {
        "key_id": settings.razorpay_key_id,
        "razorpay_order_id": razorpay_order["id"],
        "amount": razorpay_order["amount"],
        "currency": razorpay_order["currency"],
        "internal_order_id": order.id,
    }




# Change 2
@router.post("/{order_id}/verify-razorpay-payment", response_model=PaymentOut)
def verify_payment(
    order_id: int,
    body: RazorpayVerifyIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    order = db.scalars(
        select(Order).where(
            Order.id == order_id,
            Order.user_id == user.id,
        )
    ).one_or_none()

    if order is None:
        raise HTTPException(404, "Order not found")

    payment = db.scalars(
        select(Payment).where(Payment.order_id == order.id)
    ).one_or_none()

    if payment is None:
        raise HTTPException(404, "Payment not found")

    if (
        payment.provider != "razorpay"
        or payment.razorpay_order_id != body.razorpay_order_id
    ):
        raise HTTPException(400, "Razorpay order ID mismatch")

    # Verify the Razorpay signature and retrieve payment details.
    try:
        verify_razorpay_signature(
            razorpay_order_id=body.razorpay_order_id,
            razorpay_payment_id=body.razorpay_payment_id,
            razorpay_signature=body.razorpay_signature,
        )

        gateway_payment = fetch_razorpay_payment(
            body.razorpay_payment_id
        )

    except RazorpayNotConfiguredError as exc:
        raise HTTPException(503, str(exc)) from exc
    except Exception as exc:
        logger.warning(
            "Razorpay verification failed for order %s", order.id
        )
        raise HTTPException(
            400, "Could not verify Razorpay payment"
        ) from exc

    # Ensure this payment belongs to the expected Razorpay order.
    if gateway_payment.get("order_id") != payment.razorpay_order_id:
        raise HTTPException(400, "Payment order mismatch")

    # Verify the amount and currency.
    expected_amount = int(
        (Decimal(order.total) * 100).quantize(Decimal("1"))
    )

    if gateway_payment.get("amount") != expected_amount:
        raise HTTPException(400, "Payment amount mismatch")

    if gateway_payment.get("currency") != settings.razorpay_currency:
        raise HTTPException(400, "Payment currency mismatch")

    # Only captured payments are considered successful.
    if gateway_payment.get("status") != "captured":
        raise HTTPException(
            400, "Payment has not been captured yet"
        )

    # Prevent a different payment from replacing an existing payment ID.
    if (
        payment.razorpay_payment_id
        and payment.razorpay_payment_id != body.razorpay_payment_id
    ):
        raise HTTPException(400, "Payment ID mismatch")

    # Save the verified payment reference, including on repeat verification.
    payment.razorpay_payment_id = body.razorpay_payment_id
    payment.simulated_ref = body.razorpay_payment_id

    if payment.status != PaymentStatus.success.value:
        payment.status = PaymentStatus.success.value

    try:
        db.commit()
        db.refresh(payment)
    except Exception as exc:
        db.rollback()
        logger.exception(
            "Could not save verified payment for order %s", order.id
        )
        raise HTTPException(
            500, "Could not save payment result"
        ) from exc

    return PaymentOut.model_validate(payment)










@router.get("/{order_id}", response_model=OrderOut)
def order_detail(order_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    order = db.scalars(select(Order).where(Order.id == order_id, Order.user_id == user.id)).one_or_none()
    if order is None:
        raise HTTPException(404, "Order not found")
    return order




@router.get("/{order_id}/payment", response_model=PaymentOut)
def order_payment(order_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    order = db.scalars(select(Order).where(Order.id == order_id, Order.user_id == user.id)).one_or_none()
    if order is None:
        raise HTTPException(404, "Order not found")
    pay = db.scalars(select(Payment).where(Payment.order_id == order.id)).one_or_none()
    if pay is None:
        raise HTTPException(404, "Payment missing")
    return pay




@router.post("/{order_id}/simulate-payment", response_model=PaymentOut)
def simulate_payment(order_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    try:
        order = db.scalars(select(Order).where(Order.id == order_id, Order.user_id == user.id)).one_or_none()
        if order is None:
            raise HTTPException(404, "Order not found")

        payment = db.scalars(select(Payment).where(Payment.order_id == order.id)).one_or_none()
        if payment is None:
            raise HTTPException(404, "Payment missing")

        if payment.status != PaymentStatus.success.value:
            payment.status = PaymentStatus.success.value
            if not payment.simulated_ref or payment.simulated_ref == "pending":
                payment.simulated_ref = f"SIM-{order.id}-{payment.id}"
            db.commit()
            db.refresh(payment)

        publish_pending_email_for_payment(db, payment.id)
        return PaymentOut.model_validate(payment)
    except HTTPException:
        db.rollback()
        raise
    except Exception as exc:  # noqa: BLE001
        db.rollback()
        logger.exception("Payment simulation failed for order %s: %s", order_id, exc)
        raise HTTPException(500, f"Payment simulation failed: {exc}") from exc
