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

# 会話履歴を保持するリスト
conversation_history = []

def get_claude_response(user_input):
    try:
        # ユーザーの入力を会話履歴に追加
        conversation_history.append({"role": "user", "content": user_input})
        
        # 会話履歴が長すぎる場合は古いメッセージを削除
        if len(conversation_history) > 10:  # ユーザーとAIのメッセージを合わせて10件
            conversation_history.pop(0)
        
        # Bedrock用のリクエストボディを作成
        body = json.dumps({
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 500,
            "messages": conversation_history
        })
        
        logger.info(f"Request body: {body}")
        
        # Bedrockを呼び出してレスポンスを取得
        response = bedrock.invoke_model(
            modelId='anthropic.claude-3-haiku-20240307-v1:0',
            body=body.encode('utf-8')
        )
        
        # レスポンスの解析
        response_body = json.loads(response['body'].read().decode('utf-8'))
        logger.info(f"Complete response from Bedrock: {response_body}")  # レスポンス全体をログに出力
        
        # Claude 3の新しい応答形式に対応
        if 'content' in response_body:
            ai_response = response_body['content'][0]['text']
            # AIの応答を会話履歴に追加
            conversation_history.append({"role": "assistant", "content": ai_response})
            return ai_response
        else:
            logger.error(f"Unexpected response format: {response_body}")
            return "応答の形式が不正です。"
    
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