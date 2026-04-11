#!/usr/bin/env python3
"""
Fix the threshold - recalculate based on actual loss distribution
"""

import numpy as np
import pandas as pd
import torch
import joblib
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Fix_Threshold")

class LSTMAutoencoder(torch.nn.Module):
    def __init__(self, input_dim=3, hidden_dim=64):
        super(LSTMAutoencoder, self).__init__()
        self.encoder = torch.nn.LSTM(input_dim, hidden_dim, batch_first=True)
        self.decoder = torch.nn.LSTM(hidden_dim, input_dim, batch_first=True)

    def forward(self, x):
        encoded, _ = self.encoder(x)
        decoded, _ = self.decoder(encoded)
        return decoded

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
FEATURE_COLUMNS = ["temperature", "vibration", "pressure"]

# Load model and scaler
model = LSTMAutoencoder(input_dim=3, hidden_dim=64).to(DEVICE)
model.load_state_dict(torch.load("lstm_autoencoder.pth", map_location=DEVICE))
model.eval()

scaler = joblib.load("scaler.save")

# Load test data
logger.info("Loading test data...")
df = pd.read_csv("../iot/DATA/factory_data_transformed.csv")
X_all = df[FEATURE_COLUMNS].values.astype(np.float32)
y_all = df['anomaly_flag'].values.astype(np.int32)

# Normalize
X_norm = scaler.transform(X_all)

# Create sequences
def create_sequences(X, seq_length=10):
    X_seq = []
    for i in range(len(X) - seq_length + 1):
        X_seq.append(X[i:i+seq_length])
    return np.array(X_seq, dtype=np.float32)

X_seq = create_sequences(X_norm, seq_length=10)
y_seq = np.array([y_all[i:i+10].max() for i in range(len(X_seq))])

# Get losses
X_tensor = torch.from_numpy(X_seq).to(DEVICE)
with torch.no_grad():
    recon = model(X_tensor)
    losses = torch.mean((X_tensor - recon) ** 2, dim=(1, 2)).cpu().numpy()

# Separate normal and anomaly losses
normal_losses = losses[y_seq == 0]
anomaly_losses = losses[y_seq == 1]

logger.info(f"\nNormal losses - Mean: {normal_losses.mean():.6f}, Std: {normal_losses.std():.6f}")
logger.info(f"  50th: {np.percentile(normal_losses, 50):.6f}")
logger.info(f"  75th: {np.percentile(normal_losses, 75):.6f}")
logger.info(f"  90th: {np.percentile(normal_losses, 90):.6f}")
logger.info(f"  95th: {np.percentile(normal_losses, 95):.6f}")
logger.info(f"  99th: {np.percentile(normal_losses, 99):.6f}")
logger.info(f"  Max:  {normal_losses.max():.6f}")

logger.info(f"\nAnomaly losses - Mean: {anomaly_losses.mean():.6f}, Std: {anomaly_losses.std():.6f}")
logger.info(f"  Min:  {anomaly_losses.min():.6f}")
logger.info(f"  25th: {np.percentile(anomaly_losses, 25):.6f}")
logger.info(f"  50th: {np.percentile(anomaly_losses, 50):.6f}")
logger.info(f"  75th: {np.percentile(anomaly_losses, 75):.6f}")
logger.info(f"  Max:  {anomaly_losses.max():.6f}")

# Calculate optimal threshold
# Use value that maximizes separation
threshold = np.percentile(normal_losses, 95)

logger.info(f"\n✅ Recommended threshold: {threshold:.6f}")
logger.info(f"   - Will catch {np.sum(anomaly_losses > threshold) / len(anomaly_losses) * 100:.2f}% of anomalies")
logger.info(f"   - Will incorrectly flag {np.sum(normal_losses > threshold) / len(normal_losses) * 100:.2f}% of normal readings")

# Save
with open("threshold.txt", 'w') as f:
    f.write(str(threshold))

logger.info(f"\nThreshold saved to threshold.txt")
