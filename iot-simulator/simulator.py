import requests
import time
import random
import json
import csv
import ssl
import os
import paho.mqtt.client as mqtt
from datetime import datetime
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

BACKEND_URL = (os.getenv("VITE_API_URL", "http://localhost:8000")).rstrip("/") + "/api/process_data"
API_KEY     = os.getenv("DEPIN_API_KEY", "Depin_Project_Secret_Key_999")
DEVICES     = ["Device-001", "Device-002", "Device-003", "Device-004", "Device-005"]

CA_CERT     = "ca.crt"
CLIENT_CERT = "client.crt"
CLIENT_KEY  = "client.key"
MQTT_BROKER = "localhost"
MQTT_PORT   = 8883
MQTT_TOPIC  = "depin/sensors"


def generate_sensor_data(device_id):
    is_anomaly = random.random() < 0.25

    if is_anomaly:
        temperature = round(random.uniform(95.0, 120.0), 2)
        vibration   = round(random.uniform(5.0, 15.0), 2)
        power_usage = round(random.uniform(100.0, 150.0), 2)
    else:
        temperature = round(random.uniform(20.0, 60.0), 2)
        vibration   = round(random.uniform(0.1, 2.0), 2)
        power_usage = round(random.uniform(10.0, 50.0), 2)

    return {
        "device_id":   device_id,
        "temperature": temperature,
        "vibration":   vibration,
        "power_usage": power_usage,
        "timestamp":   datetime.now().isoformat(),
    }


def run_simulator():
    print(f"DePIN-Guard IoT Simulator Started")
    print(f"Sending data to: {BACKEND_URL}")
    print(f"Devices: {len(DEVICES)} active")
    print("Press Ctrl+C to stop.\n")

    try:
        while True:
            for device in DEVICES:
                data = generate_sensor_data(device)
                try:
                    headers = {
                        "X-API-Key":              API_KEY,
                        "Content-Type":           "application/json",
                        "bypass-tunnel-reminder": "true",
                        "User-Agent":             "depin-guard-bot",
                    }
                    response = requests.post(BACKEND_URL, json=data, headers=headers, timeout=15)
                    if response.status_code == 200:
                        result      = response.json()
                        status_icon = "🔴" if result.get("anomaly") else "🟢"
                        print(f"{status_icon} {device}: {data['temperature']}°C → HTTP {response.status_code}")
                    else:
                        print(f"❌ Error {response.status_code}: {response.text}")
                except requests.exceptions.ConnectionError:
                    print("❌ Connection failed — is the backend running?")
                except Exception as e:
                    print(f"⚠️ Error: {e}")
                time.sleep(1)
            time.sleep(2)
    except KeyboardInterrupt:
        print("\nSimulator stopped.")


def run_secure_simulator():
    print(f"DePIN-Guard SECURE IoT Simulator Started")
    print(f"Connecting to MQTT Broker: {MQTT_BROKER}:{MQTT_PORT} (TLS)")

    client = mqtt.Client(client_id="DePIN-Simulator-001")

    try:
        client.tls_set(
            ca_certs=CA_CERT,
            certfile=CLIENT_CERT,
            keyfile=CLIENT_KEY,
            tls_version=ssl.PROTOCOL_TLSv1_2,
        )
        print("TLS certificates loaded successfully")
    except Exception as e:
        print(f"TLS setup failed: {e}")
        print("Falling back to HTTP mode...")
        run_simulator()
        return

    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            print(f"Connected to MQTT Broker (port {MQTT_PORT}, TLS)")
        else:
            print(f"Connection failed with code: {rc}")

    client.on_connect = on_connect

    try:
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        client.loop_start()

        while True:
            for device in DEVICES:
                data    = generate_sensor_data(device)
                payload = json.dumps(data)
                client.publish(MQTT_TOPIC, payload, qos=1)
                icon = "⚠️" if data["temperature"] > 90 else "🟢"
                print(f"{icon} [TLS] {device}: {data['temperature']}°C | vib={data['vibration']} | pwr={data['power_usage']}W")
                time.sleep(1)
            time.sleep(2)

    except KeyboardInterrupt:
        print("\nSecure simulator stopped.")
        client.loop_stop()
        client.disconnect()
    except Exception as e:
        print(f"Error: {e}")


def generate_training_data(num_rows=10000):
    filename   = "normal_training_data.csv"
    fieldnames = ["timestamp", "device_id", "temperature", "vibration", "power_usage"]

    print(f"Generating {num_rows} rows of normal training data...")
    with open(filename, "w", newline="") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for i in range(num_rows):
            device = random.choice(DEVICES)
            writer.writerow({
                "timestamp":   datetime.now().isoformat(),
                "device_id":   device,
                "temperature": round(random.uniform(20.0, 60.0), 2),
                "vibration":   round(random.uniform(0.1, 2.0), 2),
                "power_usage": round(random.uniform(10.0, 50.0), 2),
            })
            if (i + 1) % 1000 == 0:
                print(f"  {i + 1}/{num_rows} rows written...")

    print(f"Done — saved to {filename}")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "generate":
        generate_training_data(10000)
    elif len(sys.argv) > 1 and sys.argv[1] == "secure":
        run_secure_simulator()
    else:
        run_simulator()