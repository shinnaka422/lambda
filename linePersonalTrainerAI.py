import json
import logging
import os
import sys
import openai
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError, LineBotApiError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import requests
import boto3
from datetime import datetime
from boto3.dynamodb.conditions import Key

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

# DynamoDB クライアントの初期化
dynamodb = boto3.resource('dynamodb')
conversation_table = dynamodb.Table('linebot-conversation-history')

def get_chatgpt_response(user_input, conversation_history):
    """
    ChatGPTからの応答を取得
    """
    try:
        # システムメッセージを追加
        messages = [
            {
                "role": "system",
                "content": "あなたはLINEチャットボットのアシスタントです。ユーザーとの会話履歴を考慮しながら、親切で自然な返答をしてください。"
            }
        ]
        
        # 会話履歴を追加
        messages.extend(conversation_history)
        
        # 現在の入力を追加
        messages.append({"role": "user", "content": user_input})
        
        logger.info(f"Sending messages to ChatGPT: {messages}")
        
        # ChatGPT APIを呼び出してレスポンスを取得
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=messages,
            max_tokens=500,
            temperature=0.7
        )
        
        if response.choices and len(response.choices) > 0:
            return response.choices[0].message.content
        else:
            logger.error("ChatGPTから応答がありませんでした")
            return "申し訳ありません。応答を生成できませんでした。"
    
    except Exception as e:
        logger.error(f"ChatGPTエラー: {str(e)}")
        return f"エラーが発生しました: {str(e)}"

def get_conversation_history(line_id, limit=5):
    """
    指定されたユーザーの会話履歴を取得
    """
    try:
        response = conversation_table.query(
            KeyConditionExpression=Key('lineId').eq(line_id),
            ScanIndexForward=False,  # 新しい順
            Limit=limit
        )
        
        # 古い順に並び替え（タイムスタンプで昇順ソート）
        messages = sorted(response['Items'], key=lambda x: x['timestamp'])
        
        # ChatGPTに送信する形式に変換
        formatted_messages = []
        for msg in messages:
            formatted_messages.append({
                "role": "user", 
                "content": msg['user_message']
            })
            if msg.get('assistant_message'):
                formatted_messages.append({
                    "role": "assistant", 
                    "content": msg['assistant_message']
                })
        
        logger.info(f"Retrieved conversation history: {formatted_messages}")
        return formatted_messages
    
    except Exception as e:
        logger.error(f"会話履歴の取得エラー: {str(e)}")
        return []

def save_conversation(line_id, user_message, assistant_message):
    """
    会話をDynamoDBに保存
    """
    try:
        timestamp = datetime.now().isoformat()
        conversation_table.put_item(
            Item={
                'lineId': line_id,
                'timestamp': timestamp,
                'user_message': user_message,
                'assistant_message': assistant_message
            }
        )
        logger.info(f"会話を保存しました: {line_id}")
    
    except Exception as e:
        logger.error(f"会話の保存エラー: {str(e)}")

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
        user_message = event.message.text
        user_id = event.source.user_id
        
        # ローディングを開始
        start_loading(user_id)
        
        # 会話履歴を取得
        conversation_history = get_conversation_history(user_id)
        logger.info(f"Conversation history length: {len(conversation_history)}")
        
        # ChatGPTからの応答を取得
        answer = get_chatgpt_response(user_message, conversation_history)
        logger.info(f"ChatGPT response: {answer}")
        
        # 会話を保存
        save_conversation(user_id, user_message, answer)
        
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