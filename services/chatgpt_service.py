import openai
import logging
logger = logging.getLogger()
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