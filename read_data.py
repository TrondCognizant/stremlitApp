import streamlit as st
import pandas as pd
from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient
import io
import yfinance as yf
import time
import gc # garbage collection

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


def update_and_save_to_azure(container_name, original_blob_name, batch_size=30, pause_seconds=2):
    credential = DefaultAzureCredential()
    blob_service_client = BlobServiceClient(account_url, credential=credential)
    source_blob_client = blob_service_client.get_blob_client(container=container_name, blob=original_blob_name)

    # --- PHASE 1: Metadata Extraction ---
    st.info("Extracting metadata from source...")
    download_stream = source_blob_client.download_blob()
    
    # Read the file
    df_temp = pd.read_parquet(io.BytesIO(download_stream.readall()))
    
    # Store only what we need (small objects)
    all_tickers = list(set(df_temp.columns.get_level_values(0)))
    start_date = df_temp.index[-1] + pd.to_timedelta(1, 'd')
    column_names = df_temp.columns.names
    end_date = pd.Timestamp.today()
    
    # Drop the big dataframe immediately
    del df_temp
    gc.collect() # Force memory release
    st.success("Source file cleared from memory. Starting download...")

    if start_date >= end_date:
        st.warning("Data is already up to date.")
        return None

    # --- PHASE 2: Batch Download ---
    new_data_chunks = []
    for i in range(0, len(all_tickers), batch_size):
        batch = all_tickers[i:i + batch_size]
        st.write(f"Fetching batch {i//batch_size + 1}...")
        
        try:
            batch_df = yf.download(batch, start=start_date, end=end_date, group_by='ticker')
            if not batch_df.empty:
                new_data_chunks.append(batch_df)
            time.sleep(pause_seconds)
        except Exception as e:
            st.error(f"Error fetching batch: {e}")

    if not new_data_chunks:
        st.error("No new data was downloaded.")
        return None

    # --- PHASE 3: Re-read & Merge ---
    # We re-read the original file ONLY when we are ready to merge and write.
    # This ensures we don't hold the original file in RAM while yfinance is running.
    
    st.info("Re-loading original for final merge...")
    download_stream = source_blob_client.download_blob()
    df_original = pd.read_parquet(io.BytesIO(download_stream.readall()))
    
    df_new = pd.concat(new_data_chunks, axis=1)
    df_new.columns.names = column_names
    
    # Combine
    df_combined = pd.concat([df_original, df_new]).sort_index()
    df_combined.index = df_combined.index.tz_localize(None)
    
    # Clean up intermediate objects
    del df_original
    del df_new
    del new_data_chunks
    gc.collect()

    # --- PHASE 4: Filename Generation & Upload ---
    clean_name = original_blob_name.replace(".parquet", "")
    date_suffix = f"{start_date.strftime('%Y-%m-%d')}_to_{end_date.strftime('%Y-%m-%d')}"
    new_blob_name = f"{clean_name}_{date_suffix}.parquet"

    new_blob_client = blob_service_client.get_blob_client(container=container_name, blob=new_blob_name)
    
    parquet_buffer = io.BytesIO()
    df_combined.to_parquet(parquet_buffer, engine='pyarrow', index=True)
    parquet_buffer.seek(0)
    
    try:
        new_blob_client.upload_blob(parquet_buffer, overwrite=True)
        st.success(f"Saved to {new_blob_name}")
        return df_combined
    except Exception as e:
        st.error(f"Upload failed: {e}")
        return None

