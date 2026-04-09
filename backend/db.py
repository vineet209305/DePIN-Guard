import os
import sqlite3
from datetime import datetime
from typing import Optional


BASE_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.join(BASE_DIR, "data")
DB_PATH = os.path.join(DATA_DIR, "depin_guard.sqlite3")


def _connect():
    os.makedirs(DATA_DIR, exist_ok=True)
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def init_db():
    with _connect() as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS sensor_readings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                device TEXT NOT NULL,
                hash TEXT,
                value TEXT,
                timestamp TEXT NOT NULL,
                status TEXT NOT NULL,
                temp REAL,
                vib REAL,
                pwr REAL,
                anomaly INTEGER NOT NULL DEFAULT 0,
                ai_source TEXT,
                ai_error TEXT,
                recommendation TEXT,
                recorded_at TEXT NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_sensor_readings_timestamp
                ON sensor_readings(timestamp);
            CREATE INDEX IF NOT EXISTS idx_sensor_readings_device
                ON sensor_readings(device);

            CREATE TABLE IF NOT EXISTS fraud_alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                asset_id TEXT NOT NULL,
                type TEXT NOT NULL,
                confidence REAL NOT NULL
            );
            """
        )
        connection.commit()


def save_sensor_reading(record: dict) -> dict:
    init_db()
    payload = {
        "device": record.get("device") or record.get("device_id") or "unknown",
        "hash": record.get("hash") or record.get("tx_hash"),
        "value": record.get("value") or "",
        "timestamp": record.get("timestamp") or datetime.now().isoformat(),
        "status": record.get("status") or "normal",
        "temp": record.get("temp") if record.get("temp") is not None else record.get("temperature"),
        "vib": record.get("vib") if record.get("vib") is not None else record.get("vibration"),
        "pwr": record.get("pwr") if record.get("pwr") is not None else record.get("power_usage"),
        "anomaly": 1 if record.get("anomaly") or record.get("status") == "critical" else 0,
        "ai_source": record.get("ai_source"),
        "ai_error": record.get("ai_error"),
        "recommendation": record.get("recommendation"),
        "recorded_at": datetime.now().isoformat(),
    }

    with _connect() as connection:
        cursor = connection.execute(
            """
            INSERT INTO sensor_readings (
                device, hash, value, timestamp, status,
                temp, vib, pwr, anomaly, ai_source,
                ai_error, recommendation, recorded_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                payload["device"],
                payload["hash"],
                payload["value"],
                payload["timestamp"],
                payload["status"],
                payload["temp"],
                payload["vib"],
                payload["pwr"],
                payload["anomaly"],
                payload["ai_source"],
                payload["ai_error"],
                payload["recommendation"],
                payload["recorded_at"],
            ),
        )
        connection.commit()
        payload["id"] = cursor.lastrowid

    return payload


def fetch_sensor_readings(limit: Optional[int] = None, newest_first: bool = False) -> list[dict]:
    init_db()
    order = "DESC" if newest_first else "ASC"
    query = f"""
        SELECT id, device, hash, value, timestamp, status, temp, vib, pwr,
               anomaly, ai_source, ai_error, recommendation, recorded_at
        FROM sensor_readings
        ORDER BY id {order}
    """
    params = []
    if limit is not None:
        query += " LIMIT ?"
        params.append(limit)

    with _connect() as connection:
        rows = connection.execute(query, params).fetchall()

    return [dict(row) for row in rows]


def get_dashboard_metrics() -> dict:
    init_db()
    with _connect() as connection:
        totals = connection.execute(
            """
            SELECT
                COUNT(*) AS scans,
                COUNT(DISTINCT device) AS active,
                COALESCE(SUM(CASE WHEN status = 'critical' THEN 1 ELSE 0 END), 0) AS anomalies
            FROM sensor_readings
            """
        ).fetchone()

    scans = int(totals["scans"] or 0)
    anomalies = int(totals["anomalies"] or 0)
    active = int(totals["active"] or 0)
    uptime = 100.0 if scans == 0 else round(max(0.0, ((scans - anomalies) / scans) * 100.0), 1)

    return {
        "active": active,
        "scans": scans,
        "anomalies": anomalies,
        "uptime": uptime,
    }


def replace_fraud_alerts(alerts: list) -> None:
    init_db()
    with _connect() as connection:
        connection.execute("DELETE FROM fraud_alerts")
        for alert in alerts:
            connection.execute(
                """
                INSERT INTO fraud_alerts (timestamp, asset_id, type, confidence)
                VALUES (?, ?, ?, ?)
                """,
                (
                    alert.get("timestamp") or datetime.now().isoformat(),
                    alert.get("asset_id") or "unknown",
                    alert.get("type") or "anomaly_cluster",
                    float(alert.get("confidence") or 0.0),
                ),
            )
        connection.commit()


def fetch_fraud_alerts() -> list[dict]:
    init_db()
    with _connect() as connection:
        rows = connection.execute(
            """
            SELECT timestamp, asset_id, type, confidence
            FROM fraud_alerts
            ORDER BY id ASC
            """
        ).fetchall()

    return [dict(row) for row in rows]