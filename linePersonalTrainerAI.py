import json
import logging
import os
import sys
import openai
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError, LineBotApiError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import requests

# ログ設定
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# 環境変数からLINEアクセストークンとシークレットを取得
CHANNEL_ACCESS_TOKEN = os.getenv('CHANNEL_ACCESS_TOKEN')
CHANNEL_SECRET = os.getenv('CHANNEL_SECRET')
OPENAI_API_KEY = os.environ['OPENAI_API_KEY']

if not CHANNEL_ACCESS_TOKEN or not CHANNEL_SECRET:
    logger.error('LINE環境変数が設定されていません。')
    sys.exit(1)

# OpenAI APIキーの設定
openai.api_key = OPENAI_API_KEY

line_bot_api = LineBotApi(CHANNEL_ACCESS_TOKEN)
webhook_handler = WebhookHandler(CHANNEL_SECRET)

def get_chatgpt_response(user_input):
    try:
        # ChatGPT APIを呼び出してレスポンスを取得
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "user", "content": user_input}
            ],
            max_tokens=500,
            temperature=0.7
        )
        
        logger.info(f"Complete response from ChatGPT: {response}")
        
        # レスポンスの形式が変わるため、アクセス方法を変更
        if hasattr(response, 'choices') and len(response.choices) > 0:
            return response.choices[0].message['content']
        else:
            logger.error(f"Unexpected response format: {response}")
            return "応答の形式が不正です。"
    
    except Exception as e:
        logger.error(f"ChatGPTエラー: {str(e)}")
        return f"エラーが発生しました: {str(e)}"

def start_loading(user_id):
    """LINEのローディングインジケーターを開始"""
    try:
        url = 'https://api.line.me/v2/bot/chat/loading/start'
        headers = {
            'Content-Type': 'application/json; charset=UTF-8',
            'Authorization': f'Bearer {CHANNEL_ACCESS_TOKEN}'
        }
        payload = {
            'chatId': user_id,
            'loadingSeconds': 20
        }
        
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        logger.info("ローディング開始")
        
    except Exception as e:
        logger.error(f"ローディング開始エラー: {str(e)}")

@webhook_handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    try:
        # ユーザーのメッセージ内容
        user_message = event.message.text
        user_id = event.source.user_id
        
        # ローディングを開始
        start_loading(user_id)
        
        # Claudeからの応答を取得
        answer = get_chatgpt_response(user_message)
        logger.info(f"Claude response: {answer}")
        
        # 応答メッセージをLINEに送信
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=answer)
        )
    
    except Exception as e:
        logger.error(f"handle_message関数でエラーが発生しました: {e}")
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="エラーが発生しました。しばらく待ってから再度お試しください。")
        )

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