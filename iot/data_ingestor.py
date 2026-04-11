import requests
import time
import random
import json
import csv
import hmac
import hashlib
import ssl
import os
import glob
import re
import paho.mqtt.client as mqtt
from datetime import datetime, timedelta
from dotenv import load_dotenv
from human_readable_formatter import HumanReadableDataFormatter

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000").rstrip("/") + "/api/process_data"
API_KEY     = os.getenv("DEPIN_API_KEY", "")
SENSOR_SECRET = API_KEY

if not API_KEY:
    raise RuntimeError("DEPIN_API_KEY is required for iot-simulator runtime")

# Initialize human-readable formatter for non-technical users
FORMATTER = HumanReadableDataFormatter()

DEVICES     = ["Device-001", "Device-002", "Device-003", "Device-004", "Device-005"]
SIMULATOR_MODE = os.getenv("SIMULATOR_MODE", "synthetic").strip().lower()
DATA_SOURCE_FILE = os.getenv("SIMULATOR_DATA_FILE", "").strip()
DEFAULT_REPLAY_FILE = os.path.join(os.path.dirname(__file__), "normal_training_data.csv")
REAL_DATA_URL = os.getenv("REAL_DATA_URL", "").strip()
REAL_DATA_ROOT_KEY = os.getenv("REAL_DATA_ROOT_KEY", "").strip()


def _is_placeholder_url(url: str) -> bool:
    if not url:
        return True
    lowered = url.lower()
    placeholder_markers = (
        "<your-real-api-endpoint>",
        "%3cyour-real-api-endpoint%3e",
        "your-real-api-endpoint",
    )
    return any(marker in lowered for marker in placeholder_markers)

CA_CERT     = "ca.crt"
CLIENT_CERT = "client.crt"
CLIENT_KEY  = "client.key"
MQTT_BROKER = "localhost"
MQTT_PORT   = 8883
MQTT_TOPIC  = "depin/sensors"

_TEMP_ALIASES = (
    "temperature", "temp", "temperature_c", "temperature_motor", "meantemp", "mean_temp"
)
_VIB_ALIASES = (
    "vibration", "vib", "vibrationmms", "vibrationmms", "vibrationrms", "rmsvibration", "vibrationmm_s"
)
_POWER_ALIASES = (
    "powerusage", "powerconsumptionkw", "powerconsumption", "pwr"
)
_CURRENT_ALIASES = ("current", "currentphaseavg")
_VOLTAGE_ALIASES = ("voltage",)
_DEVICE_ALIASES = ("device_id", "device", "machine_id", "machineid", "machine")
_TIMESTAMP_ALIASES = ("timestamp", "time", "datetime")


def _clean_key(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "", str(value).strip().lower())


def _row_get_any(row, aliases):
    normalized_row = {_clean_key(key): row.get(key) for key in row.keys()}
    for alias in aliases:
        value = normalized_row.get(_clean_key(alias))
        if value is not None and str(value).strip() != "":
            return value
    return None


def _to_float(value):
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    try:
        return float(text)
    except Exception:
        return None


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


def _normalize_payload(row, fallback_device):
    raw_device = _row_get_any(row, _DEVICE_ALIASES)
    device_id = str(raw_device).strip() if raw_device is not None else fallback_device
    raw_timestamp = _row_get_any(row, _TIMESTAMP_ALIASES)
    normalized_timestamp = datetime.now().isoformat()

    if raw_timestamp:
        try:
            parsed_timestamp = datetime.fromisoformat(str(raw_timestamp).replace("Z", "+00:00"))
            if abs((datetime.now(parsed_timestamp.tzinfo) if parsed_timestamp.tzinfo else datetime.now()) - parsed_timestamp) <= timedelta(minutes=10):
                normalized_timestamp = parsed_timestamp.isoformat()
        except Exception:
            normalized_timestamp = datetime.now().isoformat()

    temperature = _to_float(_row_get_any(row, _TEMP_ALIASES))
    vibration = _to_float(_row_get_any(row, _VIB_ALIASES))
    power_usage = _to_float(_row_get_any(row, _POWER_ALIASES))

    # Estimate power for datasets that only include electrical current/voltage.
    if power_usage is None:
        current_val = _to_float(_row_get_any(row, _CURRENT_ALIASES))
        voltage_val = _to_float(_row_get_any(row, _VOLTAGE_ALIASES))
        if current_val is not None and voltage_val is not None:
            power_usage = (current_val * voltage_val) / 1000.0
        elif current_val is not None:
            power_usage = current_val * 10.0

    if temperature is None or vibration is None or power_usage is None:
        return None

    normalized = {
        "device_id":   device_id,
        "temperature": round(float(temperature), 2),
        "vibration":   round(float(vibration), 2),
        "power_usage": round(float(power_usage), 2),
        "timestamp":   normalized_timestamp,
    }
    
    # ENHANCEMENT: Add human-readable fields for non-technical users ✅
    try:
        formatted = FORMATTER.format_for_nontechnical_users(
            device_id=normalized['device_id'],
            temperature=normalized['temperature'],
            vibration=normalized['vibration'],
            power_usage=normalized['power_usage'],
            timestamp=normalized['timestamp']
        )
        # Add non-technical fields to payload
        normalized['machine_name'] = formatted['machine_name']
        normalized['alert_level'] = formatted['alert_level']
        normalized['status_short'] = formatted['status_short']
        normalized['recommendations'] = formatted['recommendations']
    except Exception as e:
        # If formatting fails, skip non-technical fields (still send sensor data)
        pass
    
    return normalized


