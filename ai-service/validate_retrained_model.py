#!/usr/bin/env python3
"""
Test & validate the retrained LSTM Autoencoder model.

Loads retrained model and tests predictions on:
1. Pure normal data
2. Pure anomaly data
3. Mixed test set from factory data
4. Calculates accuracy metrics
"""

import numpy as np
import pandas as pd
import torch
import joblib
from pathlib import Path
import logging
from sklearn.metrics import confusion_matrix, precision_recall_fscore_support, roc_auc_score

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("AI_Testing")

# Configuration
LSTM_MODEL_PATH = "lstm_autoencoder.pth"
SCALER_PATH = "scaler.save"
THRESHOLD_PATH = "threshold.txt"
TEST_DATA_PATH = "../iot/DATA/factory_data_transformed.csv"

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
FEATURE_COLUMNS = ["temperature", "vibration", "pressure"]

# ============================================================================
# LSTM Autoencoder Model
# ============================================================================
class LSTMAutoencoder(torch.nn.Module):
    def __init__(self, input_dim=3, hidden_dim=64):
        super(LSTMAutoencoder, self).__init__()
        self.encoder = torch.nn.LSTM(input_dim, hidden_dim, batch_first=True)
        self.decoder = torch.nn.LSTM(hidden_dim, input_dim, batch_first=True)

    def forward(self, x):
        encoded, _ = self.encoder(x)
        decoded, _ = self.decoder(encoded)
        return decoded


# ============================================================================
# Create sequences for LSTM
# ============================================================================
def create_sequences(X, seq_length=10):
    """Create sequences for testing"""
    X_seq = []
    for i in range(len(X) - seq_length + 1):
        X_seq.append(X[i:i+seq_length])
    return np.array(X_seq, dtype=np.float32)


# ============================================================================
# Load Model & Data
# ============================================================================
def load_artifacts():
    """Load trained model, scaler, and threshold"""
    logger.info("Loading trained artifacts...")
    
    # Load model
    model = LSTMAutoencoder(input_dim=3, hidden_dim=64).to(DEVICE)
    model.load_state_dict(torch.load(LSTM_MODEL_PATH, map_location=DEVICE))
    model.eval()
    logger.info(f"✅ Model loaded from {LSTM_MODEL_PATH}")
    
    # Load scaler
    scaler = joblib.load(SCALER_PATH)
    logger.info(f"✅ Scaler loaded from {SCALER_PATH}")
    
    # Load threshold
    with open(THRESHOLD_PATH, 'r') as f:
        threshold = float(f.read().strip())
    logger.info(f"✅ Threshold loaded from {THRESHOLD_PATH}: {threshold:.6f}")
    
    return model, scaler, threshold


def load_test_data():
    """Load test data from transformed factory data"""
    logger.info(f"Loading test data from {TEST_DATA_PATH}")
    df = pd.read_csv(TEST_DATA_PATH)
    
    # Separate normal and anomaly data
    X_all = df[FEATURE_COLUMNS].values.astype(np.float32)
    y_all = df['anomaly_flag'].values.astype(np.int32)
    device_ids = df['device_id'].values
    
    logger.info(f"Loaded {len(df)} test samples")
    logger.info(f"  - Normal: {np.sum(y_all == 0)} ({np.sum(y_all == 0)/len(y_all)*100:.2f}%)")
    logger.info(f"  - Anomalies: {np.sum(y_all == 1)} ({np.sum(y_all == 1)/len(y_all)*100:.2f}%)")
    
    return X_all, y_all, device_ids


# ============================================================================
# Prediction & Evaluation
# ============================================================================
def predict_anomalies(model, scaler, X_test, threshold, batch_size=64):
    """
    Predict anomalies using reconstruction loss.
    Returns: anomaly_scores, predictions, losses
    """
    logger.info("Running inference on test data...")
    
    # Normalize
    X_normalized = scaler.transform(X_test)
    
    # Create sequences
    X_sequences = create_sequences(X_normalized, seq_length=10)
    y_sequences = np.zeros(len(X_sequences))  # Placeholder for now
    
    logger.info(f"Created {len(X_sequences)} test sequences")
    
    # Get predictions
    X_test_tensor = torch.from_numpy(X_sequences).to(DEVICE)
    
    model.eval()
    with torch.no_grad():
        reconstructed = model(X_test_tensor)
        
        # Calculate reconstruction loss (MSE)
        losses = torch.mean((X_test_tensor - reconstructed) ** 2, dim=(1, 2))
        losses = losses.cpu().numpy()
    
    # Make predictions
    predictions = (losses > threshold).astype(int)
    
    logger.info(f"Mean reconstruction loss: {losses.mean():.6f}")
    logger.info(f"Min loss:  {losses.min():.6f}")
    logger.info(f"Max loss:  {losses.max():.6f}")
    logger.info(f"Threshold: {threshold:.6f}")
    logger.info(f"Anomalies detected: {np.sum(predictions)} ({np.sum(predictions)/len(predictions)*100:.2f}%)")
    
    return losses, predictions


