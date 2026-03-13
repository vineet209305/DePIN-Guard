import requests
import time
import random
import json
import csv
from datetime import datetime

# --- CONFIGURATION ---
BACKEND_URL = "http://localhost:8000/api/process_data"
DEVICES = ["Device-001", "Device-002", "Device-003", "Device-004", "Device-005"]

# 🔒 SECURITY: The Key must match what is in your Backend's .env file
API_KEY = "Depin_Project_Secret_Key_999"

def generate_sensor_data(device_id):
    """
    Generates synthetic IoT data.
    Most of the time it generates 'Normal' data.
    Sometimes (25% chance here) it generates 'Anomaly' data to trigger the AI.
    """
    is_anomaly = random.random() < 0.25  # Adjusted to 25% for demo purposes

    if is_anomaly:
        print(f"⚠️ GENERATING ATTACK for {device_id}!")
        # Anomaly: High Temp, High Vibration, High Power
        temperature = round(random.uniform(95.0, 120.0), 2)  # Overheating
        vibration = round(random.uniform(5.0, 15.0), 2)      # Heavy shaking
        power_usage = round(random.uniform(100.0, 150.0), 2) # Power spike
    else:
        # Normal: Safe Temp, Low Vibration, Normal Power
        temperature = round(random.uniform(20.0, 60.0), 2)
        vibration = round(random.uniform(0.1, 2.0), 2)
        power_usage = round(random.uniform(10.0, 50.0), 2)

    return {
        "device_id": device_id,
        "temperature": temperature,
        "vibration": vibration,
        "power_usage": power_usage,
        "timestamp": datetime.now().isoformat()
    }

def run_simulator():
    print(f"🚀 DePIN-Guard IoT Simulator Started...")
    print(f"📡 Sending data to: {BACKEND_URL}")
    print("Press Ctrl+C to stop.\n")

    try:
        while True:
            for device in DEVICES:
                data = generate_sensor_data(device)
                
                try:
                    # 🔑 AUTHENTICATION: We now send the API Key in the headers!
                    headers = {
                        "X-API-Key": API_KEY,
                        "Content-Type": "application/json"
                    }

                    # Send data to Backend with Headers
                    response = requests.post(BACKEND_URL, json=data, headers=headers, timeout=2)
                    
                    if response.status_code == 200:
                        result = response.json()
                        status_icon = "🔴" if result.get("anomaly") else "🟢"
                        print(f"{status_icon} Sent {device}: {data['temperature']}°C -> {response.status_code}")
                    else:
                        print(f"❌ Error {response.status_code}: {response.text}")

                except requests.exceptions.ConnectionError:
                    print(f"❌ Connection Failed: Is the Backend running?")
                except Exception as e:
                    print(f"⚠️ Error: {e}")

                time.sleep(1) # Small delay between devices to look like a real stream
            
            time.sleep(2) # Wait 2 seconds before next batch scan

    except KeyboardInterrupt:
        print("\n🛑 Simulator Stopped.")


# =============================================
# ✅ WEEK 5 - TASK 2: Training Data Generator
#    Mohit ke liye 10,000 rows of NORMAL data
# =============================================
def generate_training_data(num_rows=10000):
    """
    Generates 10,000 rows of NORMAL sensor data for Mohit's AI training.
    Sirf normal data — koi anomaly nahi.
    Output: normal_training_data.csv
    """
    filename = "normal_training_data.csv"
    fieldnames = ["timestamp", "device_id", "temperature", "vibration", "power_usage"]

    print(f"⏳ Generating {num_rows} rows of normal training data...")

    with open(filename, "w", newline="") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        for i in range(num_rows):
            device = random.choice(DEVICES)
            row = {
                "timestamp": datetime.now().isoformat(),
                # NORMAL ranges only — no anomalies
                "device_id":    device,
                "temperature":  round(random.uniform(20.0, 60.0), 2),
                "vibration":    round(random.uniform(0.1, 2.0), 2),
                "power_usage":  round(random.uniform(10.0, 50.0), 2),
            }
            writer.writerow(row)

            # Progress print every 1000 rows
            if (i + 1) % 1000 == 0:
                print(f"  ✔ {i + 1}/{num_rows} rows written...")

    print(f"\n✅ Done! File saved: '{filename}'")
    print(f"📦 Send this file to Mohit (ya git push kar do)\n")


if __name__ == "__main__":
    import sys

    # Run karne ke 2 tarike:
    #   python simulator.py          → Live simulator chalega (backend ko data bhejega)
    #   python simulator.py generate → Training data CSV banayega (Mohit ke liye)

    if len(sys.argv) > 1 and sys.argv[1] == "generate":
        generate_training_data(10000)
    else:
        run_simulator()