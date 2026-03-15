from fastapi import FastAPI, HTTPException, Security, status, Depends, Header, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import APIKeyHeader
from pydantic import BaseModel
from routes.stream import broadcast_data, router as stream_router
import jwt, os, hashlib, json
import requests as http_requests
from datetime import datetime
from dotenv import load_dotenv
from apscheduler.schedulers.background import BackgroundScheduler
from contextlib import asynccontextmanager

try:
    from fabric_manager import fabric_client
    BLOCKCHAIN_ACTIVE = True
except ImportError:
    BLOCKCHAIN_ACTIVE = False
    print("Fabric Manager not found. Blockchain integration disabled.")


def run_gnn_analysis():
    # Week 11 replaces this stub with a real GNN call
    print("[SCHEDULER] GNN analysis triggered — scanning for fraud patterns...")

@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler = BackgroundScheduler()
    scheduler.add_job(run_gnn_analysis, 'interval', minutes=5)
    scheduler.start()
    print("[SCHEDULER] Started — GNN trigger every 5 minutes")
    yield
    scheduler.shutdown()
    print("[SCHEDULER] Stopped cleanly")

app = FastAPI(lifespan=lifespan)
app.include_router(stream_router)

# Load the secret .env file
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

# ==========================================
# 🔒 SECURITY SECTION
# ==========================================

# 1. API KEY CONFIGURATION
# API_KEY = "my-secret-depin-key-123"  # <--- The Secret Password
API_KEY = os.getenv("DEPIN_API_KEY")
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

if not API_KEY:
    print("⚠️ WARNING: API Key not found in .env file!")

async def verify_api_key(api_key: str = Security(api_key_header)):
    if api_key != API_KEY:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate credentials - Missing or Wrong API Key"
        )
    return api_key

# 2. CORS CONFIGURATION (Trusted Origins)
# ⚠️ REPLACE THE URL BELOW WITH YOUR ACTUAL FRONTEND URL (Port 5173) ⚠️
trusted_origins = [
    "http://localhost:5173",  # Local testing
    "http://localhost:3000",
    "https://opulent-robot-v6rwg7wqpxvwfwjwr-5173.app.github.dev", 
    "https://opulent-robot-v6rwg7wqpxvwfwjwr-3000.app.github.dev"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=trusted_origins, # Only allow these guys
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==========================================

AI_SERVICE_URL = os.getenv("AI_SERVICE_URL", "http://depin_ai_service:5000/predict")

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

# 🔒 SECURED ENDPOINTS (Require API Key)
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
        "count":   len(system_state["history"])
    }

# Note: We kept process_data OPEN for the simulator to work easily. 
# If you want to secure it, add dependencies=[Depends(verify_api_key)] here too.
@app.post("/api/process_data") 
async def process_data(data: SensorData):
    try:
        # A. AI ANALYSIS & HYBRID CHECK
        is_anomaly = False
        recommendation = "Normal Operation"
        
        try:
            # 1. Ask the AI Model
            response = http_requests.post(AI_SERVICE_URL, json=data.dict(), timeout=2)
            ai_result = response.json()
            ai_says_anomaly = ai_result.get("anomaly", False)
            
            # 2. Apply Hybrid Logic (AI + Hard Rules)
            if ai_says_anomaly or data.temperature > 100.0:
                is_anomaly = True
            
            # 3. Set Recommendation
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
            
            # ==========================================
            # 🔗 REAL BLOCKCHAIN LINKING LOGIC
            # ==========================================
            
            # 1. Calculate the Hash for the NEW block
            data_string = json.dumps(data.dict(), sort_keys=True)
            tx_hash = hashlib.sha256(data_string.encode()).hexdigest()
            
            # 2. Find the Previous Hash (Link the Chain)
            previous_hash = "0000000000000000" # Default for the very first block (Genesis)
            
            # If we already have blocks, grab the hash of the most recent one (Index 0)
            if len(system_state["blockchain"]["recent_blocks"]) > 0:
                previous_hash = system_state["blockchain"]["recent_blocks"][0]["hash"]

            # 3. Create the New Block
            block_record = {
                "id": system_state["blockchain"]["total_blocks"],
                "hash": tx_hash,
                "prev_hash": previous_hash, # <--- NOW IT IS REAL!
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "status": "Confirmed"
            }
            
            # 4. Add to the chain
            system_state["blockchain"]["recent_blocks"].insert(0, block_record)
            # Keep only last 10 blocks in memory
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
                    # fabric_client.submit_transaction("CreateAsset", [tx_hash, "ANOMALY", "CRITICAL", "AI", str(data.temperature)])
                    # Format: [ID, Status(Text), Vibration(Int), Source(Text), Temperature(Int)]
                    fabric_client.submit_transaction("CreateAsset", [
                        tx_hash, 
                        "CRITICAL",           # Fits in 'Color' slot (String)
                        str(int(data.vibration)),  # Fits in 'Size' slot (Must be Int)
                        "AI",                 # Fits in 'Owner' slot (String)
                        str(int(data.temperature)) # Fits in 'Value' slot (Must be Int)
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
# 🔐 JWT TOKEN VERIFICATION (Week 6)
# ==========================================

SECRET_KEY = os.getenv("JWT_SECRET_KEY", "my_super_secret_key")

def verify_token(authorization: str = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Token")
    try:
        token = authorization.split(" ")[1]
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return payload
    except:
        raise HTTPException(status_code=401, detail="Invalid Token")

@app.post("/submit-data")
async def submit_data(data: dict, user = Depends(verify_token)):
    await broadcast_data(data)
    return {"status": "Data accepted", "user": user["user"]}
