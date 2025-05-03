import os
import crawler_module as m
from time import sleep
import pandas as pd
import matplotlib.pyplot as plt
import mpl_finance as mpf
from flask import Flask, request, abort
from linebot.v3 import WebhookHandler
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.messaging import (
    Configuration, ApiClient, MessagingApi, ReplyMessageRequest,
    TextMessage, ImageMessage
)
from linebot.v3.webhooks import MessageEvent, TextMessageContent

app = Flask(__name__)

configuration = Configuration(access_token='YsYMRBHXws+LOIDe1EmNizRNyjA9Y0Rz/+DLKs0XXL5j3rbKyzPou56BHYB6p97c2bCb5Wp4gYTYCqOOEeProv54/e6RBczMXm62qKoA+ErewGWsQZuXMPjVTkWuEJ5YZfnBzBwjiHPmzTOVAG2EIgdB04t89/1O/w1cDnyilFU=')
handler = WebhookHandler('5fcd4f4e01583c44f9bad74a835b3aed')

# 🔁 用戶輸入狀態追蹤
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

from linebot.v3.messaging import PushMessageRequest

# 其他程式碼保持不變

@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    user_id = event.source.user_id
    text = event.message.text.strip()
    
    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)

        # 初始化狀態
        if user_id not in user_states:
            user_states[user_id] = {"step": -1}

        state = user_states[user_id]

        if text == "股票資訊":
            state["step"] = 0
            reply = "請輸入股票代碼"

        elif state["step"] == 0:
            state["symbol"] = text
            state["step"] = 1
            reply = "請輸入起始日期（格式：YYYYMMDD）"

        elif state["step"] == 1:
            if len(text) == 8 and text.isdigit():
                state["start"] = text
                state["step"] = 2
                reply = "請輸入結束日期（格式：YYYYMMDD）"
            else:
                reply = "格式錯誤，請重新輸入起始日期（YYYYMMDD）"

        elif state["step"] == 2:
            if len(text) == 8 and text.isdigit():
                state["end"] = text

                # 儲存到 stock.txt
                with open('stock.txt', 'w') as f:
                    f.write(f"{state['symbol']},{state['start']},{state['end']}")

                # 回覆等待訊息
                line_bot_api.reply_message_with_http_info(
                    ReplyMessageRequest(
                        reply_token=event.reply_token,
                        messages=[TextMessage(text="資料處理中，請稍後...")]
                    )
                )

                # ⏳ 生成圖片並回傳
                stock_symbol, dates = m.get_data()
                all_list = []

                for date in dates:
                    sleep(1)
                    try:
                        crawler_data = m.crawl_data(date, stock_symbol)
                        all_list.append(crawler_data[0])
                        df_columns = crawler_data[1]
                    except Exception as e:
                        print(f"error! {date}: {e}")

                all_df = pd.DataFrame(all_list, columns=df_columns)
                day = all_df["日期"].astype(str)
                openprice = all_df["開盤價"].str.replace(",", "", regex=False).astype(float)
                close = all_df["收盤價"].str.replace(",", "", regex=False).astype(float)
                high = all_df["最高價"].str.replace(",", "", regex=False).astype(float)
                low = all_df["最低價"].str.replace(",", "", regex=False).astype(float)
                volume = all_df["成交股數"].str.replace(",", "").astype(float)
                ma10 = close.rolling(window=10).mean()
                ma30 = close.rolling(window=30).mean()

                fig, (ax, ax2) = plt.subplots(2, 1, sharex=True, figsize=(24, 15), dpi=100)
                plt.rcParams['font.sans-serif'] = ['Microsoft JhengHei']
                ax.set_title(f"{stock_symbol} K 線圖 ({dates[0]} ~ {dates[-1]})")

                mpf.candlestick2_ochl(ax, openprice, close, high, low, width=0.5,
                                      colorup='r', colordown='g', alpha=0.6)
                ax.plot(ma10, label='10日均線')
                ax.plot(ma30, label='30日均線')
                ax.legend(loc="best", fontsize=20)
                ax.grid(True)

                mpf.volume_overlay(ax2, openprice, close, volume,
                                   colorup='r', colordown='g', width=0.5, alpha=0.8)
                ax2.set_xticks(range(0, len(day), 5))
                ax2.set_xticklabels(day[::5])
                ax2.grid(True)

                save_path = "./static/k_line_chart.png"
                os.makedirs("./static", exist_ok=True)
                plt.savefig(save_path, bbox_inches='tight')
                plt.close()

                image_url = request.url_root + "static/k_line_chart.png"
                image_url = image_url.replace("http" , "https")
                app.logger.info("url=" +image_url)
                
                line_bot_api.reply_message(
                    reply_token=event.reply_token,
                    image_message = [ImageMessage(
                    original_content_url=image_url,
                    preview_image_url=image_url
                )]
                )

                # 重設狀態
                user_states[user_id] = {"step": -1}
                return
            else:
                reply = "格式錯誤，請重新輸入結束日期（YYYYMMDD）"

        else:
            reply = "請輸入「股票資訊」來查詢 K 線圖"

        # 回覆文字
        line_bot_api.reply_message_with_http_info(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text=reply)]
            )
        )

if __name__ == "__main__":
    app.run()



