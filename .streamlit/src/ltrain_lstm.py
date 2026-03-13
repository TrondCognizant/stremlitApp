import numpy as np
import pandas as pd
import argparse
import mlflow
import mlflow.keras
import os
import pickle
from keras.models import Sequential
from keras.layers import Dense, LSTM
from helper_functions import create_3D_dataset, summarize_macd_intervals
from read_data import load_stock_data


def train_model(args):
    # 1. Start MLflow Autologging
    # This automatically captures model architecture, optimizer, epochs, and loss metrics
    mlflow.keras.autolog()

    # Create outputs directory if it doesn't exist
    os.makedirs('outputs', exist_ok=True)

    # 2. Data Loading & Prep
    df_data = load_stock_data()
    ticker = args.ticker
    
    df_macd_summary = summarize_macd_intervals(df_data[ticker])
    df_macd_summary_bull = df_macd_summary.query("macd_diff_first > 0")

    features = [
        'duration_cal_days','macd_diff_mean','macd_diff_first','min_value_2diff',
        'min_value_diff','max_value_diff','max_value_2diff','first_return_open_close',
        'first_return_close_open','first_return_close_close','rel_return'
    ]
    
    # Scaling
    series_scaling_vector_bull = df_macd_summary_bull[features].std() / 4
    
    # Save the scaler as an artifact so we can use it during inference/deployment
    scaler_path = "outputs/scaler.pkl"
    with open(scaler_path, "wb") as f:
        pickle.dump(series_scaling_vector_bull, f)
    mlflow.log_artifact(scaler_path)

    # 3. Dataset Creation
    X, Y = create_3D_dataset(
        df_macd_summary_bull[features] / series_scaling_vector_bull, 
        window_lenght=10, 
        target_variable='rel_return'
    )

    nr_samp_train = int(len(Y) * args.train_percentage / 100)
    trainX = X[0:nr_samp_train, :, :]
    trainY = Y[0:nr_samp_train]

    windowLength = trainX.shape[1]
    num_features = trainX.shape[2]

    # 4. Model Architecture
    model = Sequential()
    model.add(LSTM(args.hidden_nodes, input_shape=(windowLength, num_features)))
    model.add(Dense(1))

    model.compile(loss='mean_absolute_error', optimizer='adam')

    # 5. Fitting (MLflow handles the logging of these epochs automatically)
    model.fit(
        trainX, 
        trainY, 
        batch_size=args.batch_size, 
        epochs=args.epochs, 
        verbose=1
    )

    # 6. Save the final model to outputs
    model.save('outputs/lstm_model.h5')

if __name__ == "__main__":
    # Define Argument Parser for Azure ML Command Line
    parser = argparse.ArgumentParser(description="Train LSTM on Stock MACD data")
    
    parser.add_argument("--ticker", type=str, default="NVDA", help="Stock ticker to train on")
    parser.add_argument("--train_percentage", type=int, default=80, help="Percentage of data for training")
    parser.add_argument("--hidden_nodes", type=int, default=5, help="Number of LSTM neurons")
    parser.add_argument("--epochs", type=int, default=20, help="Number of training epochs")
    parser.add_argument("--batch_size", type=int, default=5, help="Batch size for training")

    args = parser.parse_args()

    # Start the Azure ML Run context
    with mlflow.start_run():
        train_model(args)