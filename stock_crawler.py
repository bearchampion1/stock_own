import crawler_module as m
from time import sleep
import pandas as pd

all_list = []
stock_symbol, dates = m.get_data()

for date in dates:
    sleep(1)
    try:
        crawler_data = m.crawl_data(date, stock_symbol)
        all_list.append(crawler_data[0])
        df_columns = crawler_data[0]
        print("  OK!  date = " + date + " ,stock symbol = " + stock_symbol)
    except:
        print("error! date = " + date + " ,stock symbol = " + stock_symbol)

all_df = pd.DataFrame(all_list, columns=df_columns)
print(all_df)
