import os
import numpy as np
import pandas as pd
import torch
import joblib

from model import LSTMAutoencoder
from preprocessing import preprocess_data


SEQ_LENGTH = 30
FEATURES = 3
CSV_PATHS = ["normal_training_data.csv", "../iot-simulator/normal_training_data.csv"]
MODEL_PATH = "lstm_autoencoder.pth"
SCALER_PATH = "scaler.save"
THRESHOLD_PATH = "threshold.txt"


def find_csv_path():
    for candidate in CSV_PATHS:
        if os.path.exists(candidate):
            return candidate
    raise FileNotFoundError("normal_training_data.csv not found in expected locations")


def create_sequences(data, seq_length):
    xs = []
    for i in range(len(data) - seq_length):
        xs.append(data[i : i + seq_length])
    return np.array(xs)


def load_scaled_normal_data():
    csv_path = find_csv_path()
    df = pd.read_csv(csv_path)

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

    max_error = float(np.max(errors))
    print(f"Calculated Anomaly Threshold: {max_error}")

    with open(THRESHOLD_PATH, "w", encoding="utf-8") as f:
        f.write(str(max_error))

    print(f"Saved threshold to {THRESHOLD_PATH}")


if __name__ == "__main__":
    main()