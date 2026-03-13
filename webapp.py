import streamlit as st
import sys
import os

# Get the absolute path of the directory containing this file
root_path = os.path.abspath(os.path.dirname(__file__))
st.write(f"root path: {root_path}")
# Add it to sys.path if it's not already there
if root_path not in sys.path:
    st.write(f"{root_path} wa not in the system paths, but is now added")
    sys.path.append(root_path)

# Set page config
#st.set_page_config(layout="wide")

#st.markdown("### **Homepage of stockdata processing **")
#st.info("⬅️ Now you can start navigating the tabs in the left-panel menu")

get_data_from_blob = st.Page("pages/page_load_data_from_blob.py", title="Load data from blob")
get_live_data = st.Page("pages/page_read_stock_data.py", title="Download live data")
update_blob_data = st.Page("pages/page_update_data_on_blob.py", title="Download and update blob data")
train_ml_model = st.Page("pages/page_train_ml_model.py", title="Train ML model on Cloud")

# pg = st.navigation([read_write_data])
pg = st.navigation(
    {

        "Get Data": [get_data_from_blob, get_live_data, update_blob_data, train_ml_model]
    }
)
pg.run()


