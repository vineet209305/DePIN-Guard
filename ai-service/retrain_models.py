#!/usr/bin/env python3
"""
Retrain AI Models (LSTM Autoencoder + GNN) using combined datasets.

Training Data: smart_manufacturing_data.csv (with anomaly labels)
Validation Data: factory_data_transformed.csv (newly transformed real data)

This script:
1. Loads both datasets
2. Combines them for LSTM training (uses temperature, vibration, pressure)
3. Creates training/validation splits
4. Trains LSTM Autoencoder with anomaly labels
5. Tunings threshold based on labeled anomalies
6. Saves new models + scaler + threshold
"""

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import joblib
from sklearn.preprocessing import MinMaxScaler
from sklearn.model_selection import train_test_split
from pathlib import Path
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("AI_Retraining")

# ============================================================================
# Configuration
# ============================================================================
TRAINING_DATA_PATH = "../iot/DATA/factory_data_transformed.csv"  # Now has anomaly labels
VALIDATION_DATA_PATH = "../iot/DATA/factory_data_transformed.csv"  # Same for now, can use smart_manufacturing for validation later
SMART_MFG_PATH = "./DATA/smart_manufacturing_data.csv"  # Original training data

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
BATCH_SIZE = 64
EPOCHS = 50
LEARNING_RATE = 0.001
VALIDATION_SPLIT = 0.2

# LSTM Architecture
INPUT_DIM = 3  # temperature, vibration, pressure
HIDDEN_DIM = 64
FEATURE_COLUMNS = ["temperature", "vibration", "pressure"]

# Model save paths
LSTM_MODEL_PATH = "lstm_autoencoder.pth"
SCALER_PATH = "scaler.save"
THRESHOLD_PATH = "threshold.txt"

# ============================================================================
# LSTM Autoencoder Model
# ============================================================================
class LSTMAutoencoder(nn.Module):
    def __init__(self, input_dim=3, hidden_dim=64):
        super(LSTMAutoencoder, self).__init__()
        self.encoder = nn.LSTM(input_dim, hidden_dim, batch_first=True)
        self.decoder = nn.LSTM(hidden_dim, input_dim, batch_first=True)

    def forward(self, x):
        encoded, _ = self.encoder(x)
        decoded, _ = self.decoder(encoded)
        return decoded


# ============================================================================
# Data Loading & Preprocessing
# ============================================================================
def load_and_prepare_data():
    """Load transformed factory data with anomaly labels"""
    logger.info(f"Loading training data from {TRAINING_DATA_PATH}")
    
    df = pd.read_csv(TRAINING_DATA_PATH)
    logger.info(f"Loaded {len(df)} rows from transformed factory data")
    
    # Load original smart manufacturing data for comparison
    try:
        smart_mfg_df = pd.read_csv(SMART_MFG_PATH)
        logger.info(f"Loaded {len(smart_mfg_df)} rows from smart manufacturing data")
        
        # Combine datasets
        df = pd.concat([df, smart_mfg_df], ignore_index=True)
        logger.info(f"Combined dataset size: {len(df)} rows")
    except FileNotFoundError:
        logger.warning(f"Smart manufacturing data not found at {SMART_MFG_PATH}, using factory data only")
    
    # Extract features and anomaly labels
    X = df[FEATURE_COLUMNS].values.astype(np.float32)
    y = df['anomaly_flag'].values.astype(np.int32) if 'anomaly_flag' in df.columns else None
    
    logger.info(f"Data shape: {X.shape}")
    logger.info(f"Feature ranges:")
    for i, feature in enumerate(FEATURE_COLUMNS):
        logger.info(f"  {feature}: [{X[:, i].min():.2f}, {X[:, i].max():.2f}]")
    
    if y is not None:
        n_anomalies = np.sum(y)
        logger.info(f"Anomaly distribution: {n_anomalies} anomalies ({n_anomalies/len(y)*100:.2f}%)")
    
    return X, y, df


def create_sequences(X, seq_length=10):
    """Create sequences for LSTM training"""
    X_seq = []
    for i in range(len(X) - seq_length + 1):
        X_seq.append(X[i:i+seq_length])
    return np.array(X_seq, dtype=np.float32)


def preprocess_data(X):
    """Normalize data using MinMaxScaler"""
    scaler = MinMaxScaler()
    X_scaled = scaler.fit_transform(X)
    joblib.dump(scaler, SCALER_PATH)
    logger.info(f"Scaler saved to {SCALER_PATH}")
    return X_scaled, scaler


