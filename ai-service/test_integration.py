"""
Integration test for the AI inference service.
Run with: python test_integration.py
Start the AI service first: python app.py
"""
import requests
import time
import random

url = "http://localhost:5000/predict"

print("--- AI Service Integration Test ---")

for i in range(1, 36):
    data = {
        "temperature": random.uniform(20, 30),
        "vibration":   random.uniform(0.1, 0.5),
        "power_usage": random.uniform(10, 50),
    }

    try:
        response = requests.post(url, json=data, timeout=5)
        result   = response.json()
        status   = result.get("status", "unknown")
        print(f"Request {i:02d}: status={status} | loss={result.get('loss', 0):.6f}")
    except Exception as e:
        print(f"Connection failed: {e}")
        break

    time.sleep(0.05)

print("\n--- Test Complete ---")