# backend/routes/fraud.py
from fastapi import APIRouter
from pydantic import BaseModel
import json, os
from datetime import datetime

router  = APIRouter()
DB_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "fraud_reports.json")

class FraudAlert(BaseModel):
    asset_id:   str
    type:       str   # anomaly_cluster | high_frequency | injection_attempt
    confidence: float

def _read_alerts():
    if not os.path.exists(DB_FILE):
        return []
    with open(DB_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def _write_alerts(data):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

@router.post("/report-fraud")
def report_fraud(alert: FraudAlert):
    record = {
        "timestamp":  datetime.now().isoformat(),
        "asset_id":   alert.asset_id,
        "type":       alert.type,
        "confidence": round(alert.confidence, 4)
    }
    existing = _read_alerts()
    existing.append(record)
    _write_alerts(existing)
    return {"status": "saved", "record": record}

@router.get("/fraud-alerts")
def get_fraud_alerts():
    return {"alerts": _read_alerts()}
