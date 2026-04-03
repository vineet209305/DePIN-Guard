"""
Async high-throughput ingestion service.
Sends concurrent sensor payloads to the backend for load testing.

Usage:
    pip install aiohttp
    python ingestion_service.py
"""
import asyncio
import aiohttp
import time
import random
from datetime import datetime

# ✅ Shared config se — env sahi se load hoga
from config import BACKEND_URL, API_KEY, DEVICES


def make_payload():
    return {
        "device_id":   random.choice(DEVICES),
        "temperature": round(random.uniform(20.0, 80.0), 2),
        "vibration":   round(random.uniform(0.1, 5.0), 2),
        "power_usage": round(random.uniform(10.0, 60.0), 2),
        "timestamp":   datetime.now().isoformat(),
    }


async def send_one(session, payload):
    headers = {"X-API-Key": API_KEY, "Content-Type": "application/json"}
    try:
        timeout = aiohttp.ClientTimeout(total=5)
        async with session.post(BACKEND_URL, json=payload, headers=headers, timeout=timeout) as resp:
            status = resp.status
            if status == 200:
                return "200"
            elif status == 429:
                return "429"
            elif status == 403:
                return "403"
            else:
                return str(status)
    except asyncio.TimeoutError:
        return "TIMEOUT"
    except Exception as e:
        return f"ERROR: {e}"


async def run_load_test(num_requests=100):
    print(f"🚀 Sending {num_requests} concurrent requests to {BACKEND_URL}...")
    payloads = [make_payload() for _ in range(num_requests)]
    start    = time.time()

    async with aiohttp.ClientSession() as session:
        tasks   = [send_one(session, p) for p in payloads]
        results = await asyncio.gather(*tasks, return_exceptions=True)

    duration = time.time() - start

    success      = sum(1 for r in results if r == "200")
    rate_limited = sum(1 for r in results if r == "429")
    forbidden    = sum(1 for r in results if r == "403")
    timeouts     = sum(1 for r in results if r == "TIMEOUT")
    errors       = sum(1 for r in results if str(r).startswith("ERROR"))

    print(f"\n📊 Results:")
    print(f"  ✅ Success (200):      {success}")
    print(f"  ⚡ Rate Limited (429): {rate_limited}")
    print(f"  🔒 Forbidden (403):    {forbidden}")
    print(f"  ⏱️  Timeouts:           {timeouts}")
    print(f"  ❌ Errors:             {errors}")
    print(f"  ⏱️  Total time:         {duration:.2f}s")
    print(f"  📈 Avg per request:    {duration / num_requests * 1000:.1f}ms")


if __name__ == "__main__":
    asyncio.run(run_load_test(100))