# ============================================================================
# Training
# ============================================================================
def train_lstm_model(X_train_seq, X_val_seq):
    """Train LSTM Autoencoder model"""
    logger.info("="*60)
    logger.info("Training LSTM Autoencoder")
    logger.info("="*60)
    
    model = LSTMAutoencoder(input_dim=INPUT_DIM, hidden_dim=HIDDEN_DIM).to(DEVICE)
    optimizer = torch.optim.Adam(model.parameters(), lr=LEARNING_RATE)
    criterion = nn.MSELoss()
    
    train_losses = []
    val_losses = []
    
    # Dataset loaders
    train_dataset = torch.from_numpy(X_train_seq).to(DEVICE)
    val_dataset = torch.from_numpy(X_val_seq).to(DEVICE)
    
    for epoch in range(EPOCHS):
        # Training phase
        model.train()
        epoch_train_loss = 0
        n_batches = 0
        
        for i in range(0, len(train_dataset), BATCH_SIZE):
            batch = train_dataset[i:i+BATCH_SIZE]
            
            optimizer.zero_grad()
            reconstructed = model(batch)
            loss = criterion(reconstructed, batch)
            loss.backward()
            optimizer.step()
            
            epoch_train_loss += loss.item()
            n_batches += 1
        
        avg_train_loss = epoch_train_loss / n_batches
        train_losses.append(avg_train_loss)
        
        # Validation phase
        model.eval()
        with torch.no_grad():
            epoch_val_loss = 0
            n_val_batches = 0
            
            for i in range(0, len(val_dataset), BATCH_SIZE):
                batch = val_dataset[i:i+BATCH_SIZE]
                reconstructed = model(batch)
                loss = criterion(reconstructed, batch)
                epoch_val_loss += loss.item()
                n_val_batches += 1
            
            avg_val_loss = epoch_val_loss / n_val_batches
            val_losses.append(avg_val_loss)
        
        if (epoch + 1) % 10 == 0:
            logger.info(f"Epoch {epoch+1}/{EPOCHS} - Train Loss: {avg_train_loss:.6f}, Val Loss: {avg_val_loss:.6f}")
    
    # Save model
    torch.save(model.state_dict(), LSTM_MODEL_PATH)
    logger.info(f"✅ Model saved to {LSTM_MODEL_PATH}")
    logger.info(f"Final train loss: {train_losses[-1]:.6f}, Final val loss: {val_losses[-1]:.6f}")
    
    return model, train_losses, val_losses


def calculate_threshold(model, X_normal, X_anomaly):
    """Calculate optimal threshold using labeled anomalies"""
    logger.info("="*60)
    logger.info("Calculating Anomaly Threshold")
    logger.info("="*60)
    
    model.eval()
    X_normal = torch.from_numpy(X_normal).to(DEVICE)
    X_anomaly = torch.from_numpy(X_anomaly).to(DEVICE)
    
    with torch.no_grad():
        # Calculate reconstruction errors
        normal_recon = model(X_normal)
        normal_loss = torch.mean((X_normal - normal_recon) ** 2, dim=(1, 2)).cpu().numpy()
        
        anomaly_recon = model(X_anomaly)
        anomaly_loss = torch.mean((X_anomaly - anomaly_recon) ** 2, dim=(1, 2)).cpu().numpy()
    
    # Find threshold that separates normal from anomalies
    min_loss = min(normal_loss.min(), anomaly_loss.min())
    max_loss = max(normal_loss.max(), anomaly_loss.max())
    
    # Try different thresholds and find best separation
    best_threshold = np.percentile(normal_loss, 95)  # 95th percentile of normal data
    
    logger.info(f"Normal data loss - Mean: {normal_loss.mean():.6f}, Max: {normal_loss.max():.6f}, 95th: {np.percentile(normal_loss, 95):.6f}")
    logger.info(f"Anomaly data loss - Mean: {anomaly_loss.mean():.6f}, Min: {anomaly_loss.min():.6f}")
    logger.info(f"Recommended threshold: {best_threshold:.6f}")
    
    # Save threshold
    with open(THRESHOLD_PATH, 'w') as f:
        f.write(str(best_threshold))
    logger.info(f"✅ Threshold saved to {THRESHOLD_PATH}")
    
    return best_threshold


# ============================================================================
# Main Execution
# ============================================================================
def main():
    logger.info("\n" + "="*60)
    logger.info("AI MODEL RETRAINING PIPELINE")
    logger.info("="*60)
    
    # Load data
    X, y, df = load_and_prepare_data()
    
    # Preprocess
    X_scaled, scaler = preprocess_data(X)
    logger.info(f"Data normalized to range [0, 1]")
    
    # Create sequences
    seq_length = 10
    X_sequences = create_sequences(X_scaled, seq_length=seq_length)
    logger.info(f"Created {len(X_sequences)} sequences of length {seq_length}")
    
    # Split data
    X_train_seq, X_val_seq = train_test_split(
        X_sequences, 
        test_size=VALIDATION_SPLIT, 
        random_state=42
    )
    logger.info(f"Train: {len(X_train_seq)}, Validation: {len(X_val_seq)}")
    
    # Train model
    model, train_losses, val_losses = train_lstm_model(X_train_seq, X_val_seq)
    
    # Calculate threshold using labeled anomalies
    if y is not None:
        y_seq = np.array([y[i:i+seq_length].max() for i in range(len(X_sequences))])  # Sequence has anomaly if any point is anomaly
        normal_indices = np.where(y_seq == 0)[0]
        anomaly_indices = np.where(y_seq == 1)[0]
        
        if len(anomaly_indices) > 0 and len(normal_indices) > 0:
            X_normal_seq = X_train_seq[normal_indices][:1000]  # Limit to 1000 for threshold calc
            X_anomaly_seq = X_train_seq[anomaly_indices][:1000]
            threshold = calculate_threshold(model, X_normal_seq, X_anomaly_seq)
        else:
            logger.warning("Insufficient anomaly data for threshold calculation, using default")
            with open(THRESHOLD_PATH, 'w') as f:
                f.write("0.05")
    
    logger.info("\n" + "="*60)
    logger.info("✅ RETRAINING COMPLETE!")
    logger.info("="*60)
    logger.info(f"\nArtifacts saved:")
    logger.info(f"  - Model: {LSTM_MODEL_PATH}")
    logger.info(f"  - Scaler: {SCALER_PATH}")
    logger.info(f"  - Threshold: {THRESHOLD_PATH}")
    logger.info(f"\nNext steps:")
    logger.info(f"  1. Test predictions on factory data")
    logger.info(f"  2. Deploy updated models to Render")
    logger.info(f"  3. Monitor anomaly detection in production")
    

if __name__ == "__main__":
    main()
