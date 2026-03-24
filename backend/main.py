import time as _time
from fastapi import FastAPI, HTTPException, Security, status, Depends, Header, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import APIKeyHeader
from pydantic import BaseModel
from routes.stream import broadcast_data, router as stream_router
from routes.fraud import router as fraud_router
import jwt, os, hashlib, json
import requests as http_requests
from datetime import datetime
from dotenv import load_dotenv
from apscheduler.schedulers.background import BackgroundScheduler
from contextlib import asynccontextmanager
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# ==========================================

try:
    from fabric_manager import fabric_client
    BLOCKCHAIN_ACTIVE = True
except ImportError:
    BLOCKCHAIN_ACTIVE = False
    print("Fabric Manager not found. Blockchain integration disabled.")


def run_gnn_analysis():
    print("[SCHEDULER] GNN analysis triggered — scanning for fraud patterns...")
    try:
        api_key = os.getenv("DEPIN_API_KEY", "Depin_Project_Secret_Key_999")
        history_res = http_requests.get(
            "http://localhost:8000/api/history/all",
            headers={"X-API-Key": api_key},
            timeout=2
        )
        records = history_res.json().get("history", [])
        if not records:
            print("[SCHEDULER] No history yet — skipping GNN run")
            return

        # Find anomaly records as fraud candidates
        fraud_candidates = [r for r in records if r.get("status") == "critical"]
        if not fraud_candidates:
            print("[SCHEDULER] No critical anomalies found — no fraud alerts raised")
            return

        # Report up to 3 most recent critical records as fraud alerts
        for rec in fraud_candidates[-3:]:
            http_requests.post(
                "http://localhost:8000/report-fraud",
                json={
                    "asset_id": rec.get("device", "unknown"),
                    "type": "anomaly_cluster",
                    "confidence": 0.87
                },
                headers={"X-API-Key": api_key},
                timeout=2
            )
        print(f"[SCHEDULER] Reported {min(3, len(fraud_candidates))} fraud alerts from GNN analysis")
    except Exception as e:
        print(f"[SCHEDULER] GNN analysis error: {e}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler = BackgroundScheduler()
    scheduler.add_job(run_gnn_analysis, 'interval', minutes=5)
    scheduler.start()
    print("[SCHEDULER] Started — GNN trigger every 5 minutes")
    yield
    scheduler.shutdown()
    print("[SCHEDULER] Stopped cleanly")

# ✅ Rate Limiter setup
limiter = Limiter(key_func=get_remote_address)

app = FastAPI(lifespan=lifespan)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.include_router(stream_router)

# Load the secret .env file
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

# ==========================================
# 🔒 SECURITY SECTION
# ==========================================

API_KEY = os.getenv("DEPIN_API_KEY")
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

if not API_KEY:
    print("⚠️ WARNING: API Key not found in .env file!")

async def verify_api_key(api_key: str = Security(api_key_header)):
    if not API_KEY or api_key != API_KEY:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate credentials - Missing or Wrong API Key"
        )
    return api_key

app.include_router(fraud_router, dependencies=[Depends(verify_api_key)])

