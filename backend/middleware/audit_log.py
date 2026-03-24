# backend/middleware/audit_log.py
from fastapi import Request
from datetime import datetime
import json, os

LOG_FILE = "audit_log.json"

async def audit_logging_middleware(request: Request, call_next):
    # 1. Capture request details
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "method": request.method,
        "path": request.url.path,
        "ip": request.client.host,
        "user_agent": request.headers.get("user-agent", "unknown")
    }

    # 2. Process the request
    response = await call_next(request)

    # 3. Add response status
    log_entry["status_code"] = response.status_code

    # 4. Save to audit log file
    logs = []
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r") as f:
            try:
                logs = json.load(f)
            except:
                logs = []

    logs.append(log_entry)

    # Keep only last 500 entries
    logs = logs[-500:]

    with open(LOG_FILE, "w") as f:
        json.dump(logs, f, indent=2)

    return response