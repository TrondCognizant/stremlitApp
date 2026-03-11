
from read_data import load_stock_data
import streamlit as st

st.title("Load Historic Stock Data")
df_loaded = load_stock_data()
all_tickers = list(set(df_loaded.columns.get_level_values(0)))
ticker = st.selectbox(
    "Search and select a stock:",
    all_tickers,
    index=None,         # Starts with nothing selected
    placeholder="Type to search...",
)

st.write(f"You selected: {ticker}")
# ticker = st.text_input("Enter Stock Ticker", value="Select ticker")

if (ticker != "Select ticker"):
    st.write("Preview of Stock Data")
    st.write(df_loaded[ticker.upper()].tail())
    #st.line_chart(df.set_index('Date')['Close'])