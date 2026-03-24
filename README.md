<div align="center">

# 🛡️ DePIN-Guard

### Decentralized Physical Infrastructure Network — Anomaly Detection & Trust Framework

[![Hyperledger Fabric](https://img.shields.io/badge/Hyperledger%20Fabric-2.5-2F3134?style=for-the-badge&logo=hyperledger&logoColor=white)](https://www.hyperledger.org/projects/fabric)
[![PyTorch](https://img.shields.io/badge/PyTorch-2.1-EE4C2C?style=for-the-badge&logo=pytorch&logoColor=white)](https://pytorch.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18.2-61DAFB?style=for-the-badge&logo=react&logoColor=black)](https://react.dev/)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://www.docker.com/)

_A decentralized framework for secure Industrial IoT (IIoT) monitoring and anomaly detection, built with Blockchain, AI, and a Full-Stack application._

</div>

---

## 📖 About The Project

DePIN-Guard addresses the **"trust deficit"** and security vulnerabilities in traditional, centralized IIoT systems. By integrating **Hyperledger Fabric**, **Artificial Intelligence**, and **IoT simulation**, this project creates a verifiable, tamper-proof, and intelligent monitoring platform — designed as the foundational trust layer for a **Decentralized Physical Infrastructure Network (DePIN)**.

The system captures sensor data from simulated IoT devices, anchors its integrity on a permissioned blockchain, and uses a sophisticated **Dual-AI Engine** to detect both real-time operational anomalies and systemic fraud patterns.

### How It Works

```
IoT Simulator ──► Backend API ──► AI Inference (LSTM) ──► Anomaly Decision
                      │                                        │
                      ▼                                        ▼
              Hyperledger Fabric                     WebSocket → Dashboard
              (Immutable Ledger)                    (Live Alerts & Charts)
                      │
                      ▼
              GNN Fraud Analysis
            (Scheduled Graph Check)
```

---

## ✨ Key Features

| Feature                           | Description                                                                                                                                                                                                                         |
| :-------------------------------- | :---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **🔗 Immutable Ledger**           | Hyperledger Fabric records every sensor reading as a tamper-proof, auditable transaction using Go-based chaincode (Smart Contracts).                                                                                                |
| **🧠 LSTM Autoencoder**           | A real-time deep learning model that detects operational anomalies (e.g., equipment overheating, abnormal vibration) by learning the reconstruction error of normal behavior. Uses a rolling 30-point sliding window for inference. |
| **🕸️ Graph Neural Network (GNN)** | An advanced GCN-based model that analyzes the blockchain transaction graph to detect systemic, long-term fraud patterns such as collusion rings. Runs on a scheduled interval via APScheduler.                                      |
| **📊 Real-Time Dashboard**        | A React-based frontend with protected routes, live data visualization, AI analysis page, blockchain explorer, device history, and fraud alert reporting.                                                                            |
| **🔐 Defense-in-Depth Security**  | JWT authentication, bcrypt password hashing, API rate limiting (SlowAPI), input validation against injection attacks, TLS-encrypted MQTT, and audit logging middleware.                                                             |
| **🐳 Containerized Deployment**   | Full Docker Compose orchestration — spin up the entire stack (AI, Backend, Frontend, Blockchain) with a single command.                                                                                                             |
| **📡 IoT Simulator**              | A Python-based multi-device simulator that generates realistic sensor data (temperature, vibration, power usage) with configurable anomaly injection for demo purposes.                                                             |

---

## 🏗️ Architecture & Tech Stack

### Services Overview

| Service           | Technology                   |      Port       | Purpose                                                              |
| :---------------- | :--------------------------- | :-------------: | :------------------------------------------------------------------- |
| **Frontend**      | React 18, React Router, Vite | `3000` / `5173` | User-facing dashboard with auth, live charts, and fraud alerts       |
| **Backend**       | FastAPI, Uvicorn, Python     |     `8000`      | REST API, WebSocket streaming, Fabric CLI integration, orchestration |
| **AI Service**    | Flask, PyTorch, Scikit-learn |     `5000`      | LSTM Autoencoder inference API with sliding-window buffering         |
| **Auth Service**  | FastAPI, PyJWT, bcrypt       |     `3000`      | JWT token issuance & verification microservice                       |
| **Blockchain**    | Hyperledger Fabric 2.x, Go   |     `7051`      | Permissioned ledger with custom chaincode for asset management       |
| **IoT Simulator** | Python, Requests             |        —        | Synthetic multi-device data generator with anomaly injection         |

### Full Technology Stack

| Layer              | Technologies                                                                                                            |
| :----------------- | :---------------------------------------------------------------------------------------------------------------------- |
| **Blockchain**     | Hyperledger Fabric 2.x, Go (Chaincode / Smart Contracts), `cryptogen`, `configtxgen`                                    |
| **AI / ML**        | PyTorch (LSTM Autoencoder), PyTorch Geometric (GCN / GNN), Scikit-learn (MinMaxScaler, Isolation Forest), Pandas, NumPy |
| **Backend**        | FastAPI, Flask, Uvicorn, Pydantic, python-jose (JWT), APScheduler, httpx                                                |
| **Frontend**       | React 18, React Router v6, Vite, JavaScript (JSX)                                                                       |
| **IoT & Comms**    | Python (`paho-mqtt`), Mosquitto MQTT Broker (TLS on port 8883)                                                          |
| **Security**       | bcrypt, SlowAPI (Rate Limiting), Input Validation, TLS Certificates, Audit Logging                                      |
| **Infrastructure** | Docker, Docker Compose, Shell Scripts                                                                                   |

---

## 📂 Project Structure

```
DePIN-Guard/
│
├── docker-compose.yml          # Master orchestration — runs all services
│
├── ai-service/                 # 🧠 AI Microservice
│   ├── app.py                  # Flask API — /predict endpoint
│   ├── model.py                # LSTM Autoencoder architecture (PyTorch)
│   ├── preprocessing.py        # Data scaling pipeline (MinMaxScaler)
│   ├── train.py                # LSTM training script
│   ├── train_isolation_forest.py
│   ├── lstm_autoencoder.pth    # Trained model weights
│   ├── scaler.save             # Fitted scaler artifact
│   ├── threshold.txt           # Anomaly detection threshold
│   ├── test_api.py             # Unit tests
│   ├── test_integration.py     # Integration tests
│   ├── dockerfile
│   └── requirements.txt
│
├── auth-service/               # 🔐 Authentication Microservice
│   ├── main.py                 # JWT login & token verification
│   └── requirements.txt
│
├── backend/                    # ⚙️ Core Backend API
│   ├── app.py                  # FastAPI app with CORS & route registration
│   ├── main.py                 # Entry point with JWT verification & scheduling
│   ├── fabric_manager.py       # Hyperledger Fabric CLI integration
│   ├── config/
│   │   └── settings.py         # Environment & app configuration
│   ├── models/
│   │   ├── device.py           # Device data models
│   │   └── user.py             # User data models
│   ├── routes/
│   │   ├── auth.py             # Auth endpoints
│   │   ├── data.py             # Data ingestion & history endpoints
│   │   └── devices.py          # Device management endpoints
│   ├── services/
│   │   ├── ai_service.py       # AI service client
│   │   ├── blockchain_service.py  # Blockchain interaction layer
│   │   └── mqtt_service.py     # MQTT subscriber
│   ├── dockerfile
│   └── requirements.txt
│
├── blockchain/                 # 🔗 Hyperledger Fabric Network
│   ├── configtx.yaml           # Channel & org policies
│   ├── bootstrap.sh            # Network bootstrap script
│   ├── install-fabric.sh       # Fabric binary installer
│   ├── chaincode-go/
│   │   ├── assetTransfer.go    # Chaincode entry point
│   │   └── chaincode/
│   │       ├── smartcontract.go      # Smart contract (CRUD for Assets)
│   │       └── smartcontract_test.go # Contract unit tests
│   ├── config/
│   │   └── crypto-config.yaml  # Organization & certificate definitions
│   ├── channel-artifacts/      # Generated channel transaction
│   └── system-genesis-block/   # Genesis block
│
├── frontend/                   # 🖥️ React Dashboard
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js
│   ├── dockerfile
│   └── src/
│       ├── App.jsx             # Router with Protected & Public routes
│       ├── main.jsx            # React entry point
│       ├── components/
│       │   └── layout/         # Footer, Layout components
│       └── pages/
│           ├── LoginPage.jsx       # Login form
│           ├── SignupPage.jsx      # Registration form
│           ├── DashboardPage.jsx   # Main monitoring dashboard
│           ├── AIAnalysisPage.jsx  # AI anomaly analysis view
│           ├── BlockchainPage.jsx  # Blockchain explorer
│           ├── HistoryPage.jsx     # Device data history
│           └── SettingsPage.jsx    # User settings
│
├── iot-simulator/              # 📡 IoT Device Simulator
│   ├── simulator.py            # Multi-device data generator
│   ├── ingestion_service.py    # Async high-throughput ingestion
│   └── config.py               # Simulator configuration
│
└── docker/                     # 🐳 Additional Docker configs
    ├── docker-compose.yml
    ├── Dockerfile.backend
    └── Dockerfile.frontend
```

---

## 🚀 Getting Started

### Prerequisites

- **Docker** & **Docker Compose** installed
- **Python 3.9+** (for local development)
- **Node.js 18+** (for frontend development)
- **Hyperledger Fabric binaries** (for blockchain network)

### Quick Start (Docker)

```bash
# Clone the repository
git clone https://github.com/your-org/DePIN-Guard.git
cd DePIN-Guard

# Launch the entire stack
docker-compose up --build
```

| Service            | URL                            |
| :----------------- | :----------------------------- |
| Frontend Dashboard | `http://localhost:3000`        |
| Backend API        | `http://localhost:8000`        |
| AI Inference API   | `http://localhost:5000`        |
| API Health Check   | `http://localhost:8000/health` |

### Local Development

```bash
# Backend
cd backend
pip install -r requirements.txt
uvicorn app:app --host 0.0.0.0 --port 8000 --reload

# AI Service
cd ai-service
pip install -r requirements.txt
python app.py

# Frontend
cd frontend
npm install
npm run dev

# IoT Simulator
cd iot-simulator
python simulator.py
```

---

## 🧠 AI Models

### 1. LSTM Autoencoder (Real-Time Anomaly Detection)

- **Architecture:** Encoder-Decoder LSTM with 64-dimensional embedding
- **Input:** Sliding window of 30 time steps × 2 features (temperature, vibration)
- **Training:** Trained on normal operational data; learns to reconstruct expected patterns
- **Inference:** Calculates Mean Squared Error (MSE) between input and reconstruction — if MSE exceeds the threshold stored in `threshold.txt`, the reading is flagged as an anomaly
- **Artifacts:** `lstm_autoencoder.pth`, `scaler.save`, `threshold.txt`

### 2. Graph Neural Network (Systemic Fraud Detection)

- **Architecture:** 2-layer Graph Convolutional Network (GCN) via PyTorch Geometric
- **Input:** Transaction graph built from blockchain history (Users → Assets)
- **Purpose:** Detects collusion rings, cyclic fraud patterns, and suspicious relationship clusters
- **Scheduling:** Triggered automatically via APScheduler at configurable intervals

---

## 🔐 Security Design

| Layer                    | Mechanism                                                                        |
| :----------------------- | :------------------------------------------------------------------------------- |
| **Authentication**       | JWT-based token system with 1-hour expiry, bcrypt-hashed passwords               |
| **API Protection**       | Bearer token verification on all protected endpoints                             |
| **Rate Limiting**        | SlowAPI middleware — prevents DoS via request throttling                         |
| **Input Validation**     | Server-side validation for physical bounds + injection attack detection          |
| **Transport**            | TLS-encrypted MQTT (port 8883) with mutual certificate authentication            |
| **Audit Trail**          | HTTP middleware logs every request (method, URL, status, latency) to `audit.log` |
| **Blockchain Integrity** | Hyperledger Fabric endorsement policies ensure tamper-proof data immutability    |
| **Frontend Guards**      | Protected routes with auto-logout on 401 token expiration                        |

---

## 📡 Data Contract

```json
{
  "device_id": "Device-001",
  "timestamp": "2025-10-26T10:00:00Z",
  "temperature": 45.5,
  "vibration": 30.2,
  "power_usage": 25.8
}
```

### AI Inference Response

```json
{
  "is_anomaly": false,
  "anomaly_score": 0.001234,
  "threshold": 0.045,
  "status": "active"
}
```

---

## 👥 Team

| Member        | Role                              | Responsibilities                                                                           |
| :------------ | :-------------------------------- | :----------------------------------------------------------------------------------------- |
| **Mohit**     | AI Specialist                     | LSTM Autoencoder, GNN architecture, training pipelines, preprocessing                      |
| **Prateek**   | Cybersecurity Specialist          | Auth service, TLS/SSL, input validation, rate limiting, penetration testing, audit logging |
| **Priyanshu** | Full-Stack (Backend & Blockchain) | FastAPI backend, Fabric network, chaincode, Docker orchestration, scheduler                |
| **Vineet**    | Full-Stack (Frontend & IoT)       | React dashboard, protected routes, IoT simulator, async ingestion                          |

---

## 📄 License

This project was developed as a **Final Year Project** for academic purposes.

---

<div align="center">

_Built with ❤️ by Team DePIN-Guard_

</div>

---

## 🐳 Deployment Modes

### Lab Mode (Full Docker Stack)
Runs all 4 services via Docker Compose — for validation and completeness only.
```bash
docker-compose up --build
```

| Service      | URL                       |
| :----------- | :------------------------ |
| Frontend     | `http://localhost:5173`   |
| Backend      | `http://localhost:8000`   |
| AI Service   | `http://localhost:5000`   |
| Auth Service | `http://localhost:8001`   |

### Demo Mode (Hybrid Local — Recommended for Professor Demo)
Run each service locally from known-good commands. Fabric runs in GitHub Codespace.
```bash
# 1. AI Service
cd ai-service && python app.py

# 2. Auth Service
cd auth-service && uvicorn main:app --port 8001

# 3. Backend
cd backend && uvicorn main:app --port 8000

# 4. Frontend
cd frontend && npm run dev

# 5. IoT Simulator
cd iot-simulator && python simulator.py
```

> **Note:** Fabric blockchain runs in GitHub Codespace — start it before the presentation.
> If Fabric is unavailable, the backend falls back to in-memory simulated blockchain automatically.
