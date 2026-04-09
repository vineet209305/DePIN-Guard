import os
import sys

import requests

BASE_URL = os.getenv("AI_SERVICE_URL", "http://127.0.0.1:10000")


def post_json(path, payload):
    response = requests.post(f"{BASE_URL}{path}", json=payload, timeout=5)
    try:
        data = response.json()
    except ValueError as exc:
        raise AssertionError(f"Response was not valid JSON: {exc}") from exc
    return response, data


def assert_predict_response(data):
    assert isinstance(data.get("is_anomaly"), bool), "is_anomaly must be a boolean"
    assert isinstance(data.get("anomaly"), bool), "anomaly must be a boolean"
    assert isinstance(data.get("loss"), (int, float)), "loss must be numeric"
    assert isinstance(data.get("threshold"), (int, float)), "threshold must be numeric"


def test_predict(label, payload):
    response, data = post_json("/predict", payload)
    assert response.status_code == 200, f"{label} request failed with {response.status_code}: {data}"
    assert_predict_response(data)
    tag = "ANOMALY" if data.get("is_anomaly") else "NORMAL"
    print(
        f"[{label}] {tag} | "
        f"loss={float(data.get('loss')):.6f} | "
        f"threshold={float(data.get('threshold')):.6f}"
    )


def test_invalid_payload():
    response, data = post_json("/predict", {"temperature": 35.0})
    assert response.status_code == 400, f"Invalid payload should return 400, got {response.status_code}: {data}"
    assert "error" in data, "Invalid payload response must include an error field"


if __name__ == "__main__":
    try:
        print("=== DePIN-Guard AI Inference Test ===")
        test_predict("Normal  ", {"temperature": 35.0, "vibration": 0.5, "power_usage": 25.0})
        test_predict("Extreme ", {"temperature": 120.0, "vibration": 12.0, "power_usage": 145.0})
        test_invalid_payload()
        print("AI smoke test passed.")
    except Exception as exc:
        print(f"AI smoke test failed: {exc}")
        sys.exit(1)