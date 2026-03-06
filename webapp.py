import re

import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
from datetime import datetime, timedelta


# Set page config
st.set_page_config(layout="wide")

st.title("📈 Previous Month Stock Price Candlestick Chart")

# Sidebar for user input
st.sidebar.header("User Input")
ticker = st.sidebar.text_input("Enter Stock Ticker", value="AAPL")

# Choose interval length
max_value=60
end_date = datetime.now()
start_date = end_date - timedelta(days=max_value)

try:
    # Download data
    data_full = yf.download(ticker, start=start_date, end=end_date).swaplevel(axis='columns')[ticker]
except Exception as e:
    st.error(f"An error occurred: {e}")
    


interval_days = st.slider("Select the time interval (days]", min_value=5, max_value=max_value, value=30)
data = data_full.iloc[-1*interval_days:]
    
# Fetch data button
if st.sidebar.button("Fetch Data"):
    with st.expander("View Raw Data"):       
        if not data_full.empty:
            st.subheader(f"{ticker.upper()} - Last {interval_days} Days")
            
            # Create Candlestick chart
            fig = go.Figure(data=[go.Candlestick(
                x=data.index,
                open=data['Open'],
                high=data['High'],
                low=data['Low'],
                close=data['Close'],
                name=ticker
            )])
            
            # Customize layout
            fig.update_layout(
                title=f"{ticker.upper()} Price (Previous Month)",
                yaxis_title="Price (USD)",
                xaxis_title="Date",
                xaxis_rangeslider_visible=False,
                template="plotly_dark",
                height=600
            )
            
            # Show plot
            st.plotly_chart(fig, use_container_width=True)
    
         # Optional: Show raw data
            st.write(data)

        
        else:
            st.error("No data found. Please check the ticker symbol.")           
else:
    st.info("Enter a ticker in the sidebar and click 'Fetch Data'.")
