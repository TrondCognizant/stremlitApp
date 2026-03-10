import streamlit as st
from st_pages import Page, show_pages

# Set page config
st.set_page_config(layout="wide")

st.markdown("### **Homepage of stockdata processing **")
st.info("⬅️ Now you can start navigating the tabs in the left-panel menu")

show_pages([
     Page("page_read_stock_data.py", "Read Data"),
 ])

