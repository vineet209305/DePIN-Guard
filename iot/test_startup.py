#!/usr/bin/env python3
"""
Test script to debug data_ingestor startup
"""
print("1️⃣  Starting test script...")

try:
    print("2️⃣  Importing dotenv...")
    from dotenv import load_dotenv
    import os
    print("✅ Dotenv imported")
    
    print("3️⃣  Loading .env file...")
    load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))
    print("✅ .env loaded")
    
    print("4️⃣  Getting environment variables...")
    BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000").rstrip("/") + "/api/process_data"
    API_KEY = os.getenv("DEPIN_API_KEY", "")
    SIMULATOR_MODE = os.getenv("SIMULATOR_MODE", "synthetic").strip().lower()
    DATA_SOURCE_FILE = os.getenv("SIMULATOR_DATA_FILE", "").strip()
    
    print(f"✅ Env vars loaded:")
    print(f"   - BACKEND_URL: {BACKEND_URL}")
    print(f"   - API_KEY: {API_KEY[:8]}..." if API_KEY else "   - API_KEY: (empty)")
    print(f"   - SIMULATOR_MODE: {SIMULATOR_MODE}")
    print(f"   - DATA_SOURCE_FILE: {DATA_SOURCE_FILE}")
    
    if not API_KEY:
        raise RuntimeError("DEPIN_API_KEY is required!")
    
    print("5️⃣  Importing remaining modules...")
    import requests
    import csv
    import json
    import time
    import random
    import hmac
    import hashlib
    import ssl
    import glob
    import re
    import paho.mqtt.client as mqtt
    from datetime import datetime, timedelta
    from human_readable_formatter import HumanReadableDataFormatter
    print("✅ All modules imported")
    
    print("6️⃣  Initializing formatter...")
    FORMATTER = HumanReadableDataFormatter()
    print("✅ Formatter initialized")
    
    print("7️⃣  Checking data file...")
    import os
    data_file = DATA_SOURCE_FILE or os.path.join(os.path.dirname(__file__), "normal_training_data.csv")
    print(f"   File path: {data_file}")
    print(f"   File exists: {os.path.exists(data_file)}")
    if os.path.exists(data_file):
        size_mb = os.path.getsize(data_file) / (1024 * 1024)
        print(f"   File size: {size_mb:.1f} MB")
    
    print("8️⃣  Loading CSV file (first 5 rows)...")
    with open(data_file, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        count = 0
        for row in reader:
            print(f"   Row {count}: {row}")
            count += 1
            if count >= 5:
                break
    print(f"✅ CSV file is readable")
    
    print("\n✅ ALL TESTS PASSED - startup should work!")
    
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
