"""MongoDB database connection and models for DePIN-Guard"""
import os
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from motor.motor_asyncio import AsyncClient, AsyncDatabase
import logging

logger = logging.getLogger("depin_guard.database")

# MongoDB connection
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017/depin_guard")
mongodb_client: Optional[AsyncClient] = None
db: Optional[AsyncDatabase] = None


async def connect_to_mongo():
    """Connect to MongoDB"""
    global mongodb_client, db
    try:
        mongodb_client = AsyncClient(MONGODB_URI)
        # Verify connection
        await mongodb_client.admin.command('ping')
        db = mongodb_client["depin_guard"]
        logger.info("✅ Connected to MongoDB")
        
        # Create indexes
        await create_indexes()
    except Exception as e:
        logger.error(f"❌ MongoDB connection failed: {e}")
        raise


async def close_mongo_connection():
    """Close MongoDB connection"""
    global mongodb_client
    if mongodb_client:
        mongodb_client.close()
        logger.info("🔌 MongoDB connection closed")


async def create_indexes():
    """Create database indexes"""
    try:
        sensor_data_col = db["sensor_data"]
        await sensor_data_col.create_index("device_id")
        await sensor_data_col.create_index("timestamp")
        await sensor_data_col.create_index([("timestamp", -1)])
        
        fraud_alerts_col = db["fraud_alerts"]
        await fraud_alerts_col.create_index("device_id")
        await fraud_alerts_col.create_index("timestamp")
        await fraud_alerts_col.create_index([("timestamp", -1)])
        
        logger.info("✅ Database indexes created")
    except Exception as e:
        logger.error(f"Index creation error: {e}")


# Pydantic Models
class SensorDataModel(BaseModel):
    """Sensor data model"""
    device_id: str
    temperature: float
    vibration: float
    power_usage: float
    pressure: Optional[float] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class AnomalyResultModel(BaseModel):
    """AI anomaly detection result"""
    device_id: str
    is_anomaly: bool
    anomaly: bool  # Keep both fields for compatibility
    status: str  # "normal" or "anomaly"
    loss: float
    threshold: float
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class FraudAlertModel(BaseModel):
    """Fraud alert model"""
    device_id: str
    alert_type: str  # "anomaly", "suspicious_pattern", "threshold_exceeded"
    severity: str  # "low", "medium", "high"
    message: str
    anomaly_data: Optional[dict] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


# Database operations
async def save_sensor_data(data: SensorDataModel):
    """Save sensor data to MongoDB"""
    try:
        result = await db["sensor_data"].insert_one(data.dict())
        logger.info(f"✅ Sensor data saved: {result.inserted_id}")
        return result.inserted_id
    except Exception as e:
        logger.error(f"Error saving sensor data: {e}")
        raise


async def save_fraud_alert(alert: FraudAlertModel):
    """Save fraud alert to MongoDB"""
    try:
        result = await db["fraud_alerts"].insert_one(alert.dict())
        logger.info(f"✅ Fraud alert saved: {result.inserted_id}")
        return result.inserted_id
    except Exception as e:
        logger.error(f"Error saving fraud alert: {e}")
        raise


async def get_recent_sensor_data(device_id: str, limit: int = 100):
    """Get recent sensor data for a device"""
    try:
        data = await db["sensor_data"].find(
            {"device_id": device_id}
        ).sort("timestamp", -1).limit(limit).to_list(length=limit)
        return data
    except Exception as e:
        logger.error(f"Error retrieving sensor data: {e}")
        return []


async def get_fraud_alerts(device_id: Optional[str] = None, limit: int = 50):
    """Get fraud alerts"""
    try:
        query = {} if not device_id else {"device_id": device_id}
        alerts = await db["fraud_alerts"].find(query).sort("timestamp", -1).limit(limit).to_list(length=limit)
        return alerts
    except Exception as e:
        logger.error(f"Error retrieving fraud alerts: {e}")
        return []


async def get_device_stats(device_id: str):
    """Get statistics for a device"""
    try:
        # Total readings
        total_readings = await db["sensor_data"].count_documents({"device_id": device_id})
        
        # Anomalies detected
        anomaly_count = await db["fraud_alerts"].count_documents({
            "device_id": device_id,
            "alert_type": "anomaly"
        })
        
        # Recent data
        recent = await db["sensor_data"].find_one(
            {"device_id": device_id},
            sort=[("timestamp", -1)]
        )
        
        return {
            "device_id": device_id,
            "total_readings": total_readings,
            "anomalies_detected": anomaly_count,
            "last_reading": recent["timestamp"] if recent else None
        }
    except Exception as e:
        logger.error(f"Error getting device stats: {e}")
        return {}
