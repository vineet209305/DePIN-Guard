"""
Integration test for the AI inference service.
Run with: python test_integration.py
Start the AI service first: python app.py
"""
import os
import random
import sys
import time

import requests

BASE_URL = os.getenv("AI_SERVICE_URL", "http://127.0.0.1:5000")
REQUEST_COUNT = int(os.getenv("AI_SERVICE_TEST_REQUESTS", "35"))
URL = f"{BASE_URL}/predict"


print("--- AI Service Integration Test ---")

try:
    for i in range(1, REQUEST_COUNT + 1):
        data = {
            "temperature": random.uniform(20, 30),
            "vibration": random.uniform(0.1, 0.5),
            "power_usage": random.uniform(10, 50),
        }

        response = requests.post(URL, json=data, timeout=5)
        response.raise_for_status()

        result = response.json()
        if not isinstance(result.get("is_anomaly"), bool):
            raise AssertionError("Response must include boolean is_anomaly")
        if not isinstance(result.get("loss"), (int, float)):
            raise AssertionError("Response must include numeric loss")

        status = result.get("status", "unknown")
        print(f"Request {i:02d}: status={status} | loss={float(result.get('loss', 0)):.6f}")

        time.sleep(0.05)

    print("\n--- Test Complete ---")
except Exception as exc:
    print(f"Integration test failed: {exc}")
    sys.exit(1)