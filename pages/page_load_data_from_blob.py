
from read_data import load_stock_data
import streamlit as st

st.title("Load Historic Stock Data")
df_loaded = load_stock_data()
ticker="AKSO.OL"

if not df_loaded.empty:
    st.write("Preview of Stock Data")
    st.write(df_loaded[ticker.upper()].tail())
    #st.line_chart(df.set_index('Date')['Close'])