from read_data import update_and_save_to_azure
import streamlit as st

# Setup connection (Use environment variables for production!)
account_url = "https://genaitraining68696287510.blob.core.windows.net"
container_name = "stock-data"
blob_name = "Etoro_2000_14mar2025.parquet" # Or prices.csv


st.title("Load and Update Historic Stock Data")
if st.button("Start stock date update"):
    update_and_save_to_azure(container_name, blob_name, batch_size=30, pause_seconds=2)

