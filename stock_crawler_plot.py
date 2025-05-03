import matplotlib.pyplot as plt
import crawler_module as m
from time import sleep
import pandas as pd
import mpl_finance as mpf
import os

all_list = []
stock_symbol, dates = m.get_data()

for date in dates:
    sleep(2)
    try:
        crawler_data = m.crawl_data(date, stock_symbol)
        all_list.append(crawler_data[0])
        df_columns = crawler_data[1]
        print("  OK!  date = " + date + " ,stock symbol = " + stock_symbol)
    except:
        print("error! date = " + date + " ,stock symbol = " + stock_symbol)

all_df = pd.DataFrame(all_list, columns=df_columns)

# step 1 prepare data
day = all_df["日期"].astype(str)
openprice = all_df["開盤價"].str.replace(",", "", regex=False).astype(float)
close = all_df["收盤價"].str.replace(",", "", regex=False).astype(float)
high = all_df["最高價"].str.replace(",", "", regex=False).astype(float)
low = all_df["最低價"].str.replace(",", "", regex=False).astype(float)
volume = all_df["成交股數"].str.replace(',', '').astype(float)

# 計算移動平均線（使用 pandas）
ma10 = close.rolling(window=10).mean()
ma30 = close.rolling(window=30).mean()

# step 2 create plot
fig, (ax, ax2) = plt.subplots(2, 1, sharex=True, figsize=(24, 15), dpi=100)
plt.rcParams['font.sans-serif'] = ['Microsoft JhengHei']
ax.set_title(stock_symbol + "  K 線圖 ( " + dates[0] + " ~ " + dates[-1] + " )")

# step 3 plot 子圖(ax)
mpf.candlestick2_ochl(ax, openprice, close, high, low, width=0.5,
                      colorup='r', colordown='g', alpha=0.6)
ax.plot(ma10, label='10日均線')
ax.plot(ma30, label='30日均線')
ax.legend(loc="best", fontsize=20)
ax.grid(True)

# step 3 plot 子圖(ax2)
mpf.volume_overlay(ax2, openprice, close, volume, colorup='r',
                   colordown='g', width=0.5, alpha=0.8)
ax2.set_xticks(range(0, len(day), 5))
ax2.set_xticklabels(day[::5])
ax2.grid(True)

# step 4 show plot
def runnig(save_dir="./static", filename="k_line_chart.png"):
    os.makedirs(save_dir, exist_ok=True)
    save_path = os.path.join(save_dir, filename)
    plt.savefig(save_path, bbox_inches='tight')
    plt.show()
    return save_path


runnig()
