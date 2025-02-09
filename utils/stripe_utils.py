import logging
import os
import stripe

logger = logging.getLogger()
logger.setLevel(logging.INFO)

STRIPE_SECRET_KEY = os.getenv('STRIPE_SECRET_KEY')
stripe.api_key = STRIPE_SECRET_KEY

def create_stripe_checkout_session(line_user_id):
    """Stripeの支払いセッションを作成"""
    try:
        customer = stripe.Customer.create(
            metadata={"lineId": line_user_id}
        )

        session = stripe.checkout.Session.create(
            customer=customer.id,
            payment_method_types=['card'],
            line_items=[{
                'price': 'price_1Qnga52M1XKafECj1TnzYuWt',
                'quantity': 1,
            }],
            mode='subscription',
            success_url='https://example.com/success',
            locale='ja',
            allow_promotion_codes=True,
            metadata={"lineId": line_user_id},
            customer_update={
                'name': 'auto',
                'address': 'auto'
            }
        )
        return session
    except Exception as e:
        logger.error(f"Stripeセッション作成エラー: {str(e)}")
        raise