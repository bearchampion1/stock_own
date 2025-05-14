import os
from flask import Flask, request, abort
import yfinance as yf
import mplfinance as mpf
from dotenv import load_dotenv

from linebot.v3 import WebhookHandler
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.messaging import (
    Configuration, ApiClient, MessagingApi,
    ReplyMessageRequest, PushMessageRequest,
    TextMessage, ImageMessage
)
from linebot.v3.webhooks import MessageEvent, TextMessageContent

# ✅ 載入 .env 檔案
load_dotenv("id.env")
CHANNEL_SECRET = os.getenv.__get__("CHANNEL_SECRET")
CHANNEL_ACCESS_TOKEN = os.getenv.__get__("CHANNEL_ACCESS_TOKEN")

app = Flask(__name__)
configuration = Configuration(access_token=CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(CHANNEL_SECRET)

# 🔁 使用者狀態追蹤
user_states = {}

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    user_id = event.source.user_id
    text = event.message.text.strip()

    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)

        if user_id not in user_states:
            user_states[user_id] = {"step": -1}

        state = user_states[user_id]

        if text == "股票資訊":
            state["step"] = 0
            reply = "請輸入股票代碼（如 2330 或 AAPL）"

        elif state["step"] == 0:
            state["symbol"] = text.upper()
            state["step"] = 1
            reply = "請輸入起始日期（格式：YYYY-MM-DD）"

        elif state["step"] == 1:
            state["start"] = text
            state["step"] = 2
            reply = "請輸入結束日期（格式：YYYY-MM-DD）"

        elif state["step"] == 2:
            state["end"] = text

            # ⏳ 資料處理中訊息
            line_bot_api.push_message(
                PushMessageRequest(
                    to=user_id,
                    messages=[TextMessage(text="資料處理中，請稍後...")]
                )
            )

            symbol = state['symbol']
            if symbol.isdigit():
                symbol += ".TW"

            try:
                df = yf.download(symbol, start=state['start'], end=state['end'])
                if df.empty:
                    reply = "查無資料，請確認代碼與日期範圍。"
                else:
                    # 📈 繪圖與儲存圖片
                    os.makedirs("./static", exist_ok=True)
                    save_path = "./static/k_line_chart.jpg"

                    mpf.plot(
                        df,
                        type='candle',
                        mav=(10, 30),
                        volume=True,
                        style='charles',
                        title=f"{symbol} K 線圖",
                        ylabel='價格',
                        ylabel_lower='成交量',
                        savefig=save_path
                    )

                    image_url = request.url_root + "static/k_line_chart.jpg"
                    image_url = image_url.replace("http", "https")

                    image_message = ImageMessage(
                        original_content_url=image_url,
                        preview_image_url=image_url
                    )

                    line_bot_api.push_message(
                        PushMessageRequest(
                            to=user_id,
                            messages=[image_message]
                        )
                    )

                    user_states[user_id] = {"step": -1}
                    return

            except Exception as e:
                print("Error:", e)
                reply = "發生錯誤，請稍後再試或確認輸入是否正確。"

        else:
            reply = "請輸入「股票資訊」來查詢 K 線圖"

        # 📩 回覆文字訊息
        line_bot_api.reply_message(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text=reply)]
            )
        )

if __name__ == "__main__":
    app.run()
