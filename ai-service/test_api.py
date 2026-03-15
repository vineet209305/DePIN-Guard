import requests

BASE_URL = "http://localhost:5000"


def test_predict(label, payload):
    res = requests.post(f"{BASE_URL}/predict", json=payload, timeout=5)
    data = res.json()
    tag = "ANOMALY" if data.get("is_anomaly") else "NORMAL"
    print(
        f"[{label}] {tag} | "
        f"loss={data.get('loss'):.6f} | "
        f"threshold={data.get('threshold'):.6f}"
    )


if __name__ == "__main__":
    print("=== DePIN-Guard AI Inference Test ===")
    test_predict("Normal  ", {"temperature": 35.0, "vibration": 0.5, "power_usage": 25.0})
    test_predict("Extreme ", {"temperature": 120.0, "vibration": 12.0, "power_usage": 145.0})