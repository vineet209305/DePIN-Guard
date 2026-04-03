# AI Service Deployment Runbook (Phase 1)

Last verified: 2026-04-03
Scope: ai-service deployment and backend integration contract

## 1. Purpose

Deploy the AI inference service in a repeatable way and verify it is compatible with backend calls to the prediction API.

## 2. Runtime Contract (Source of Truth)

Validated against:

- ai-service/app.py
- ai-service/Dockerfile
- docker-compose.yml
- backend/main.py

Expected service behavior:

- Service exposes health endpoint: GET /health
- Service exposes readiness endpoint: GET /ready
- Service exposes inference endpoint: POST /predict
- Container runtime binds to port 10000
- Backend integration URL contract: http://ai-service:10000/predict

Expected /predict response fields:

- is_anomaly (bool)
- anomaly (bool)
- status (normal or anomaly)
- loss (float)
- threshold (float)

## 3. Prerequisites

1. Docker installed and running.
2. Repository checked out with latest changes.
3. AI artifacts present in ai-service:
   - lstm_autoencoder.pth
   - scaler.save
   - threshold.txt
4. If deploying full stack, set required environment variables:
   - DEPIN_API_KEY
   - JWT_SECRET_KEY

## 4. Local Docker Deployment (Recommended Baseline)

Run from repository root:

```bash
# Start only AI service
 docker compose up --build ai-service
```

If deploying full stack:

```bash
 docker compose up --build
```

## 5. Post-Deploy Verification Checklist

Run these checks after deployment:

```bash
# Liveness
curl http://localhost:10000/health

# Readiness (artifact load + model availability)
curl http://localhost:10000/ready
```

Expected readiness response:

- HTTP 200 with {"status":"ready"}

Inference smoke test:

```bash
curl -X POST http://localhost:10000/predict \
  -H "Content-Type: application/json" \
  -d '{"temperature":35.0,"vibration":0.5,"power_usage":25.0}'
```

Expected:

- HTTP 200
- JSON includes: is_anomaly, anomaly, status, loss, threshold

Negative validation test:

```bash
curl -X POST http://localhost:10000/predict \
  -H "Content-Type: application/json" \
  -d '{"temperature":35.0}'
```

Expected:

- HTTP 400 with error message for missing required fields

## 6. Backend Integration Verification

When backend is running in docker-compose, verify backend uses:

- AI_SERVICE_URL=http://ai-service:10000/predict

Then submit test data through backend and confirm successful processing.

## 7. Rollback Plan

If deployment fails or readiness remains not_ready:

1. Roll back to previously known-good image/tag or commit.
2. Verify artifact files exist and are readable inside container.
3. Check ai-service logs for artifact loading errors.
4. Restore previous working compose/service config if contract regression is detected.

## 8. Provider-Specific Notes (Optional)

This runbook is provider-neutral. If deploying on Render or another managed platform:

1. Ensure root directory is ai-service.
2. Ensure runtime command uses gunicorn from ai-service/Dockerfile.
3. Ensure service port is 10000.
4. Run readiness and inference checks using the provider URL before integrating backend.

## 9. Operational Notes

- /ready is the authoritative probe for model readiness.
- If /health is up but /ready fails, deployment is incomplete (artifacts/config issue).
- Keep AI artifact and code versions aligned to avoid inference drift.
