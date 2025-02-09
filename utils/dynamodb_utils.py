import logging
import boto3
from datetime import datetime
from boto3.dynamodb.conditions import Key
import pytz

logger = logging.getLogger()
logger.setLevel(logging.INFO)

dynamodb = boto3.resource('dynamodb')
conversation_table = dynamodb.Table('dev-linebot-conversation-history')

def get_today_conversation_count(line_id):
    """
    今日の会話回数を取得
    """
    try:
        # 日本時間で今日の日付を取得
        jst = pytz.timezone('Asia/Tokyo')
        now = datetime.now(jst)
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = now.replace(hour=23, minute=59, second=59, microsecond=999999)

        # ISO形式の文字列に変換
        start_str = today_start.isoformat()
        end_str = today_end.isoformat()

        logger.info(f"検索期間: {start_str} から {end_str}")

        # 今日の会話を取得
        response = conversation_table.query(
            KeyConditionExpression=Key('lineId').eq(line_id) &
                                   Key('timestamp').between(start_str, end_str)
        )

        logger.info(f"DynamoDB応答: {response}")
        logger.info(f"取得された会話数: {len(response['Items'])}")

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
            Limit=limit # ユーザーとアシスタントのメッセージペアを考慮
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