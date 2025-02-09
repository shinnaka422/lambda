import logging
import requests
import os
from linebot import LineBotApi
from linebot.models import FlexSendMessage, TextSendMessage
import linebot.v3.messaging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

CHANNEL_ACCESS_TOKEN = os.getenv('CHANNEL_ACCESS_TOKEN')
line_bot_api = LineBotApi(CHANNEL_ACCESS_TOKEN)

def start_loading(user_id):
    """LINEのローディングインジケーターを開始"""
    try:
        configuration = linebot.v3.messaging.Configuration(
            access_token=os.getenv('CHANNEL_ACCESS_TOKEN')
        )
        
        with linebot.v3.messaging.ApiClient(configuration) as api_client:
            api_instance = linebot.v3.messaging.MessagingApi(api_client)
            show_loading_animation_request = linebot.v3.messaging.ShowLoadingAnimationRequest(
                chat_id=user_id,
                loading_seconds=20
            )
            api_response = api_instance.show_loading_animation(show_loading_animation_request)
            logger.info("ローディング開始")

    except Exception as e:
        logger.error(f"ローディング開始エラー: {str(e)}")

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

def reply_message(reply_token, messages):
    line_bot_api.reply_message(reply_token, messages)