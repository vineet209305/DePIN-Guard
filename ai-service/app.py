import logging
import os
import threading
import time

import joblib
import torch
from flask import Flask, jsonify, request

from model import LSTMAutoencoder
from preprocessing import canonicalize_sensor_frame

app = Flask(__name__)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger("depin_guard.ai_service")

FEATURES = 3
MODEL_PATH = "lstm_autoencoder.pth"
SCALER_PATH = "scaler.save"
THRESHOLD_PATH = "threshold.txt"
# Render sets PORT env var; check it first, then fallback to AI_SERVICE_PORT or 10000
DEFAULT_PORT = int(os.getenv("PORT", os.getenv("AI_SERVICE_PORT", "10000")))
DEFAULT_HOST = os.getenv("HOST", "0.0.0.0")

_artifact_lock = threading.Lock()
_artifacts_loaded = False
_artifact_error = None
model = None
scaler = None
THRESHOLD = None


def ensure_artifacts_loaded():
    global _artifacts_loaded, _artifact_error, model, scaler, THRESHOLD

    if _artifacts_loaded:
        return

    with _artifact_lock:
        if _artifacts_loaded:
            return

        try:
            logger.info("Loading AI inference artifacts")

            loaded_model = LSTMAutoencoder(input_dim=FEATURES, hidden_dim=64)
            loaded_model.load_state_dict(torch.load(MODEL_PATH, map_location=torch.device("cpu")))
            loaded_model.eval()

            loaded_scaler = joblib.load(SCALER_PATH)

            with open(THRESHOLD_PATH, "r", encoding="utf-8") as threshold_file:
                loaded_threshold = float(threshold_file.read().strip())

            model = loaded_model
            scaler = loaded_scaler
            THRESHOLD = loaded_threshold
            _artifact_error = None
            _artifacts_loaded = True

            logger.info("AI service ready with threshold %.6f", THRESHOLD)
        except Exception as exc:
            _artifact_error = f"{type(exc).__name__}: {exc}"
            logger.exception("Failed to load AI inference artifacts")
            raise


def validate_payload(payload):
    if not isinstance(payload, dict):
        return None, (jsonify({"error": "Request body must be a JSON object"}), 400)

    missing = [field for field in ("temperature", "vibration") if field not in payload]
    if missing:
        return None, (jsonify({"error": f"Missing required field(s): {', '.join(missing)}"}), 400)

    if payload.get("pressure") is None and payload.get("power_usage") is None:
        return None, (jsonify({"error": "Missing pressure/power_usage field"}), 400)

    try:
        input_frame = canonicalize_sensor_frame([payload])
    except (KeyError, ValueError, TypeError) as exc:
        return None, (jsonify({"error": str(exc)}), 400)

    return input_frame, None


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


@app.route("/ready", methods=["GET"])
def ready():
    try:
        ensure_artifacts_loaded()
        return jsonify({"status": "ready"})
    except Exception:
        return jsonify({"status": "not_ready", "error": _artifact_error or "unknown error"}), 503


@app.route("/predict", methods=["POST"])
def predict():
    started_at = time.perf_counter()

    try:
        ensure_artifacts_loaded()
    except Exception:
        return jsonify({"error": "AI inference artifacts are unavailable", "details": _artifact_error or "unknown"}), 503

    payload = request.get_json(silent=True)
    input_frame, error_response = validate_payload(payload)
    if error_response is not None:
        return error_response

    scaled_data = scaler.transform(input_frame)
    tensor_data = torch.tensor(scaled_data, dtype=torch.float32).unsqueeze(0)

    with torch.no_grad():
        reconstruction = model(tensor_data)
        loss = torch.mean((tensor_data - reconstruction) ** 2).item()

    is_anomaly = loss > THRESHOLD
    duration_ms = (time.perf_counter() - started_at) * 1000.0

    logger.info("Inference completed in %.2f ms with loss %.6f", duration_ms, loss)

    return jsonify(
        {
            "is_anomaly": bool(is_anomaly),
            "anomaly": bool(is_anomaly),
            "status": "anomaly" if is_anomaly else "normal",
            "loss": float(loss),
            "threshold": float(THRESHOLD),
        }
    )


if __name__ == "__main__":
    logger.info(f"Starting AI service on {DEFAULT_HOST}:{DEFAULT_PORT}")
    app.run(host=DEFAULT_HOST, port=DEFAULT_PORT, debug=False)