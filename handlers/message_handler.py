import logging
from services.chatgpt_service import get_chatgpt_response
from services.conversation_service import get_conversation_history, save_conversation
from services.loading_service import start_loading
from linebot.models import MessageEvent, TextMessage, TextSendMessage

logger = logging.getLogger()

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