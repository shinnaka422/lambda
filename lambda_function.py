import json
import logging
import os
import sys
import openai
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError, LineBotApiError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, FlexSendMessage, BubbleContainer
import requests
import boto3
from datetime import datetime, timedelta
from boto3.dynamodb.conditions import Key, Attr
import pytz
import stripe

# ログ設定
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# 環境変数からLINEアクセストークンとシークレットを取得
CHANNEL_ACCESS_TOKEN = os.getenv('CHANNEL_ACCESS_TOKEN')
CHANNEL_SECRET = os.getenv('CHANNEL_SECRET')
STRIPE_SECRET_KEY = os.getenv('STRIPE_SECRET_KEY')
OPENAI_API_KEY = os.environ['OPENAI_API_KEY']

if not CHANNEL_ACCESS_TOKEN or not CHANNEL_SECRET or not STRIPE_SECRET_KEY:
    logger.error('環境変数が設定されていません。')
    sys.exit(1)

# OpenAI APIキーの設定
openai.api_key = OPENAI_API_KEY

# Stripe設定を追加
stripe.api_key = STRIPE_SECRET_KEY

line_bot_api = LineBotApi(CHANNEL_ACCESS_TOKEN)
webhook_handler = WebhookHandler(CHANNEL_SECRET)

# DynamoDB クライアントの初期化
dynamodb = boto3.resource('dynamodb')
conversation_table = dynamodb.Table('dev-linebot-conversation-history')

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

def get_today_conversation_count(line_id):
    """
    今日の会話回数を取得
    """
    try:
        # 日本時間で今日の日付を取得
        jst = pytz.timezone('Asia/Tokyo')
        today = datetime.now(jst).date()
        today_start = datetime.combine(today, datetime.min.time()).astimezone(jst)
        today_end = datetime.combine(today, datetime.max.time()).astimezone(jst)
        
        # ISO形式の文字列に変換
        start_str = today_start.isoformat()
        end_str = today_end.isoformat()
        
        # 今日の会話を取得
        response = conversation_table.query(
            KeyConditionExpression=Key('lineId').eq(line_id) & 
                                 Key('timestamp').between(start_str, end_str)
        )
        
        return len(response['Items'])
    
    except Exception as e:
        logger.error(f"会話カウントの取得エラー: {str(e)}")
        return 0

def get_conversation_history(line_id, limit=5):
    """
    指定されたユーザーの会話履歴を取得
    """
    try:
        response = conversation_table.query(
            KeyConditionExpression=Key('lineId').eq(line_id),
            ScanIndexForward=False,  # 新しい順
            Limit=limit * 2  # ユーザーとアシスタントのメッセージペアを考慮
        )
        
        # 古い順に並び替え
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
        # 日本時間のタイムスタンプを生成
        jst = pytz.timezone('Asia/Tokyo')
        timestamp = datetime.now(jst).isoformat()
        
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
        alt_text="サブスクリプションのご案内",
        contents={
            "type": "bubble",
            "header": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "text",
                        "text": "AIチャットボット",
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
                        "text": "プレミアムプラン",
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
                        "text": "・無制限のAIチャット\n・優先サポート\n・高度な機能へのアクセス",
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
                            "label": "プレミアムに登録",
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
    try:
        user_message = event.message.text
        user_id = event.source.user_id
        
        daily_count = get_today_conversation_count(user_id)
        logger.info(f"Today's conversation count for user {user_id}: {daily_count}")
        
        if daily_count >= 3:
            # Stripeセッション作成
            session = create_stripe_checkout_session(user_id)
            # Flexメッセージ作成
            flex_message = create_subscription_flex_message(session.url)
            
            # テキストメッセージとFlexメッセージを配列で送信
            line_bot_api.reply_message(
                event.reply_token,
                [
                    TextSendMessage(text="本日の上限に到達しました。\n毎日「無料で3通」お使いいただけますので、明日までお待ちください✨\nプレミアムプランに加入すると、引き続きお使いいただけます✨"),
                    flex_message
                ]
            )
            return
        
        # 会話履歴を取得
        conversation_history = get_conversation_history(user_id)
        
        # ローディングを開始
        start_loading(user_id)
        
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
    """
    AWS Lambda のハンドラー関数
    """
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