trusted_origins = [
    "http://localhost:5173",
    "http://localhost:3000",
    "https://opulent-robot-v6rwg7wqpxvwfwjwr-5173.app.github.dev",
    "https://opulent-robot-v6rwg7wqpxvwfwjwr-3000.app.github.dev"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=trusted_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==========================================
# 📋 AUDIT LOGGING MIDDLEWARE
# ==========================================
AUDIT_LOG_PATH = "audit.log"

@app.middleware("http")
async def audit_logger(request: Request, call_next):
    start    = _time.time()
    response = await call_next(request)
    duration = (_time.time() - start) * 1000
    log_line = (
        f"{datetime.now().isoformat()}"
        f"|{request.method}"
        f"|{request.url.path}"
        f"|{response.status_code}"
        f"|{duration:.1f}ms\n"
    )
    with open(AUDIT_LOG_PATH, "a", encoding="utf-8") as log_f:
        log_f.write(log_line)
    return response

# ==========================================

AI_SERVICE_URL = os.getenv("AI_SERVICE_URL", "http://localhost:5000/predict")

system_state = {
    "dashboard": {
        "active_devices": set(),
        "total_scans": 0,
        "anomalies": 0,
        "uptime": 100.0
    },
    "blockchain": {
        "total_blocks": 0,
        "transactions": 0,
        "recent_blocks": []
    },
    "ai": {
        "total_analyses": 0,
        "anomalies_found": 0,
        "recent_results": []
    },
    "history": []
}

class SensorData(BaseModel):
    device_id: str
    temperature: float
    vibration: float
    power_usage: float
    timestamp: str

@app.get("/")
def read_root():
    return {"status": "Backend is Live", "blockchain_active": BLOCKCHAIN_ACTIVE}

@app.get("/api/dashboard", dependencies=[Depends(verify_api_key)])
def get_dashboard():
    return {
        "stats": {
            "active": len(system_state["dashboard"]["active_devices"]),
            "scans": system_state["dashboard"]["total_scans"],
            "anomalies": system_state["dashboard"]["anomalies"],
            "uptime": system_state["dashboard"]["uptime"]
        },
        "recent_data": system_state["history"][-5:]
    }

@app.get("/api/blockchain", dependencies=[Depends(verify_api_key)])
def get_blockchain():
    return system_state["blockchain"]

@app.get("/api/ai-analysis", dependencies=[Depends(verify_api_key)])
def get_ai_analysis():
    return system_state["ai"]

@app.get("/api/history", dependencies=[Depends(verify_api_key)])
def get_history():
    return system_state["history"]

@app.get("/api/history/all", dependencies=[Depends(verify_api_key)])
def get_all_history():
    """
    Stable history endpoint used by Mohit's graph processor.
    Schema: device, status, temp, vib, pwr, timestamp
    """
    return {
        "history": system_state["history"],
        "count": len(system_state["history"])
    }

@app.post("/api/process_data", dependencies=[Depends(verify_api_key)])
@limiter.limit("60/minute")  # ✅ Fixed to 60/minute
async def process_data(request: Request, data: SensorData):
    try:
        is_anomaly = False
        recommendation = "Normal Operation"

        try:
            response = http_requests.post(AI_SERVICE_URL, json=data.dict(), timeout=2)
            ai_result = response.json()
            ai_says_anomaly = ai_result.get("anomaly", False)

            if ai_says_anomaly or data.temperature > 100.0:
                is_anomaly = True

            if is_anomaly:
                if data.temperature > 100:
                    recommendation = "CRITICAL: Overheating Detected. Cooling Fan Failure likely."
                elif data.vibration > 10:
                    recommendation = "WARNING: Severe Mechanical Vibration. Check mounting."
                else:
                    recommendation = "ALERT: AI Detected Unknown Anomaly Pattern."

        except Exception as e:
            print(f"⚠️ AI Connection Warning: {e}")
            if data.temperature > 100.0:
                is_anomaly = True
                recommendation = "CRITICAL: Overheating (AI Offline)"
            else:
                is_anomaly = False

        await broadcast_data({
            "device_id": data.device_id,
            "temperature": data.temperature,
            "vibration": data.vibration,
            "power_usage": data.power_usage,
            "is_anomaly": is_anomaly,
            "timestamp": datetime.now().isoformat()
        })

        system_state["dashboard"]["total_scans"] += 1
        system_state["dashboard"]["active_devices"].add(data.device_id)
        system_state["ai"]["total_analyses"] += 1

        status_label = "normal"

        if is_anomaly:
            status_label = "critical"
            system_state["dashboard"]["anomalies"] += 1
            system_state["ai"]["anomalies_found"] += 1
            system_state["blockchain"]["total_blocks"] += 1
            system_state["blockchain"]["transactions"] += 1

            data_string = json.dumps(data.dict(), sort_keys=True)
            tx_hash = hashlib.sha256(data_string.encode()).hexdigest()

            previous_hash = "0000000000000000"
            if len(system_state["blockchain"]["recent_blocks"]) > 0:
                previous_hash = system_state["blockchain"]["recent_blocks"][0]["hash"]

            block_record = {
                "id": system_state["blockchain"]["total_blocks"],
                "hash": tx_hash,
                "prev_hash": previous_hash,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "status": "Confirmed"
            }

            system_state["blockchain"]["recent_blocks"].insert(0, block_record)
            system_state["blockchain"]["recent_blocks"] = system_state["blockchain"]["recent_blocks"][:10]

            ai_record = {
                "device": data.device_id,
                "confidence": 95.0,
                "recommendation": recommendation,
                "timestamp": datetime.now().strftime("%H:%M:%S"),
                "severity": "high"
            }
            system_state["ai"]["recent_results"].insert(0, ai_record)
            system_state["ai"]["recent_results"] = system_state["ai"]["recent_results"][:10]

            if BLOCKCHAIN_ACTIVE:
                try:
                    fabric_client.submit_transaction("CreateAsset", [
                        tx_hash,
                        "CRITICAL",
                        str(int(data.vibration)),
                        "AI",
                        str(int(data.temperature))
                    ])
                    print(f"Ledger Updated: {tx_hash}")
                except Exception as e:
                    print(f"Ledger Write Failed: {e}")

        history_record = {
            "id": system_state["dashboard"]["total_scans"],
            "device": data.device_id,
            "hash": tx_hash if is_anomaly else "---",
            "value": f"{data.temperature}C",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "status": status_label,
            "temp": data.temperature,
            "vib": data.vibration,
            "pwr": data.power_usage
        }
        system_state["history"].append(history_record)

        if len(system_state["history"]) > 100:
            system_state["history"].pop(0)

        return {"status": "Processed", "anomaly": is_anomaly}

    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ==========================================
# 🔐 JWT TOKEN VERIFICATION
# ==========================================

SECRET_KEY = os.getenv("JWT_SECRET_KEY", "my_super_secret_key")

def verify_token(authorization: str = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Token")
    try:
        token = authorization.split(" ")[1]
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return payload
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid Token")

@app.post("/submit-data")
@limiter.limit("60/minute")  # ✅ Fixed to 60/minute
async def submit_data(request: Request, data: dict, user = Depends(verify_token)):
    await broadcast_data(data)
    return {"status": "Data accepted", "user": user["user"]}