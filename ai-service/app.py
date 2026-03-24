from flask import Flask, request, jsonify
import torch
import joblib
import pandas as pd

from model import LSTMAutoencoder

app = Flask(__name__)

FEATURES = 3
MODEL_PATH = "lstm_autoencoder.pth"
SCALER_PATH = "scaler.save"
THRESHOLD_PATH = "threshold.txt"

print("Loading AI inference artifacts...")

model = LSTMAutoencoder(input_dim=FEATURES, hidden_dim=64)
model.load_state_dict(torch.load(MODEL_PATH, map_location=torch.device("cpu")))
model.eval()

scaler = joblib.load(SCALER_PATH)

with open(THRESHOLD_PATH, "r", encoding="utf-8") as f:
    THRESHOLD = float(f.read().strip())

print(f"AI service ready. Threshold: {THRESHOLD:.6f}")


@app.route("/predict", methods=["POST"])
def predict():
    try:
        data = request.get_json(force=True)

        temperature = data["temperature"]
        vibration = data["vibration"]
        pressure = data.get("pressure", data.get("power_usage"))

        if pressure is None:
            return jsonify({"error": "Missing pressure/power_usage field"}), 400

        input_df = pd.DataFrame(
            [[temperature, vibration, pressure]],
            columns=["temperature", "vibration", "pressure"],
        )
        scaled_data = scaler.transform(input_df)

        tensor_data = torch.FloatTensor(scaled_data).unsqueeze(0)

        with torch.no_grad():
            reconstruction = model(tensor_data)
            loss = torch.mean((tensor_data - reconstruction) ** 2).item()

        is_anomaly = loss > THRESHOLD
        return jsonify(
            {
                "is_anomaly": bool(is_anomaly),
                "anomaly": bool(is_anomaly),
                "loss": float(loss),
                "threshold": float(THRESHOLD),
            }
        )
    except KeyError as e:
        return jsonify({"error": f"Missing required field: {str(e)}"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)