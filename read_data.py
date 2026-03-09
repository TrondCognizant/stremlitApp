import streamlit as st
import pandas as pd
from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient
import io


# Setup connection (Use environment variables for production!)
account_url = "https://genaitraining68696287510.blob.core.windows.net"
container_name = "stock-data"
blob_name = "Etoro_2000_14mar2025.parquet" # Or prices.csv

@st.cache_data
def load_stock_data():
    try:
        # Authenticate using Managed Identity (if deployed) or Azure CLI (locally)
        credential = DefaultAzureCredential()
        blob_service_client = BlobServiceClient(account_url, credential=credential)
        blob_client = blob_service_client.get_blob_client(container=container_name, blob=blob_name)

        # Download blob data into memory
        download_stream = blob_client.download_blob()
        data = download_stream.readall()
        
        # Load into DataFrame (change to pd.read_csv if using CSV)
        df = pd.read_parquet(io.BytesIO(data))
        return df
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return pd.DataFrame()


# Key Takeaways for your Job Prep:
# Parquet is the "Gold Standard": In an MLOps role (like the one you shared), using Parquet shows you understand efficient data storage.

# st.cache_data is Vital: Streamlit reruns the whole script on every interaction. If you don't use this decorator, your app will download the file from Azure every single time a user clicks a button, which is slow and expensive.

# Security: Using DefaultAzureCredential is the industry standard. It will automatically find your credentials if you are logged in via Azure CLI locally, or use a Managed Identity if the app is running in Azure.

# Would you like me to help you set up the Environment Variables in your Azure Web App so your Streamlit code can connect to the storage safely?

