"""
Backend connectivity diagnostic script.
Tests whether the backend is reachable and returns expected JSON responses.

Usage:
    python security_scripts/diagnose_backend.py [URL]

Default URL is http://localhost:8000.
"""
import sys
import json
import requests

URL = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"

print(f"DePIN-Guard Backend Diagnostics")
print(f"Target: {URL}")
print("-" * 50)

print("Test 1: Root endpoint...")
try:
    res = requests.get(URL, timeout=10)
    if res.status_code == 200:
        print("SUCCESS: Backend reachable")
    else:
        print(f"Reached but got status: {res.status_code}")
except Exception as e:
    print(f"FAILED: {e}")

print("-" * 50)

print("Test 2: Health endpoint...")
try:
    res = requests.get(f"{URL.rstrip('/')}/health", timeout=10)
    try:
        data = res.json()
        print(f"SUCCESS: {data}")
    except json.JSONDecodeError:
        print(f"FAILED: Got HTML instead of JSON (status {res.status_code})")
except Exception as e:
    print(f"FAILED: {e}")

print("-" * 50)