from fastapi import APIRouter
from pydantic import BaseModel
from datetime import datetime
from typing import Optional

from database import save_fraud_alert, get_fraud_alerts, FraudAlertModel

router = APIRouter()


class FraudAlert(BaseModel):
    device_id: Optional[str] = None
    asset_id: str
    type: str  # anomaly_cluster | high_frequency | injection_attempt
    confidence: float


@router.post("/report-fraud")
async def report_fraud(alert: FraudAlert):
    """Report a fraud alert - MongoDB only"""
    try:
        fraud_record = FraudAlertModel(
            device_id=alert.device_id or "unknown",
            asset_id=alert.asset_id,
            type=alert.type,
            confidence=round(alert.confidence, 4),
            timestamp=datetime.now().isoformat(),
            status="active"
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