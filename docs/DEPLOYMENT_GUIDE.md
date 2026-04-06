# DePIN-Guard Deployment Guide

Last updated: 2026-04-06

This guide covers deploying each service to cloud platforms for production use.

## Pre-Deployment Checklist

1. All Dockerfiles are configured (`backend/`, `ai-service/`, `auth-service/`, `frontend/`)
2. `.env.production` files created for each service
3. Team confirms production hostnames (e.g., `api.depinguard.com`)
4. Secrets rotated (all keys in `.env.production` are NEW, not local)
5. Each service has its own deployment platform (no shared platform)

## Deployment Options

### Option 1: Render.com (Recommended for students)

Free tier available, easy deployment.

#### Backend Deployment

1. Go to https://dashboard.render.com
2. Click New → Web Service
3. Connect GitHub repo
4. Configure:
   - Name: `depin-backend`
   - Root directory: `backend`
   - Build command: `pip install -r requirements.txt`
   - Start command: `uvicorn main:app --host 0.0.0.0 --port 8000`
   - Region: closest to your location
5. Add Environment Variables from `backend/.env.production`
6. Deploy

7. After deploy, you get a URL like: `https://depin-backend.onrender.com`

#### Auth Deployment

1. Click New → Web Service (again)
2. Configure:
   - Name: `depin-auth`
   - Root directory: `auth-service`
   - Build command: `pip install -r requirements.txt`
   - Start command: `uvicorn main:app --host 0.0.0.0 --port 8001`
3. Add Environment Variables from `auth-service/.env.production`
4. Deploy → get URL like: `https://depin-auth.onrender.com`

#### AI Deployment

1. Click New → Web Service
2. Configure:
   - Name: `depin-ai`
   - Root directory: `ai-service`
   - Build command: `pip install -r requirements.txt`
   - Start command: `gunicorn app:app --bind 0.0.0.0:5000 --workers 1 --threads 2`
3. Add Environment Variables from `ai-service/.env.production`
4. Deploy → get URL like: `https://depin-ai.onrender.com`

#### Frontend Deployment (Vercel - Free Tier)

1. Go to https://vercel.com
2. Click New Project
3. Import GitHub repo
4. Configure:
   - Framework: Vite
   - Root directory: `frontend`
   - Build: `npm run build`
   - Output: `dist`
5. Add Environment Variables:
   - `VITE_API_URL=https://depin-backend.onrender.com`
   - `VITE_AUTH_URL=https://depin-auth.onrender.com`
6. Deploy → get URL like: `https://depin-frontend.vercel.app`

### Option 2: Railway.app

1. Sign up at https://railway.app
2. New Project → GitHub
3. Select repo and branch
4. Configure per service (similar to Render)
5. Set environment variables
6. Deploy

### Option 3: Heroku (Eco Dynos - paid)

1. Heroku no longer offers free tier fully
2. Eco Dynos: $5/month per service (cheapest option for 4 services = $20/month)
3. Deploy via `heroku create`, `git push heroku main`

---

## Post-Deployment Steps

1. Verify all health endpoints:
   - `https://depin-backend.onrender.com/health`
   - `https://depin-auth.onrender.com/health`
   - `https://depin-ai.onrender.com/health`

2. Update `backend/.env` with production URLs:

   ```
   AI_SERVICE_URL=https://depin-ai.onrender.com/predict
   CORS_ALLOWED_ORIGINS=https://depin-frontend.vercel.app,https://depin-auth.onrender.com
   ```

3. Restart backend service

4. Test end-to-end flow:
   - Signup on frontend → should work
   - Login → should work
   - Send data from simulator → should appear in dashboard

5. Monitor logs:
   - Render: Dashboard → Service Logs
   - Vercel: Deployments → Overview
   - Railway: Logs tab

---

## Blockchain Deployment (Advanced)

If deploying Hyperledger Fabric:

1. Fabric cannot run on Render/Vercel (requires Docker-enabled host)
2. Use a dedicated server:
   - AWS EC2 (t3.medium, $20/month)
   - DigitalOcean Droplet (2GB, $6/month)
   - Linode Nanode ($5/month)

3. Update `FABRIC_ORDERER_ADDRESS` and `FABRIC_PEER*_ADDRESS` to your server IPs

---

## Cost Breakdown

**Minimum Production Setup (Student Budget):**

1. Render Backend: Free tier (sleeping, slows after 15 min of inactivity)
2. Render Auth: Free tier
3. Render AI: Free tier
4. Vercel Frontend: Free tier
5. **Total: $0/month** (with limitations) OR **$20-40/month** (with reliability)

**Recommended Setup (Reliable):**

1. Render Backend: $7/month
2. Render Auth: $7/month
3. Render AI: $7/month
4. Vercel Frontend: $20/month (Pro)
5. **Total: ~$41/month**

---

## Troubleshooting

**Service not responding:**

- Check logs for errors
- Verify environment variables are set correctly
- Ensure health check endpoints return 200 OK

**CORS errors:**

- Verify `CORS_ALLOWED_ORIGINS` includes frontend URL
- Restart backend after updating

**Blockchain unreachable:**

- If using local Fabric, ensure server has Docker running
- Update `FABRIC_*_ADDRESS` to correct hostnames/IPs

**Database issues (if migrating):**

- Backend currently uses JSON files (`data/fraud_reports.json`)
- Migrate to PostgreSQL/MongoDB if scaling
