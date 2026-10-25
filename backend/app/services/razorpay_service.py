# New changes for the payment gateway 


from decimal import Decimal , ROUND_HALF_UP


import razorpay

from app.config import settings


class RazorpayNotConfiguredError(RuntimeError):
    pass

def  get_razorpay_client():
    if not settings.razorpay_key_id or not settings.razorpay_key_secret:
        raise RazorpayNotConfiguredError(
            "Razorpay API Credentials are not configured"
        )
        
    return razorpay.Client(
        auth=(
            settings.razorpay_key_id,
            settings.razorpay_key_secret,
        )
    )
    
    
def create_razorpay_order(total:Decimal , receipt:str) -> dict:
    client = get_razorpay_client()
    
    amount_paise = int(
        (Decimal(total)*100).quantize(
            Decimal("1"),
            rounding=ROUND_HALF_UP
        )    
    )
    
    if amount_paise <= 0:
        raise ValueError("Payment amount must be greater than zero")
    
    return client.order.create(
        data = {
            "amount":amount_paise,
            "currency":settings.razorpay_currency,
            "receipt":receipt
        }
    )


def verify_razorpay_signature(razorpay_order_id:str , razorpay_payment_id:str , razorpay_signature:str) -> None:
    client = get_razorpay_client()
    
    
    client.utility.verify_payment_signature(
        {
            "razorpay_order_id": razorpay_order_id,
            "razorpay_payment_id":razorpay_payment_id,
            "razorpay_signature":razorpay_signature,
        }
    )



def fetch_razorpay_payment(razorpay_payment_id: str) -> dict:
    client = get_razorpay_client()
    return client.payment.fetch(razorpay_payment_id)