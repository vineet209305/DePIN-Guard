import os
from datetime import datetime

import pandas as pd


CANONICAL_COLUMNS = [
    "timestamp",
    "device_id",
    "device_type",
    "temperature",
    "vibration",
    "power_usage",
    "pressure",
    "anomaly",
    "maintenance_required",
    "failure_type",
    "downtime_risk",
]


def _pick_column(frame: pd.DataFrame, aliases: list[str]):
    for name in aliases:
        if name in frame.columns:
            return frame[name]
    return None


def _as_numeric(series: pd.Series | None, default: float = 0.0) -> pd.Series:
    if series is None:
        return pd.Series([default] * 0)
    return pd.to_numeric(series, errors="coerce")


def canonicalize_iot_dataframe(frame: pd.DataFrame, source_name: str = "unknown") -> pd.DataFrame:
    mapped = pd.DataFrame()

    timestamp = _pick_column(frame, ["timestamp", "time", "datetime", "event_time"])
    if timestamp is None:
        mapped["timestamp"] = datetime.utcnow().isoformat()
    else:
        parsed = pd.to_datetime(timestamp, errors="coerce", utc=True)
        mapped["timestamp"] = parsed.dt.strftime("%Y-%m-%dT%H:%M:%SZ")
        mapped["timestamp"] = mapped["timestamp"].fillna(datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"))

    device_id = _pick_column(frame, ["device_id", "machine_id", "asset_id", "sensor_id"])
    if device_id is None:
        mapped["device_id"] = [f"{source_name}-device-{i}" for i in range(len(frame))]
    else:
        mapped["device_id"] = device_id.astype(str)

    device_type = _pick_column(frame, ["device_type", "sensor_type", "machine_type"])
    mapped["device_type"] = device_type.astype(str) if device_type is not None else "industrial_sensor"

    temp = _pick_column(frame, ["temperature", "temp", "temperature_c", "temp_c"])
    vib = _pick_column(frame, ["vibration", "vib", "vibration_rms"])
    pressure = _pick_column(frame, ["pressure", "press", "pressure_bar"])
    power_usage = _pick_column(frame, ["power_usage", "pwr", "energy_consumption", "power"])

    mapped["temperature"] = pd.to_numeric(temp, errors="coerce")
    mapped["vibration"] = pd.to_numeric(vib, errors="coerce")
    mapped["pressure"] = pd.to_numeric(pressure, errors="coerce")
    mapped["power_usage"] = pd.to_numeric(power_usage, errors="coerce")

    if mapped["pressure"].isna().all() and not mapped["power_usage"].isna().all():
        mapped["pressure"] = mapped["power_usage"]
    if mapped["power_usage"].isna().all() and not mapped["pressure"].isna().all():
        mapped["power_usage"] = mapped["pressure"]

    anomaly = _pick_column(frame, ["anomaly", "anomaly_flag", "is_anomaly"])
    maintenance = _pick_column(frame, ["maintenance_required", "label", "target", "failure"])
    failure_type = _pick_column(frame, ["failure_type", "fault_type", "failure_reason"])
    downtime = _pick_column(frame, ["downtime_risk", "risk_score", "failure_probability"])

    mapped["anomaly"] = pd.to_numeric(anomaly, errors="coerce").fillna(0).astype(int) if anomaly is not None else 0
    mapped["maintenance_required"] = (
        pd.to_numeric(maintenance, errors="coerce").fillna(0).astype(int)
        if maintenance is not None
        else mapped["anomaly"].astype(int)
    )
    mapped["failure_type"] = failure_type.astype(str) if failure_type is not None else "unknown"
    mapped["downtime_risk"] = pd.to_numeric(downtime, errors="coerce").fillna(0.0) if downtime is not None else 0.0

    mapped = mapped.dropna(subset=["temperature", "vibration"])

    for column in CANONICAL_COLUMNS:
        if column not in mapped.columns:
            mapped[column] = None

    return mapped[CANONICAL_COLUMNS].reset_index(drop=True)


def load_canonical_iot_csv(csv_path: str) -> pd.DataFrame:
    frame = pd.read_csv(csv_path)
    source_name = os.path.splitext(os.path.basename(csv_path))[0]
    return canonicalize_iot_dataframe(frame, source_name=source_name)
