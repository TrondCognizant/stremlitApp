
from read_data import load_stock_data
import streamlit as st

st.title("Load Historic Stock Data")
df_loaded = load_stock_data()

ticker = st.text_input("Enter Stock Ticker", value="Select")

if (ticker != "Select"):
    st.write("Preview of Stock Data")
    st.write(df_loaded[ticker.upper()].tail())
    #st.line_chart(df.set_index('Date')['Close'])