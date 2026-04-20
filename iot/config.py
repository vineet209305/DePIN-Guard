import os
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000").rstrip("/") + "/api/process_data"
API_KEY     = os.getenv("DEPIN_API_KEY", "")

if not API_KEY:
    raise RuntimeError("DEPIN_API_KEY is required for iot-simulator runtime")

DEVICES     = ["Device-001", "Device-002", "Device-003", "Device-004", "Device-005"]

MQTT_BROKER = "localhost"
MQTT_PORT   = 8883
MQTT_TOPIC  = "depin/sensors"

CA_CERT     = "ca.crt"
CLIENT_CERT = "client.crt"
CLIENT_KEY  = "client.key"