import json
import logging
import os
import sys
import boto3
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError, LineBotApiError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

# ログ設定
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# 環境変数からLINEアクセストークンとシークレットを取得
CHANNEL_ACCESS_TOKEN = os.getenv('CHANNEL_ACCESS_TOKEN')
CHANNEL_SECRET = os.getenv('CHANNEL_SECRET')

if not CHANNEL_ACCESS_TOKEN or not CHANNEL_SECRET:
    logger.error('LINE環境変数が設定されていません。')
    sys.exit(1)

line_bot_api = LineBotApi(CHANNEL_ACCESS_TOKEN)
webhook_handler = WebhookHandler(CHANNEL_SECRET)

# Bedrockクライアントの初期化
bedrock = boto3.client(
    service_name='bedrock-runtime',
    region_name='us-east-1'
)

def get_claude_response(user_input):
    try:
        system_message = "あなたは世界一のフィットネスコーチです、私の質問と基本情報を元に痩せるまでの完璧な私専用のパーソナルアドバイスをしてください。性別: male、年齢: 34歳、身長: 175cm、体重: 70kg、目標体重: 65kg、目標期間: 6 months、食事回数: 3 meals a day、運動頻度: 3 times a week (gym)"
        # Bedrock用のリクエストボディを作成
        body = json.dumps({
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 500,
            "messages": [
                {
                    "role": "assistant",
                    "content": system_message
                },
                {
                    "role": "user",
                    "content": user_input
                }
            ]
        })
        
        logger.info(f"Request body: {body}")
        
        # Bedrockを呼び出してレスポンスを取得
        response = bedrock.invoke_model(
            modelId='anthropic.claude-3-haiku-20240307-v1:0',
            body=body.encode('utf-8')
        )
        
        response_body = json.loads(response['body'].read().decode('utf-8'))
        return response_body['choices'][0]['message']['content']
    
    except Exception as e:
        logger.error(f"Bedrockエラー: {str(e)}")
        return f"エラーが発生しました: {str(e)}"

@webhook_handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    try:
        # ユーザーのメッセージ内容
        user_message = event.message.text

        # Claudeからの応答を取得
        answer = get_claude_response(user_message)
        logger.info(f"Claude response: {answer}")

        # 応答メッセージをLINEに送信
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=answer))

    except Exception as e:
        logger.error(f"handle_message関数でエラーが発生しました: {e}")
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text="エラーが発生しました。"))

def lambda_handler(event, context):
    signature = event['headers'].get('x-line-signature')
    if not signature:
        return {'statusCode': 400, 'body': json.dumps('Missing signature')}

    body = event['body']
    logger.info(f"Webhook body: {body}")

    try:
        webhook_handler.handle(body, signature)
    except InvalidSignatureError:
        logger.error("署名が無効です。")
        return {'statusCode': 400, 'body': json.dumps('Invalid signature')}
    except LineBotApiError as e:
        logger.error(f"LINE APIエラー: {e.message}")
        return {'statusCode': 500, 'body': json.dumps('LINE API error')}
    except Exception as e:
        logger.error(f"予期しないエラーが発生しました: {e}")
        return {'statusCode': 500, 'body': json.dumps('Internal server error')}

    return {'statusCode': 200, 'body': json.dumps('Success')}