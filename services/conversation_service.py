import boto3
from datetime import datetime
from boto3.dynamodb.conditions import Key
import logging
logger = logging.getLogger()
dynamodb = boto3.resource('dynamodb')
conversation_table = dynamodb.Table('linebot-conversation-history')
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