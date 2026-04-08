import os
import numpy as np
import pandas as pd
import torch
import joblib
import sqlite3

from data_adapter import load_canonical_iot_csv
from model import LSTMAutoencoder
from preprocessing import preprocess_data


SEQ_LENGTH = 30
FEATURES = 3
CSV_PATHS = [
    "DATA/smart_manufacturing_data.csv",
    "normal_training_data.csv",
    "../iot-simulator/normal_training_data.csv",
]
SQLITE_PATHS = [
    "../backend/data/depin_guard.sqlite3",
    "backend/data/depin_guard.sqlite3",
]
MODEL_PATH = "lstm_autoencoder.pth"
SCALER_PATH = "scaler.save"
THRESHOLD_PATH = "threshold.txt"
TRAINING_SOURCE = os.getenv("TRAINING_SOURCE", "auto").strip().lower()
THRESHOLD_PERCENTILE = float(os.getenv("THRESHOLD_PERCENTILE", "95"))


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


def create_sequences(data, seq_length):
    xs = []
    for i in range(len(data) - seq_length):
        xs.append(data[i : i + seq_length])
    return np.array(xs)


def load_scaled_normal_data():
    df = load_threshold_frame()

    if "pressure" not in df.columns and "power_usage" in df.columns:
        df["pressure"] = df["power_usage"]

    required_columns = ["temperature", "vibration", "pressure"]
    if not all(col in df.columns for col in required_columns):
        raise ValueError("CSV must contain temperature, vibration, pressure columns")

    feature_df = df[required_columns]

    if os.path.exists(SCALER_PATH):
        scaler = joblib.load(SCALER_PATH)
        try:
            scaled_data = scaler.transform(feature_df)
        except ValueError:
            scaled_data = preprocess_data(feature_df.to_dict("records"))
    else:
        scaled_data = preprocess_data(feature_df.to_dict("records"))

    return scaled_data


def load_threshold_frame() -> pd.DataFrame:
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
                print(f"Loading threshold data from SQLite: {sqlite_path} ({len(df)} rows)")
                return df
            print(f"SQLite data exists but not enough rows for threshold sequences: {len(df)}")
        except Exception as exc:
            print(f"SQLite threshold source unavailable ({exc}); falling back to CSV")

    csv_path = find_csv_path()
    print(f"Loading threshold data from CSV: {csv_path}")
    return load_canonical_iot_csv(csv_path)


def main():
    if not os.path.exists(MODEL_PATH):
        raise FileNotFoundError("lstm_autoencoder.pth not found. Run train.py first.")

    scaled_data = load_scaled_normal_data()
    sequences = create_sequences(scaled_data, SEQ_LENGTH)
    if len(sequences) == 0:
        raise ValueError("Not enough rows to create sequences for threshold calculation")

    model = LSTMAutoencoder(input_dim=FEATURES, hidden_dim=64)
    model.load_state_dict(torch.load(MODEL_PATH, map_location="cpu"))
    model.eval()

    inputs = torch.tensor(sequences, dtype=torch.float32)

    with torch.no_grad():
        reconstructions = model(inputs)
        errors = torch.mean((inputs - reconstructions) ** 2, dim=(1, 2)).numpy()

    percentile_error = float(np.percentile(errors, THRESHOLD_PERCENTILE))
    print(f"Calculated Anomaly Threshold (p{THRESHOLD_PERCENTILE:g}): {percentile_error}")

    with open(THRESHOLD_PATH, "w", encoding="utf-8") as f:
        f.write(str(percentile_error))

    print(f"Saved threshold to {THRESHOLD_PATH}")


if __name__ == "__main__":
    main()