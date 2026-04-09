import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
import joblib


SENSOR_FEATURES = ("temperature", "vibration", "pressure")


def canonicalize_sensor_frame(data):
    """
    Convert a sensor payload list or DataFrame into the canonical 3-feature frame.

    The LSTM pipeline expects temperature, vibration, and pressure. If the
    upstream source only provides power_usage, it is mapped into pressure.
    """
    if isinstance(data, pd.DataFrame):
        frame = data.copy()
    else:
        frame = pd.DataFrame(data)

    if "pressure" not in frame.columns and "power_usage" in frame.columns:
        frame["pressure"] = frame["power_usage"]

    missing = [column for column in SENSOR_FEATURES if column not in frame.columns]
    if missing:
        raise ValueError(f"Missing required feature column(s): {', '.join(missing)}")

    return frame.loc[:, SENSOR_FEATURES]


def preprocess_data(data_list):
    """
    Takes a list of sensor reading dicts and returns normalized (0-1) data
    ready for the LSTM model. Also saves the fitted scaler to disk.

    Args:
        data_list: list of dicts with keys temperature, vibration, pressure

    Returns:
        scaled_data: numpy array of shape (n_samples, 3)
    """
    features = canonicalize_sensor_frame(data_list)

    scaler      = MinMaxScaler()
    scaled_data = scaler.fit_transform(features)

    joblib.dump(scaler, 'scaler.save')
    return scaled_data


def get_preprocessed_data(df, seq_length=30):
    """
    Scales sensor data and builds sliding-window sequences for the LSTM.

    Args:
        df:         DataFrame with temperature, vibration, and pressure columns
        seq_length: number of timesteps per sequence

    Returns:
        (sequences, scaler)
    """
    features    = canonicalize_sensor_frame(df)
    scaler      = MinMaxScaler()
    data_scaled = scaler.fit_transform(features)

    xs = []
    for i in range(len(data_scaled) - seq_length):
        xs.append(data_scaled[i : i + seq_length])

    return np.array(xs), scaler