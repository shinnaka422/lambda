from linebot import LineBotApi
from linebot.models import TextMessage, TextSendMessage
import random

# LINE Bot API初期化
CHANNEL_ACCESS_TOKEN = "NC9qOw+k8dJxigvluz7FoDb91a6XrjYSKsRA8UNbAe9n/nZmbcSXt2rO82+c9My3Bxvy7yVhy+h+fblcJdkCU7U921s4f1YclZf7gaZngucKfgzHvj7rHH33BM3X3M+Rma9Sd5aHhvNMOyETSw/20gdB04t89/1O/w1cDnyilFU="
YOUR_LINE_ID = "U8c6b1a8150c54b4aafe58689cb13d26a"

line_bot_api = LineBotApi(CHANNEL_ACCESS_TOKEN)

def get_random_message():
    try:
        # Lambda環境での絶対パスを使用
        with open('/var/task/messages.txt', 'r', encoding='utf-8') as file:
            messages = file.read().splitlines()
            message = random.choice(messages)
            # \nを実際の改行に変換
            return message.replace('\\n', '\n')
    except Exception as e:
        print(f"メッセージファイルの読み込みに失敗しました: {str(e)}")
        return "連絡は？"

def lambda_handler(event, context):
    try:
        # ランダムなメッセージを取得して送信
        message = get_random_message()
        line_bot_api.push_message(
            YOUR_LINE_ID,
            TextSendMessage(text=message)
        )
        print("Push message sent successfully.")
        return {
            'statusCode': 200,
            'body': 'Message sent successfully'
        }
    except Exception as e:
        print(f"Failed to send push message: {str(e)}")
        return {
            'statusCode': 500,
            'body': f'Error: {str(e)}'
        }