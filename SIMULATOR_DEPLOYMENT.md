# IoT Simulator - Render Deployment Guide

## Quick Deploy Instructions for Mohit

### Step 1: Push to GitHub

```powershell
cd DePIN-Guard
git add iot-simulator/
git commit -m "IoT Simulator ready for Render deployment"
git push origin main
```

### Step 2: Create New Service on Render

1. Go to https://dashboard.render.com
2. Click **"New +"** → **"Web Service"**
3. Connect GitHub repo `DePIN-Guard`
4. Fill in:
   - **Name:** `depin-guard-simulator`
   - **Runtime:** Docker
   - **Branch:** main
   - **Dockerfile path:** `iot-simulator/Dockerfile`

### Step 3: Configure Environment

Before deploying, add these in Render dashboard:

**Environment Variables:**

```
BACKEND_URL=https://depin-guard-backend.onrender.com
DEPIN_API_KEY=546cd99c0d9b2ecf14ff85b089a2f37e500874830de918a6f0a1f4f8a5fbe95f
SIMULATOR_MODE=synthetic
```

### Step 4: Deploy Settings

- **Plan:** Free (perfectly fine for simulator)
- **Build Command:** Leave empty (uses Dockerfile)
- **Start Command:** Leave empty (uses Dockerfile CMD)

### Step 5: Click "Create Web Service"

- Wait 3-5 minutes for build
- Check logs in Render dashboard
- Should see: "✅ Sending data to backend..."

---

## Important Notes

### What it does:

- Generates 5 fictional devices (Device-001 through Device-005)
- Sends 1 sensor reading per second
- Runs CONTINUOUSLY until you stop it

### Expected logs:

```
📤 Device-001: temp=52.3°C, vibration=3.2Hz, power=245W → 200 OK
📤 Device-002: temp=48.1°C, vibration=2.8Hz, power=198W → 200 OK
📤 Device-003: temp=91.5°C, vibration=8.7Hz, power=342W ⚠️ ANOMALY
... (repeating every second)
```

### Data flow:

```
IoT Simulator (Render)
        ↓
Backend API (Render)
        ↓
AI Service (Render) → anomaly detection
        ↓
MongoDB Atlas → stores in sensor_data collection
        ↓
Frontend (Vercel) → displays live updates
```

### Stopping the simulator:

1. Go to Render dashboard
2. Select `depin-guard-simulator` service
3. Click **"Suspend"** (not delete - preserves service)
4. Data collection stops, MongoDB usage stops

---

## Test It's Working

After deployment, verify in frontend:

1. Go to https://depin-guard-frontend.vercel.app
2. Should see live sensor readings appearing
3. If using WebSocket, readings update every ~1 second
4. Check `/api/storage/status` to see data accumulating

---

## Storage Timeline (3 days)

```
Day 0: 0 MB
Day 1: ~43 MB (1 day × 86,400 readings)
Day 2: ~86 MB (2 days)
Day 3: ~129 MB (3 days)

Remaining: 512 - 129 = 383 MB (75% free) ✅

If teacher approves on Day 3 → SUSPEND simulator
Then: Export via /api/data/export before Day 12
```

---

## Troubleshooting

**If simulator crashes:**

- Check logs: should show connection to backend
- Verify `DEPIN_API_KEY` matches backend
- Verify `BACKEND_URL` is accessible

**If data not showing in frontend:**

- Check WebSocket connection
- Verify backend is receiving: `POST /api/process_data` returns 200 OK
- Check MongoDB connection on backend

**If storage grows too fast:**

- MongoDB is collecting all sensor data (intended)
- Use `/api/data/export` to backup and clear
- Or reduce reading rate in data_ingestor.py

---

**Status:** Ready to deploy! 🚀
**Estimated deployment time:** 5 minutes
**Monthly cost:** $0 (free tier)
