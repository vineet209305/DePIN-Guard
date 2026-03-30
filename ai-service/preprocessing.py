import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
import joblib


def preprocess_data(data_list):
    """
    Takes a list of sensor reading dicts and returns normalized (0-1) data
    ready for the LSTM model. Also saves the fitted scaler to disk.

    Args:
        data_list: list of dicts with keys temperature, vibration, pressure

    Returns:
        scaled_data: numpy array of shape (n_samples, 3)
    """
    df = pd.DataFrame(data_list)
    features = df[['temperature', 'vibration', 'pressure']]

    scaler      = MinMaxScaler()
    scaled_data = scaler.fit_transform(features)

    joblib.dump(scaler, 'scaler.save')
    return scaled_data


def get_preprocessed_data(df, seq_length=30):
    """
    Scales sensor data and builds sliding-window sequences for the LSTM.

    Args:
        df:         DataFrame with temperature and vibration columns
        seq_length: number of timesteps per sequence

    Returns:
        (sequences, scaler)
    """
    features    = ['temperature', 'vibration']
    scaler      = MinMaxScaler()
    data_scaled = scaler.fit_transform(df[features])

    xs = []
    for i in range(len(data_scaled) - seq_length):
        xs.append(data_scaled[i : i + seq_length])

    return np.array(xs), scaler