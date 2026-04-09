import torch
import torch.nn as nn
import numpy as np
import pandas as pd
import os
import sqlite3

from data_adapter import load_canonical_iot_csv
from model import LSTMAutoencoder
from preprocessing import preprocess_data

SEQ_LENGTH = 30
FEATURES   = 3
EPOCHS     = 50
LR         = 0.001
CSV_PATHS  = [
    "DATA/smart_manufacturing_data.csv",
    "normal_training_data.csv",
    "../iot-simulator/normal_training_data.csv",
]
SQLITE_PATHS = [
    "../backend/data/depin_guard.sqlite3",
    "backend/data/depin_guard.sqlite3",
]
TRAINING_SOURCE = os.getenv("TRAINING_SOURCE", "auto").strip().lower()


def find_csv_path():
    for candidate in CSV_PATHS:
        if os.path.exists(candidate):
            return candidate
    raise FileNotFoundError("normal_training_data.csv not found in expected locations")


def find_sqlite_path():
    for candidate in SQLITE_PATHS:
        if os.path.exists(candidate):
            return candidate
    return None


def load_training_frame() -> pd.DataFrame:
    sqlite_path = find_sqlite_path()
    if sqlite_path and TRAINING_SOURCE in ("auto", "sqlite"):
        try:
            with sqlite3.connect(sqlite_path) as connection:
                df = pd.read_sql_query(
                    """
                    SELECT temp AS temperature, vib AS vibration, pwr AS pressure
                    FROM sensor_readings
                    WHERE temp IS NOT NULL AND vib IS NOT NULL AND pwr IS NOT NULL
                    ORDER BY id ASC
                    """,
                    connection,
                )
            if len(df) > SEQ_LENGTH:
                print(f"Loading training data from SQLite: {sqlite_path} ({len(df)} rows)")
                return df
            print(f"SQLite data exists but not enough rows for LSTM sequences: {len(df)}")
        except Exception as exc:
            print(f"SQLite training source unavailable ({exc}); falling back to CSV")

    csv_path = find_csv_path()
    print(f"Loading training data from CSV: {csv_path}")
    return load_canonical_iot_csv(csv_path)


def create_sequences(data, seq_length):
    return np.array([data[i : i + seq_length] for i in range(len(data) - seq_length)])


def main():
    df = load_training_frame()

    if "pressure" not in df.columns and "power_usage" in df.columns:
        df["pressure"] = df["power_usage"]

    required_columns = ["temperature", "vibration", "pressure"]
    if not all(col in df.columns for col in required_columns):
        raise ValueError("CSV must contain temperature, vibration, pressure columns")

    data_list   = df[required_columns].to_dict("records")
    scaled_data = preprocess_data(data_list)
    X_train     = create_sequences(scaled_data, SEQ_LENGTH)

    if len(X_train) == 0:
        raise ValueError("Not enough rows in CSV to create training sequences")

    X_train_tensor = torch.tensor(X_train, dtype=torch.float32)

    model     = LSTMAutoencoder(input_dim=FEATURES, hidden_dim=64)
    criterion = nn.MSELoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=LR)

    print("Training LSTM autoencoder...")
    model.train()
    for epoch in range(EPOCHS):
        optimizer.zero_grad()
        output = model(X_train_tensor)
        loss   = criterion(output, X_train_tensor)
        loss.backward()
        optimizer.step()

        if (epoch + 1) % 10 == 0:
            print(f"Epoch [{epoch + 1}/{EPOCHS}]  Loss: {loss.item():.6f}")

    torch.save(model.state_dict(), "lstm_autoencoder.pth")
    print("Model weights saved to lstm_autoencoder.pth")


if __name__ == "__main__":
    main()