def _resolve_replay_files(file_path):
    if not file_path:
        return [DEFAULT_REPLAY_FILE]

    if os.path.isdir(file_path):
        return sorted(glob.glob(os.path.join(file_path, "*.csv")))

    if "*" in file_path or "?" in file_path:
        return sorted(glob.glob(file_path))

    if os.path.exists(file_path):
        return [file_path]

    return []


def _load_replay_rows(file_path):
    replay_rows = []
    replay_files = _resolve_replay_files(file_path)
    if not replay_files:
        return []

    for replay_file in replay_files:
        if replay_file.lower().endswith(".csv"):
            with open(replay_file, "r", encoding="utf-8") as csv_file:
                reader = csv.DictReader(csv_file)
                for row in reader:
                    normalized = _normalize_payload(row, random.choice(DEVICES))
                    if normalized:
                        replay_rows.append(normalized)
            continue

        if replay_file.lower().endswith(".json"):
            with open(replay_file, "r", encoding="utf-8") as json_file:
                payload = json.load(json_file)
            rows = payload.get("records") if isinstance(payload, dict) else payload
            for row in rows:
                if not isinstance(row, dict):
                    continue
                normalized = _normalize_payload(row, random.choice(DEVICES))
                if normalized:
                    replay_rows.append(normalized)

    return replay_rows


def _extract_online_rows(payload):
    if isinstance(payload, list):
        return payload

    if isinstance(payload, dict):
        # Open-Meteo current weather payload support.
        current = payload.get("current")
        if isinstance(current, dict):
            temp = current.get("temperature_2m")
            wind = current.get("wind_speed_10m")
            if temp is not None:
                temp_val = float(temp)
                wind_val = float(wind) if wind is not None else 0.0
                return [{
                    "device_id": "Weather-Station-001",
                    "temperature": temp_val,
                    "vibration": round(max(wind_val / 20.0, 0.05), 2),
                    "power_usage": round(20.0 + (temp_val * 0.35) + (wind_val * 0.15), 2),
                    "timestamp": current.get("time") or datetime.now().isoformat(),
                }]

        if REAL_DATA_ROOT_KEY and isinstance(payload.get(REAL_DATA_ROOT_KEY), list):
            return payload.get(REAL_DATA_ROOT_KEY)

        for key in ("records", "data", "items", "results"):
            if isinstance(payload.get(key), list):
                return payload.get(key)

    return []


def _fetch_online_rows():
    if _is_placeholder_url(REAL_DATA_URL):
        return []

    try:
        response = requests.get(REAL_DATA_URL, timeout=20)
        response.raise_for_status()
        payload = response.json()
    except Exception as exc:
        print(f"⚠️ Real-data fetch failed: {exc}")
        return []

    rows = _extract_online_rows(payload)
    return [_normalize_payload(row, random.choice(DEVICES)) for row in rows if isinstance(row, dict)]


