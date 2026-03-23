# iot-simulator/async_ingestion.py
# Install: pip install aiohttp
# Run: python async_ingestion.py

import asyncio, aiohttp, time, random
from datetime import datetime

BACKEND_URL = "http://localhost:8000/api/process_data"
API_KEY = "Depin_Project_Secret_Key_999"
DEVICES = ["Device-001", "Device-002", "Device-003", "Device-004", "Device-005"]

def make_payload():
    return {
        "device_id": random.choice(DEVICES),
        "temperature": round(random.uniform(20.0, 80.0), 2),
        "vibration": round(random.uniform(0.1, 5.0), 2),
        "power_usage": round(random.uniform(10.0, 60.0), 2),
        "timestamp": datetime.now().isoformat()
    }

async def send_one(session, payload):
    headers = {"X-API-Key": API_KEY, "Content-Type": "application/json"}
    try:
        timeout = aiohttp.ClientTimeout(total=5)
        async with session.post(BACKEND_URL, json=payload, headers=headers, timeout=timeout) as resp:
            return resp.status
    except Exception as e:
        return f"ERROR: {e}"

async def run_load_test(num_requests=100):
    print(f"Sending {num_requests} concurrent requests to backend...")
    payloads = [make_payload() for _ in range(num_requests)]
    start = time.time()
    async with aiohttp.ClientSession() as session:
        tasks = [send_one(session, p) for p in payloads]
        results = await asyncio.gather(*tasks, return_exceptions=True)
    duration = time.time() - start
    success = sum(1 for r in results if r == 200)
    print(f"Success: {success} | Failed: {num_requests - success} | Total: {duration:.2f}s | Avg: {duration/num_requests*1000:.1f}ms")

if __name__ == "__main__":
    asyncio.run(run_load_test(100))