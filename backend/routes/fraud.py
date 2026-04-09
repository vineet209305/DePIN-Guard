from fastapi import APIRouter
from pydantic import BaseModel
from datetime import datetime

from db import fetch_fraud_alerts, replace_fraud_alerts

router  = APIRouter()


class FraudAlert(BaseModel):
    asset_id:   str
    type:       str   # anomaly_cluster | high_frequency | injection_attempt
    confidence: float


def _read_alerts() -> list:
    return fetch_fraud_alerts()


def _write_alerts(data: list) -> None:
    replace_fraud_alerts(data)


@router.post("/report-fraud")
def report_fraud(alert: FraudAlert):
    record = {
        "timestamp":  datetime.now().isoformat(),
        "asset_id":   alert.asset_id,
        "type":       alert.type,
        "confidence": round(alert.confidence, 4),
    }
    existing = _read_alerts()
    existing.append(record)
    _write_alerts(existing)
    return {"status": "saved", "record": record}


@router.get("/fraud-alerts")
def get_fraud_alerts():
    return {"alerts": _read_alerts()}