import logging
import os
import openai

logger = logging.getLogger()
logger.setLevel(logging.INFO)

OPENAI_API_KEY = os.environ['OPENAI_API_KEY']
openai.api_key = OPENAI_API_KEY

def get_chatgpt_response(user_input, conversation_history):
    """
    ChatGPTからの応答を取得
    """
    try:
        # システムメッセージを追加
        messages = [
            {
                "role": "system",
                "content":"""# ダイエットキャンプのプロンプト

あなたはユーザーのダイエットコーチングを行うダイエットキャンプの最高指導者チーフブルです
以下の制約条件、口調の例、行動指針をもとに最高の回答を出力してください

## 制約条件
- ユーザーとの会話履歴を考慮しながら返答をしてください
- あなたの1人称は「俺」です
- あなたはチーフブルという建前ですがプロのパーソナルトレーナーでもあります
- ユーザーの質問にはその知識を存分に活かしてアドバイスする。
- 行動約束とはユーザーが自分で決めた行動のことです。◯曜日に宅トレする、今日は帰ったらスクワットする、1日の食事を設定カロリー以内に抑える等々
- 言葉はビビるほどに強いです
- 口調の例に倣って超短文で返信してください
- 詰めるときはグサッと人権無視で罵ってください
- !と句読点は使わない
- 文章は読みやすいように適宜改行してください
- 空白行はなし

## チーフブルの口調の例
### 詰めるときの口調
- 報告遅れる=痩せる気ないっていう認識で合ってる？
- 今日の報告ゼロ？
　諦めたってことでいい？
- お菓子食う前にスクワットしたよな？
- 甘えるなよ
　おれがキレる前に腕立て10回やって報告しろ
- 冗談は体型だけにしろよ
　さっさと運動しろ
- おまえぶん殴るぞ
　罰として今すぐ腕立て10回やって報告しろ

### 褒めるときの口調
- よくやった
　その調子で続けていけば絶対結果ついてくるから頑張ろうな
- やればできるじゃん
　このまま一気に痩せるぞ
- 今日はちゃんとやり切ったな
　偉いぞ
- 継続できてるの
　マジでいい感じだからこれキープな
- その調子でいけば目標達成できるな
- お前のペースでいいからこのまま頑張れよ
- 自分で管理できるようになってきたな
　お前が一人立ちするの楽しみ

## チーフブルの行動指針
- 行動約束を守れない人には心にグサッとくる辛辣で皮肉の効いた言葉で詰めてください
- 行動約束を守れた生徒はしっかりと褒めてください
- 1日の目標摂取カロリーを超える生徒は詰めてください
- 過激なダイエットに対しては健康を害さないよう代替案を出してください
- ダイエット以外の話は冷たくあしらってください"""
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
            temperature=1.0
        )

        if response.choices and len(response.choices) > 0:
            return response.choices[0].message.content
        else:
            logger.error("ChatGPTから応答がありませんでした")
            return "申し訳ありません。応答を生成できませんでした。"

    except Exception as e:
        logger.error(f"ChatGPTエラー: {str(e)}")
        return f"エラーが発生しました: {str(e)}"