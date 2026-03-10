import streamlit as st
import pandas as pd
from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient
import io
import yfinance as yf
import time

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


def update_and_save_to_azure(container_name, blob_name, batch_size=30, pause_seconds=2):
    
    # 1. Initialize Azure Client & Download existing data
    credential = DefaultAzureCredential()
    blob_service_client = BlobServiceClient(account_url, credential=credential)
    blob_client = blob_service_client.get_blob_client(container=container_name, blob=blob_name)

    print(f"Downloading {blob_name} from Azure...")
    download_stream = blob_client.download_blob()
    df = pd.read_parquet(io.BytesIO(download_stream.readall()))

    # 2. Extract unique tickers from MultiIndex columns
    # Your df.columns is likely [(Ticker, Metric), ...]
    all_tickers = list(set(df.columns.get_level_values(0)))
    start_date = df.index[-1] + pd.to_timedelta(1, 'd')
    end_date = pd.Timestamp.today()

    if start_date >= end_date:
        st.warning("Data is already up to date.")
        return df

    # 3. Batch processing to avoid yfinance limits
    new_data_frames = []
    for i in range(0, len(all_tickers), batch_size):
        batch = all_tickers[i:i + batch_size]
        print(f"Fetching batch {i//batch_size + 1}: {len(batch)} tickers...")
        
        try:
            # Download batch
            batch_df = yf.download(batch, start=start_date, end=end_date, group_by='ticker')
            
            if not batch_df.empty:
                # Align MultiIndex to match your storage format (Metric, Ticker) or (Ticker, Metric)
                # yf.download(group_by='ticker') returns (Ticker, Metric)
                new_data_frames.append(batch_df)
            
            # Respectful pause to prevent IP blocking
            time.sleep(pause_seconds)
            
        except Exception as e:
            print(f"Error fetching batch {batch}: {e}")

    # 4. Combine and Merge
    if new_data_frames:
        df_new = pd.concat(new_data_frames, axis=1)
        
        # Ensure the level order matches your original DF
        # If your original is (Ticker, Metric), this matches. 
        # If it's (Metric, Ticker), use df_new.swaplevel(axis=1)
        if df.columns.names != df_new.columns.names:
             df_new.columns.names = df.columns.names

        df_combined = pd.concat([df, df_new]).sort_index()
        # Clean timezone info for Parquet compatibility
        df_combined.index = df_combined.index.tz_localize(None)

        # 5. Save back to Azure
        print("Uploading updated dataframe to Azure...")
        parquet_buffer = io.BytesIO()
        df_combined.to_parquet(parquet_buffer, engine='pyarrow', index=True)
        parquet_buffer.seek(0)
        
        blob_client.upload_blob(parquet_buffer, overwrite=True)
        print("Update successful.")
        return df_combined
    else:
        print("No new data was downloaded.")
        return df

