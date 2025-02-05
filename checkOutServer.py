import json
import logging
import os
import stripe
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError, LineBotApiError
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,
    FlexSendMessage, BubbleContainer
)

# ログ設定
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# 環境変数の設定
CHANNEL_ACCESS_TOKEN = os.getenv('CHANNEL_ACCESS_TOKEN')
CHANNEL_SECRET = os.getenv('CHANNEL_SECRET')
STRIPE_SECRET_KEY = os.getenv('STRIPE_SECRET_KEY')

# LINE Bot API
line_bot_api = LineBotApi(CHANNEL_ACCESS_TOKEN)
webhook_handler = WebhookHandler(CHANNEL_SECRET)

# Stripe設定
stripe.api_key = STRIPE_SECRET_KEY

def create_stripe_checkout_session(line_user_id):
    """Stripeの支払いセッションを作成"""
    try:
        # 顧客作成
        customer = stripe.Customer.create(
            metadata={"lineId": line_user_id}
        )
        
        # チェックアウトセッション作成
        session = stripe.checkout.Session.create(
            customer=customer.id,
            payment_method_types=['card'],
            line_items=[{
                'price': 'price_1Qnga52M1XKafECj1TnzYuWt',  # あなたの実際のPrice ID
                'quantity': 1,
            }],
            mode='subscription',
            success_url='https://example.com/success',
            cancel_url='https://line.me/R/',
            locale='ja',
            allow_promotion_codes=True,
            customer_update={
                'name': 'auto',
                'address': 'auto'
            }
        )
        
        return session
    except Exception as e:
        logger.error(f"Stripeセッション作成エラー: {str(e)}")
        raise

def create_subscription_flex_message(checkout_url):
    """サブスクリプション案内のFlexメッセージを作成"""
    return FlexSendMessage(
        alt_text="サブスクリプションのごaaaa案内",
        contents={
            "type": "bubble",
            "header": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "text",
                        "text": "パーソナルトレーニング",
                        "weight": "bold",
                        "size": "xl",
                        "color": "#ffffff"
                    }
                ],
                "backgroundColor": "#2B5FED"
            },
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "text",
                        "text": "月額プラン",
                        "weight": "bold",
                        "size": "md",
                        "margin": "md"
                    },
                    {
                        "type": "text",
                        "text": "¥5,000 / 月",
                        "size": "xl",
                        "margin": "md"
                    },
                    {
                        "type": "text",
                        "text": "・AIトレーナーによる24時間サポート\n・パーソナライズされたトレーニングメニュー\n・食事アドバイス\n・進捗管理",
                        "wrap": True,
                        "margin": "md",
                        "size": "sm",
                        "color": "#666666"
                    }
                ]
            },
            "footer": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "button",
                        "action": {
                            "type": "uri",
                            "label": "サブスクリプションに登録",
                            "uri": checkout_url
                        },
                        "style": "primary",
                        "color": "#2B5FED"
                    }
                ]
            }
        }
    )

@webhook_handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    """メッセージイベントのハンドラー"""
    try:
        user_id = event.source.user_id
        
        # Stripeセッション作成
        session = create_stripe_checkout_session(user_id)
        
        # Flexメッセージ作成
        flex_message = create_subscription_flex_message(session.url)
        
        # メッセージ送信
        line_bot_api.reply_message(
            event.reply_token,
            flex_message
        )
        
    except Exception as e:
        logger.error(f"メッセージ処理エラー: {str(e)}")
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="エラーが発生しました。しばらく待ってから再度お試しください。")
        )

def lambda_handler(event, context):
    """Lambda関数のハンドラー"""
    try:
        signature = event['headers'].get('x-line-signature')
        if not signature:
            return {
                'statusCode': 400,
                'body': json.dumps('署名が見つかりません。')
            }

        body = event['body']
        logger.info(f"Webhook body: {body}")

        webhook_handler.handle(body, signature)
        
        return {
            'statusCode': 200,
            'body': json.dumps('Success')
        }
        
    except InvalidSignatureError:
        logger.error("署名が無効です。")
        return {
            'statusCode': 400,
            'body': json.dumps('署名が無効です。')
        }
    except Exception as e:
        logger.error(f"予期しないエラーが発生しました: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps('サーバーエラーが発生しました。')
        }