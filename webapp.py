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

# Define time range (Previous Month)
end_date = datetime.now()
interval_days  = 20
start_date = end_date - timedelta(days=interval_days)

# Fetch data button
if st.sidebar.button("Fetch Data"):
    with st.spinner(f'Fetching data for {ticker}...'):
        try:
            # Download data
            data = yf.download(ticker, start=start_date, end=end_date)
            
            if not data.empty:
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
                st.plotly_chart(fig)#, use_container_width=True, render_mode="svg")
                
                # Optional: Show raw data
                with st.expander("View Raw Data"):
                    st.write(data)
                    
            else:
                st.error("No data found. Please check the ticker symbol.")
                
        except Exception as e:
            st.error(f"An error occurred: {e}")

else:
    st.info("Enter a ticker in the sidebar and click 'Fetch Data'.")
