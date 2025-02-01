import stripe
import json
import logging
import os

# ロガーの設定
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# 環境変数から設定を取得
STRIPE_SECRET_KEY = os.getenv('STRIPE_SECRET_KEY')
STRIPE_WEBHOOK_SECRET = os.getenv('STRIPE_WEBHOOK_SECRET')

# 環境変数が設定されているか確認
if not STRIPE_SECRET_KEY or not STRIPE_WEBHOOK_SECRET:
    logger.error("必要な環境変数が設定されていません")
    raise ValueError("STRIPE_SECRET_KEY と STRIPE_WEBHOOK_SECRET が必要です")

# Stripeのシークレットキーを設定
stripe.api_key = STRIPE_SECRET_KEY

def create_payment_intent(amount, currency='jpy'):
    """
    決済インテントを作成する関数
    """
    try:
        payment_intent = stripe.PaymentIntent.create(
            amount=amount,  # 金額（日本円の場合は整数）
            currency=currency,
            automatic_payment_methods={
                'enabled': True,
            }
        )
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'clientSecret': payment_intent.client_secret
            })
        }
        
    except stripe.error.StripeError as e:
        logger.error(f"Stripeエラー: {str(e)}")
        return {
            'statusCode': 400,
            'body': json.dumps({
                'error': str(e)
            })
        }
    
    except Exception as e:
        logger.error(f"予期せぬエラー: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': '内部サーバーエラー'
            })
        }

def handle_webhook(event):
    """
    Stripeからのwebhookを処理する関数
    """
    try:
        # webhookシークレットを環境変数から取得
        webhook_secret = STRIPE_WEBHOOK_SECRET
        
        # イベントデータとシグネチャを取得
        payload = event['body']
        sig_header = event['headers']['Stripe-Signature']
        
        # イベントを検証
        stripe_event = stripe.Webhook.construct_event(
            payload, sig_header, webhook_secret
        )
        
        # イベントタイプに応じた処理
        if stripe_event['type'] == 'payment_intent.succeeded':
            payment_intent = stripe_event['data']['object']
            logger.info(f"決済成功: {payment_intent['id']}")
            # ここに決済成功時の処理を追加
            
        return {
            'statusCode': 200,
            'body': json.dumps({'received': True})
        }
        
    except stripe.error.SignatureVerificationError as e:
        logger.error(f"Webhook署名エラー: {str(e)}")
        return {
            'statusCode': 400,
            'body': json.dumps({'error': 'Invalid signature'})
        }
        
    except Exception as e:
        logger.error(f"Webhookエラー: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Webhook handling failed'})
        }

def lambda_handler(event, context):
    """
    Lambda関数のメインハンドラー
    """
    try:
        # パスパラメータに基づいて処理を分岐
        path = event.get('path', '')
        
        if path == '/create-payment-intent':
            body = json.loads(event['body'])
            return create_payment_intent(body['amount'])
            
        elif path == '/webhook':
            return handle_webhook(event)
            
        else:
            return {
                'statusCode': 404,
                'body': json.dumps({'error': 'Not found'})
            }
            
    except Exception as e:
        logger.error(f"ハンドラーエラー: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': '内部サーバーエラー'})
        }
