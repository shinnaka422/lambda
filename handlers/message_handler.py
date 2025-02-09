import logging
from utils import chatgpt_api, dynamodb_utils, line_utils, stripe_utils
from linebot.models import TextMessage, FlexSendMessage

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def handle_message(event):
    try:
        user_message = event.message.text
        user_id = event.source.user_id

        daily_count = dynamodb_utils.get_today_conversation_count(user_id)
        logger.info(f"Today's conversation count for user {user_id}: {daily_count}")

        if daily_count >= 30:
            session = stripe_utils.create_stripe_checkout_session(user_id)
            flex_message = line_utils.create_subscription_flex_message(session.url)

            line_utils.reply_message(
                event.reply_token,
                [
                    TextMessage(text="本日の上限に達しました。\n毎日「無料で3通」お使いいただけますので、明日までお待ちください✨\nプレミアムプランに加入すると、引き続きお使いいただけます✨"),
                    flex_message
                ]
            )
            return

        conversation_history = dynamodb_utils.get_conversation_history(user_id)

        line_utils.start_loading(user_id)

        answer = chatgpt_api.get_chatgpt_response(user_message, conversation_history)
        logger.info(f"ChatGPT response: {answer}")

        dynamodb_utils.save_conversation(user_id, user_message, answer)

        line_utils.reply_message(event.reply_token, TextMessage(text=answer))

    except Exception as e:
        logger.error(f"handle_message関数でエラーが発生しました: {e}")
        line_utils.reply_message(
            event.reply_token,
            TextMessage(text="エラーが発生しました。しばらく待ってから再度お試しください。")
        )