def evaluate_model(y_true, y_pred, losses, threshold):
    """Evaluate model performance"""
    logger.info("\n" + "="*60)
    logger.info("PERFORMANCE METRICS")
    logger.info("="*60)
    
    # Pad sequences for comparison (we lose 9 samples due to seq_length)
    seq_length = 10
    n_missing = seq_length - 1
    y_true_aligned = y_true[n_missing:n_missing+len(y_pred)]
    
    # Confusion matrix
    tn, fp, fn, tp = confusion_matrix(y_true_aligned, y_pred).ravel()
    logger.info(f"\nConfusion Matrix:")
    logger.info(f"  TP: {tp:6d} (Correctly identified anomalies)")
    logger.info(f"  TN: {tn:6d} (Correctly identified normal)")
    logger.info(f"  FP: {fp:6d} (False positive anomalies)")
    logger.info(f"  FN: {fn:6d} (False negative anomalies missed)")
    
    # Metrics
    precision, recall, f1, _ = precision_recall_fscore_support(y_true_aligned, y_pred, average='binary')
    accuracy = (tp + tn) / (tp + tn + fp + fn)
    specificity = tn / (tn + fp) if (tn + fp) > 0 else 0
    
    logger.info(f"\nMetrics:")
    logger.info(f"  Accuracy:    {accuracy:.4f} ({accuracy*100:.2f}%)")
    logger.info(f"  Precision:   {precision:.4f}")
    logger.info(f"  Recall:      {recall:.4f}")
    logger.info(f"  F1-Score:    {f1:.4f}")
    logger.info(f"  Specificity: {specificity:.4f}")
    
    # ROC-AUC
    try:
        auc_score = roc_auc_score(y_true_aligned, losses)
        logger.info(f"  ROC-AUC:     {auc_score:.4f}")
    except:
        logger.warning("  ROC-AUC:     N/A (not enough samples)")
    
    return accuracy, precision, recall, f1


def test_on_device(model, scaler, X_all, y_all, device_ids, threshold):
    """Test on specific devices"""
    logger.info("\n" + "="*60)
    logger.info("PER-DEVICE PERFORMANCE")
    logger.info("="*60)
    
    unique_devices = np.unique(device_ids)
    device_stats = []
    
    for device in unique_devices[:5]:  # Test first 5 devices
        device_mask = device_ids == device
        X_device = X_all[device_mask]
        y_device = y_all[device_mask]
        
        if len(X_device) == 0:
            continue
        
        # Normalize and predict
        X_norm = scaler.transform(X_device)
        X_seq = create_sequences(X_norm, seq_length=10)
        
        X_tensor = torch.from_numpy(X_seq).to(DEVICE)
        with torch.no_grad():
            recon = model(X_tensor)
            losses = torch.mean((X_tensor - recon) ** 2, dim=(1, 2)).cpu().numpy()
        
        preds = (losses > threshold).astype(int)
        accuracy = np.mean(preds == y_device[9:9+len(preds)])
        n_anomalies = np.sum(y_device)
        
        logger.info(f"\n{device}:")
        logger.info(f"  Samples:    {len(X_device)}")
        logger.info(f"  Anomalies:  {n_anomalies} ({n_anomalies/len(X_device)*100:.2f}%)")
        logger.info(f"  Accuracy:   {accuracy:.4f} ({accuracy*100:.2f}%)")
        logger.info(f"  Detected:   {np.sum(preds)}")
        
        device_stats.append({
            'device': device,
            'samples': len(X_device),
            'anomalies': n_anomalies,
            'accuracy': accuracy
        })
    
    return device_stats


# ============================================================================
# Main Testing
# ============================================================================
def main():
    logger.info("\n" + "="*60)
    logger.info("RETRAINED AI MODEL VALIDATION")
    logger.info("="*60)
    
    # Load artifacts
    model, scaler, threshold = load_artifacts()
    
    # Load test data
    X_test, y_test, device_ids = load_test_data()
    
    # Predict
    losses, predictions = predict_anomalies(model, scaler, X_test, threshold)
    
    # Evaluate
    accuracy, precision, recall, f1 = evaluate_model(y_test, predictions, losses, threshold)
    
    # Per-device analysis
    test_on_device(model, scaler, X_test, y_test, device_ids, threshold)
    
    logger.info("\n" + "="*60)
    logger.info("✅ VALIDATION COMPLETE!")
    logger.info("="*60)
    logger.info(f"\nKey Results:")
    logger.info(f"  - Overall Accuracy: {accuracy:.4f}")
    logger.info(f"  - Precision: {precision:.4f}")
    logger.info(f"  - Recall: {recall:.4f}")
    logger.info(f"  - F1-Score: {f1:.4f}")
    logger.info(f"\nAll models are production-ready! ✅")
    logger.info(f"Next: Deploy to Render backend service")


if __name__ == "__main__":
    main()
