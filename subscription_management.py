import stripe

# Stripeのシークレットキーを設定
stripe.api_key = "sk_test_51QL11y2M1XKafECjbo7lMVKZaXU1Oo1buQ0bkFlYpcFZO2eLfRWyiHGPaVcdqpmPltJyIStHD93RX7js0ldAunta00Lv4FXUfF"

# Checkoutセッションを作成
session = stripe.checkout.Session.create(
    payment_method_types=["card"],
    line_items=[
        {
            "price": "price_1Qnga52M1XKafECj1TnzYuWt",  # カタログに登録された商品IDを使用
            "quantity": 1,
        }
    ],
    mode="subscription",
    success_url="https://example.com/success",
    metadata={"lineId": "U7276b9f6fa044542dcab01f7b58f7ddc"},
)

# 生成されたURLを出力
print(session.url)