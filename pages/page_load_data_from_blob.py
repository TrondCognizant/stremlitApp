
from src.read_data import load_stock_data
import streamlit as st
import plotly.graph_objects as go

st.title("Load Historic Stock Data")
df_loaded = load_stock_data()

all_tickers = list(set(df_loaded.columns.get_level_values(0)))
ticker = st.selectbox(
    "Search and select a stock:",
    all_tickers,
    index=None,         # Starts with nothing selected
    placeholder="NVDA",
)


#if (ticker != "Select ticker"):
#    st.write("Preview of Stock Data")
#    st.write(df_loaded[ticker].tail())
    #st.line_chart(df.set_index('Date')['Close'])
interval_days = st.slider("Select the time interval [days]", min_value=5, max_value=300, value=60)      
    
# Fetch data button
#with st.spinner(f'Fetching data for {ticker}...'): 
data = df_loaded[ticker].iloc[-1*interval_days:]
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
    st.plotly_chart(fig, use_container_width=True)
    
    if st.button("Show data frame"):
        # Optional: Show raw data
        st.write(data) 
else:
    st.error("No data found. Please check the ticker symbol.")           
