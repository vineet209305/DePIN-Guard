from fastapi import APIRouter
from pydantic import BaseModel
from datetime import datetime
from typing import Optional

from database import save_fraud_alert, get_fraud_alerts, FraudAlertModel

router = APIRouter()


class FraudAlert(BaseModel):
    device_id: Optional[str] = None
    alert_type: str  # "anomaly", "suspicious_pattern", "threshold_exceeded"
    severity: str  # "low", "medium", "high"
    message: str
    confidence: Optional[float] = None
    anomaly_data: Optional[dict] = None


@router.post("/report-fraud")
async def report_fraud(alert: FraudAlert):
    """Report a fraud alert - MongoDB only"""
    try:
        fraud_record = FraudAlertModel(
            device_id=alert.device_id or "unknown",
            alert_type=alert.alert_type,
            severity=alert.severity,
            message=alert.message,
            anomaly_data=alert.anomaly_data or {},
            timestamp=datetime.utcnow()
        )
        result_id = await save_fraud_alert(fraud_record)
        return {"status": "saved", "record": fraud_record.dict(), "id": str(result_id)}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@router.get("/fraud-alerts")
async def get_all_fraud_alerts(device_id: Optional[str] = None, limit: int = 50):
    """Get fraud alerts from MongoDB"""
    try:
        alerts = await get_fraud_alerts(device_id=device_id, limit=limit)
        return {"alerts": alerts, "count": len(alerts), "source": "mongodb"}
    except Exception as e:
        return {"alerts": [], "count": 0, "error": str(e)}