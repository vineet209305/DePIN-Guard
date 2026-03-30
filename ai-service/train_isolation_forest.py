import numpy as np
import joblib
from sklearn.ensemble import IsolationForest

print("Training Isolation Forest model...")

np.random.seed(42)

normal_temp = 25 + np.random.randn(500) * 5
normal_vibe = 10 + np.random.randn(500) * 2

X_train = np.vstack([normal_temp, normal_vibe]).T
print(f"Training data shape: {X_train.shape}")

model = IsolationForest(contamination=0.1, random_state=42)
model.fit(X_train)
print("Model training complete")

joblib.dump(model, 'model_v1.joblib')
print("Model saved as model_v1.joblib")