def _sign_payload(payload):
    message = f"{payload['device_id']}|{payload['temperature']}|{payload['vibration']}|{payload['power_usage']}|{payload['timestamp']}"
    payload["signature"] = hmac.new(
        SENSOR_SECRET.encode("utf-8"),
        message.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    return payload


def run_simulator():
    print(f"DePIN-Guard IoT Synthetic Data Ingestor Started")
    print(f"Sending data to: {BACKEND_URL}")
    print(f"Devices: {len(DEVICES)} active")
    print("Press Ctrl+C to stop.\n")

    try:
        while True:
            for device in DEVICES:
                data = generate_sensor_data(device)
                data = _sign_payload(data)
                try:
                    headers = {
                        "X-API-Key": API_KEY,
                        "Content-Type": "application/json",
                    }
                    response = requests.post(BACKEND_URL, json=data, headers=headers, timeout=15)
                    if response.status_code == 200:
                        result      = response.json()
                        status_icon = "🔴" if result.get("anomaly") else "🟢"
                        print(f"{status_icon} {device}: {data['temperature']}°C → HTTP {response.status_code}")
                    else:
                        print(f"❌ Error {response.status_code}: {response.text}")
                except requests.exceptions.ConnectionError:
                    print("❌ Connection failed — backend chal raha hai? (uvicorn main:app --port 8000)")
                except Exception as e:
                    print(f"⚠️ Error: {e}")
                time.sleep(1)
            time.sleep(2)
    except KeyboardInterrupt:
        print("\nSimulator stopped.")


def run_replay_simulator():
    replay_file = DATA_SOURCE_FILE or DEFAULT_REPLAY_FILE
    rows = _load_replay_rows(replay_file)

    if not rows:
        if DATA_SOURCE_FILE:
            print(f"No replay data found at {replay_file}.")
            print("Provide a valid external CSV/JSON file in SIMULATOR_DATA_FILE and retry.")
            return

        print(f"No replay data found at {replay_file}; falling back to synthetic mode.")
        run_simulator()
        return

    print("DePIN-Guard IoT CSV Data Ingestor Started")
    print(f"Replaying data from: {replay_file}")
    print(f"Sending data to: {BACKEND_URL}")
    print(f"Rows loaded: {len(rows)}")
    print("Press Ctrl+C to stop.\n")

    try:
        while True:
            for data in rows:
                try:
                    data = _sign_payload(dict(data))
                    headers = {
                        "X-API-Key": API_KEY,
                        "Content-Type": "application/json",
                    }
                    response = requests.post(BACKEND_URL, json=data, headers=headers, timeout=15)
                    if response.status_code == 200:
                        result = response.json()
                        status_icon = "🔴" if result.get("anomaly") else "🟢"
                        print(f"{status_icon} {data['device_id']}: {data['temperature']}°C → HTTP {response.status_code}")
                    else:
                        print(f"❌ Error {response.status_code}: {response.text}")
                except requests.exceptions.ConnectionError:
                    print("❌ Connection failed — backend chal raha hai? (uvicorn main:app --port 8000)")
                except Exception as e:
                    print(f"⚠️ Error: {e}")
                time.sleep(1)
            time.sleep(2)
    except KeyboardInterrupt:
        print("\nReplay simulator stopped.")


def run_online_simulator():
    if _is_placeholder_url(REAL_DATA_URL):
        print("REAL_DATA_URL is not configured with a real endpoint.")
        print("Set REAL_DATA_URL in iot-simulator/.env or run replay/synthetic mode.")
        print("Falling back to replay mode.\n")
        run_replay_simulator()
        return

    print("DePIN-Guard IoT Online Data Ingestor Started")
    print(f"Source API: {REAL_DATA_URL}")
    print(f"Sending data to: {BACKEND_URL}")
    print("Press Ctrl+C to stop.\n")

    try:
        while True:
            rows = _fetch_online_rows()
            if not rows:
                print("No online rows available right now; retrying...")
                time.sleep(5)
                continue

            for data in rows:
                try:
                    data["timestamp"] = datetime.now().isoformat()
                    data = _sign_payload(dict(data))
                    headers = {
                        "X-API-Key": API_KEY,
                        "Content-Type": "application/json",
                    }
                    response = requests.post(BACKEND_URL, json=data, headers=headers, timeout=15)
                    if response.status_code == 200:
                        result = response.json()
                        status_icon = "🔴" if result.get("anomaly") else "🟢"
                        print(f"{status_icon} {data['device_id']}: {data['temperature']}°C → HTTP {response.status_code}")
                    else:
                        print(f"❌ Error {response.status_code}: {response.text}")
                except requests.exceptions.ConnectionError:
                    print("❌ Connection failed — backend chal raha hai? (uvicorn main:app --port 8000)")
                except Exception as exc:
                    print(f"⚠️ Error: {exc}")
                time.sleep(1)

            time.sleep(5)
    except KeyboardInterrupt:
        print("\nOnline-data simulator stopped.")


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
    elif len(sys.argv) > 1 and sys.argv[1] == "replay":
        run_replay_simulator()
    elif len(sys.argv) > 1 and sys.argv[1] == "online":
        run_online_simulator()
    elif SIMULATOR_MODE == "online":
        run_online_simulator()
    elif SIMULATOR_MODE == "replay":
        run_replay_simulator()
    else:
        run_simulator()