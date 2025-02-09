import json
import logging
import os
import sys
from handlers import message_handler
from linebot import WebhookHandler
from linebot.exceptions import InvalidSignatureError, LineBotApiError
from linebot.models import MessageEvent, TextMessage  # MessageEvent を追加

# ログ設定
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# 環境変数
CHANNEL_SECRET = os.getenv('CHANNEL_SECRET')

if not CHANNEL_SECRET:
    logger.error('環境変数が設定されていません。')
    sys.exit(1)

webhook_handler = WebhookHandler(CHANNEL_SECRET)

@webhook_handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    message_handler.handle_message(event)

def lambda_handler(event, context):
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
    except LineBotApiError as e:
        logger.error(f"LINE APIエラー: {e.message}")
        return {
            'statusCode': 500,
            'body': json.dumps('LINE APIエラーが発生しました。')
        }
    except Exception as e:
        logger.error(f"予期しないエラーが発生しました: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps('サーバーエラーが発生しました。')
        }