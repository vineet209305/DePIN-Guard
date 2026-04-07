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

DePIN-Guard addresses the **"trust deficit"** in traditional IIoT systems by integrating **Blockchain**, **AI**, and **IoT** to create a verifiable, tamper-proof monitoring platform for industrial assets.

The system simulates IoT sensor data, records it immutably on Hyperledger Fabric, and uses AI to detect real-time anomalies and systemic fraud patterns.

### How It Works

```
IoT Simulator ──► Backend API ──► AI Inference ──► Anomaly Detection
                      │
                      ▼
              Blockchain Ledger ──► Fraud Analysis ──► Dashboard Alerts
```

---

## ✨ Key Features

| Feature                       | Description                                             |
| :---------------------------- | :------------------------------------------------------ |
| **🔗 Immutable Ledger**       | Hyperledger Fabric ensures tamper-proof data recording  |
| **🧠 AI Anomaly Detection**   | LSTM Autoencoder for real-time operational anomalies    |
| **🕸️ Fraud Pattern Analysis** | Graph Neural Network detects systemic fraud             |
| **📊 Real-Time Dashboard**    | React-based UI with live charts and alerts              |
| **🔐 Security**               | JWT authentication, rate limiting, and input validation |
| **🐳 Easy Deployment**        | Docker Compose for full-stack orchestration             |

---

## 🏗️ Technology Stack

| Component          | Technology             |
| :----------------- | :--------------------- |
| **Blockchain**     | Hyperledger Fabric 2.x |
| **AI/ML**          | PyTorch, LSTM, GNN     |
| **Backend**        | FastAPI, Python        |
| **Frontend**       | React 18, Vite         |
| **IoT**            | MQTT, Python Simulator |
| **Infrastructure** | Docker, Docker Compose |

---

## 🚀 Getting Started

### Prerequisites

- Docker & Docker Compose
- Python 3.9+ (optional for local dev)
- Node.js 18+ (optional for local dev)

### Quick Start

```bash
git clone https://github.com/MohitSingh-2335/DePIN-Guard.git
cd DePIN-Guard
docker-compose up --build
```

| Service   | URL                     |
| :-------- | :---------------------- |
| Dashboard | `http://localhost:5173` |
| API       | `http://localhost:8000` |

### Persistence and data ingest

- Backend sensor history and fraud alerts are now stored in SQLite at `backend/data/depin_guard.sqlite3`.
- To replay recorded sensor traces, set `SIMULATOR_MODE=replay` and optionally `SIMULATOR_DATA_FILE` to a CSV or JSON export.
- The backend dashboard and history endpoints now read from the database, so data remains available after restarts.
- Sensor payloads are signed with the shared API key and the backend rejects unsigned or stale readings.

---

## 📂 Project Structure

```
DePIN-Guard/
├── ai-service/          # AI inference service
├── auth-service/        # Authentication microservice
├── backend/             # Main API and orchestration
├── blockchain/          # Hyperledger Fabric network
├── frontend/            # React dashboard
├── iot-simulator/       # IoT device simulator
└── docker-compose.yml   # Full-stack deployment
```

---

## 🤝 Contributing

Contributions are welcome! Please open an issue or submit a pull request.

## 📄 License

This project is licensed under the MIT License.
