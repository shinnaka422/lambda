import requests
import logging
logger = logging.getLogger()
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