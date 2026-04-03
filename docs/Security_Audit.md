# DePIN-Guard Security Audit (Implementation-Aligned)

Last verified: 2026-04-03
Audit type: source-level implementation review

## 1. Scope and Evidence

This document summarizes security controls observed in current runtime code and deployment manifests.

Validated against:

- backend/main.py
- auth-service/main.py
- iot-simulator/simulator.py
- docker/mosquitto/mosquitto.conf
- docker/docker-compose.yml
- docker/docker-compose-custom.yaml
- docker-compose.yml
- .gitignore

## 2. Authentication and Authorization

Observed controls:

- Backend API key guard exists via X-API-Key dependency for protected backend routes.
- Fraud routes are included with API key dependency.
- Backend also includes JWT token verification for /submit-data.
- Auth service issues JWTs with 1 hour expiry.
- Auth service uses bcrypt password hashing for stored credentials.

Important implementation note:

- Authorization model is mixed, not single-mode:
  - X-API-Key on many backend endpoints.
  - JWT verification path on /submit-data.

## 3. Transport Security

Observed controls:

- MQTT broker config enforces TLS listener on 8883.
- MQTT broker requires client certificates (mTLS) and anonymous access is disabled.
- Broker cert and key references are present and mapped in docker cert path.

Caution:

- Certificate lifecycle and rotation workflow are not documented in this file.
- Private key handling must remain outside public source control workflows.

## 4. API Security Controls

Observed controls:

- Backend uses request rate limiting (60/minute per IP) on ingestion endpoints.
- Backend request schema validation is enforced through Pydantic models for typed endpoints.
- CORS is allowlist-based in backend.

Accuracy note:

- Current CORS allowlist includes localhost and tunnel domains for development/testing.
- This is not equivalent to a strict production-only origin policy.

## 5. Logging and Auditability

Observed controls:

- Backend middleware writes request audit entries with timestamp, method, path, status, and duration.
- Audit log file pattern is excluded in .gitignore (\*.log).

Gaps:

- No documented centralized log shipping/retention policy in this file.

## 6. Secret Management Status

Observed controls:

- .env is excluded by .gitignore.
- Runtime reads sensitive values from environment variables.

Gaps and risks:

- Code-level fallback secrets exist when environment values are missing (backend/auth service).
- This means "never hardcoded" cannot be claimed as an absolute guarantee.

## 7. Security Test Statement (What Is Verified vs Not Verified)

Verified from source:

- Presence of auth checks, rate limiting middleware, and validation structures.
- Presence of mTLS broker config and cert references.

Not verified in this document:

- Live penetration test execution logs.
- Environment-specific runtime hardening (host firewall, secret manager policy, IDS/WAF controls).

## 8. Known Limitations

1. Mixed auth model complexity increases misconfiguration risk.
2. Development CORS origins and tunnel URLs are still present in runtime defaults.
3. Default secret fallback behavior should be removed for strict production posture.
4. Local sqlite + demo admin account in auth service is not enterprise IAM.
5. Rate limiting state resets on process restart.

## 9. Recommended Hardening Actions

P0:

1. Remove default fallback secrets and fail fast when required env values are missing.
2. Split CORS policy by environment (dev vs production allowlists).
3. Standardize endpoint auth policy and document endpoint-by-endpoint requirements.

P1:

4. Add reproducible security test appendix with commands, date, environment, and expected status codes.
5. Add certificate rotation and key management policy for MQTT TLS materials.

P2:

6. Add centralized logging, retention, and correlation ID guidance for multi-service tracing.

## 10. Compliance Statement

This document is implementation-aligned and intentionally avoids blanket security guarantees.
It should be treated as a current-state control summary, not as certification evidence.
