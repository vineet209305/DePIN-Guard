"""
Backend connectivity diagnostic script.
Tests whether the backend is reachable, with and without localtunnel bypass headers.

Usage:
    python security_scripts/diagnose_backend.py [URL]

Default URL is http://localhost:8000. Pass a localtunnel URL as argument when testing remotely.
"""
import sys
import json
import requests

URL = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"

print(f"DePIN-Guard Backend Diagnostics")
print(f"Target: {URL}")
print("-" * 50)

# Test 1: Plain request
print("Test 1: Plain HTTP request...")
try:
    res = requests.get(URL, timeout=10)
    if "localtunnel" in res.text.lower():
        print("WARNING: Blocked by localtunnel warning page — use bypass headers")
    elif res.status_code == 200:
        print("SUCCESS: Backend reachable")
    else:
        print(f"Reached but got status: {res.status_code}")
except Exception as e:
    print(f"FAILED: {e}")

print("-" * 50)

# Test 2: With bypass headers
print("Test 2: Request with localtunnel bypass headers...")
headers = {"bypass-tunnel-reminder": "true", "User-Agent": "depin-guard-bot"}
try:
    res = requests.get(URL, headers=headers, timeout=10)
    try:
        data = res.json()
        print(f"SUCCESS: {data}")
    except json.JSONDecodeError:
        print(f"FAILED: Got HTML instead of JSON (status {res.status_code})")
except Exception as e:
    print(f"FAILED: {e}")

print("-" * 50)