import os

BACKEND_URL = (os.getenv("VITE_API_URL", "http://localhost:8000")).rstrip("/") + "/api/process_data"
API_KEY     = os.getenv("DEPIN_API_KEY", "Depin_Project_Secret_Key_999")
DEVICES     = ["Device-001", "Device-002", "Device-003", "Device-004", "Device-005"]

MQTT_BROKER = "localhost"
MQTT_PORT   = 8883
MQTT_TOPIC  = "depin/sensors"

CA_CERT     = "ca.crt"
CLIENT_CERT = "client.crt"
CLIENT_KEY  = "client.key"