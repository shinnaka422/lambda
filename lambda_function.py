import json
import os
import sys
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError, LineBotApiError
from utils.logger import setup_logger

# ログ設定
logger = setup_logger()

# 環境変数からLINEアクセストークンとシークレットを取得
CHANNEL_ACCESS_TOKEN = os.getenv('CHANNEL_ACCESS_TOKEN')
CHANNEL_SECRET = os.getenv('CHANNEL_SECRET')

if not CHANNEL_ACCESS_TOKEN or not CHANNEL_SECRET:
    logger.error('LINE環境変数が設定されていません。')
    sys.exit(1)

line_bot_api = LineBotApi(CHANNEL_ACCESS_TOKEN)
webhook_handler = WebhookHandler(CHANNEL_SECRET)

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