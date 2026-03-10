import streamlit as st

# Set page config
st.set_page_config(layout="wide")

st.markdown("### **Homepage of stockdata processing **")
st.info("⬅️ Now you can start navigating the tabs in the left-panel menu")

read_write_data = st.Page("page_read_stock_data.py", title="Get Data")

# pg = st.navigation([read_write_data])
pg = st.navigation(
    {
        "Get Stock Data": [read_write_data]
    }
)
pg.run()


