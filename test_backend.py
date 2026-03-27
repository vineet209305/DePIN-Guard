import requests
import json

URL = "https://depin-backend.loca.lt"

print("🔍 Starting DePIN-Guard Distributed Diagnostics...")
print(f"🌍 Target Backend: {URL}")
print("-" * 50)

try:
    # Test 1: Normal HTTP Ping (Checking if Localtunnel warns us)
    print("Test 1: Normal HTTP Ping...")
    res = requests.get(URL, timeout=10)
    
    if "localtunnel" in res.text.lower() and "click to continue" in res.text.lower():
        print("⚠️ RESULT: Reached Localtunnel, but blocked by the 'Warning Page'!")
    elif res.status_code == 200:
        print("✅ SUCCESS: Backend is Live and reachable!")
    elif res.status_code == 404:
        print("❌ FAILED: 404 Not Found. Priyanshu's Localtunnel is running, but his FastAPI is DEAD.")
    else:
        print(f"⚠️ REACHED, but got status code: {res.status_code}")
except Exception as e:
    print(f"❌ FATAL ERROR: Cannot reach {URL} at all.")
    print("💡 FIX: Priyanshu must run `npx localtunnel --port 8000 --subdomain depin-backend` right now!")

print("-" * 50)

try:
    # Test 2: HTTP Ping WITH Bypass Secret Header
    print("Test 2: Target Ping WITH Secret Bypass Headers...")
    headers = {"bypass-tunnel-reminder": "true", "User-Agent": "depin-guard-bot"}
    res2 = requests.get(URL, headers=headers, timeout=10)
    
    # Try parsing the FastAPI Root Response
    try:
        data = res2.json()
        print(f"✅ SUCCESS: Backend successfully parsed! Response: {data}")
    except json.JSONDecodeError:
        print("❌ FAILED: The bypass code failed. Localtunnel is still forcing HTML.")
except Exception as e:
    print(f"❌ Error during bypass test: {e}")

print("-" * 50)