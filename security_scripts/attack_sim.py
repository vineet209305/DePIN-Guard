# security_scripts/attack_sim.py
import os
import requests
import time

BASE_URL = os.getenv("BACKEND_BASE_URL", "http://localhost:8000")
API_KEY = os.getenv("DEPIN_API_KEY", "")

print("=" * 50)
print("🔐 DePIN-Guard Penetration Test")
print("=" * 50)

if not API_KEY:
    print("❌ Missing DEPIN_API_KEY environment variable")
    raise SystemExit(1)

# ─── Test 1: No API Key ───
print("\n[TEST 1] Calling /api/dashboard WITHOUT API Key...")
response = requests.get(f"{BASE_URL}/api/dashboard")
if response.status_code == 403:
    print(f"✅ PASSED — Got {response.status_code} Forbidden as expected")
else:
    print(f"❌ FAILED — Got {response.status_code} (should be 403)")

# ─── Test 2: Wrong API Key ───
print("\n[TEST 2] Calling /api/dashboard with WRONG API Key...")
response = requests.get(f"{BASE_URL}/api/dashboard", headers={"X-API-Key": "wrong-key"})
if response.status_code == 403:
    print(f"✅ PASSED — Got {response.status_code} Forbidden as expected")
else:
    print(f"❌ FAILED — Got {response.status_code} (should be 403)")

# ─── Test 3: No JWT Token ───
print("\n[TEST 3] Calling /submit-data WITHOUT JWT Token...")
response = requests.post(f"{BASE_URL}/submit-data", json={"test": "data"})
if response.status_code == 401:
    print(f"✅ PASSED — Got {response.status_code} Unauthorized as expected")
else:
    print(f"❌ FAILED — Got {response.status_code} (should be 401)")

# ─── Test 4: Rate Limiting ───
print("\n[TEST 4] Sending 65 requests to trigger Rate Limiting...")
blocked = False
for i in range(65):
    response = requests.post(f"{BASE_URL}/api/process_data", 
    json={
        "device_id": "test-device",
        "temperature": 50.0,
        "vibration": 5.0,
        "power_usage": 100.0,
        "timestamp": "2026-01-01T00:00:00"
    },
        headers={"X-API-Key": API_KEY})
    if response.status_code == 429:
        print(f"✅ PASSED — Rate limit triggered at request {i+1} (429 Too Many Requests)")
        blocked = True
        break

if not blocked:
    print("❌ FAILED — Rate limit never triggered after 65 requests")

# ─── Test 5: SQL Injection Attempt ───
print("\n[TEST 5] Sending SQL Injection payload with valid API key...")
response = requests.post(f"{BASE_URL}/api/process_data", 
    json={
        "device_id": "'; DROP TABLE users; --",
        "temperature": 50.0,
        "vibration": 5.0,
        "power_usage": 100.0,
        "timestamp": "2026-01-01T00:00:00"
    },
    headers={"X-API-Key": API_KEY})
if response.status_code in [400, 422]:
    print(f"✅ PASSED — Injection blocked with {response.status_code}")
else:
    print(f"⚠️  INFO — Got {response.status_code} (system processed it, note for report)")

print("\n" + "=" * 50)
print("✅ Penetration Test Complete!")
print("=" * 50)