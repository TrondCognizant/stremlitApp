import streamlit as st

# Set page config
#st.set_page_config(layout="wide")

#st.markdown("### **Homepage of stockdata processing **")
#st.info("⬅️ Now you can start navigating the tabs in the left-panel menu")

get_data_from_blob = st.Page("pages/page_load_data_from_blob.py")
get_live_data = st.Page("pages/page_read_stock_data.py")


# pg = st.navigation([read_write_data])
pg = st.navigation(
    {
        "Get Data": [get_data_from_blob, get_live_data]
    }
)
pg.run()


