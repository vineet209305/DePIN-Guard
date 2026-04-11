# DePIN-Guard Implementation Plan

**Last Updated:** April 11, 2026  
**Status:** Team Review & Discussion Phase

---

## 📋 Overview

This document tracks ALL pending changes needed across services. Team reviews, discusses, and marks items as approved before implementation.

---

## 🔐 Auth Service (`auth-service/`)

### Priority: HIGH (Affects User Security)

#### 1. **Email Verification on Signup**

- **Problem:** Anyone can signup with fake email (e.g., "student@fake.com")
- **Impact:** Teacher demo may see fake student accounts
- **Solution Options:**
  - [ ] Option A: Require email OTP verification before account activation
  - [ ] Option B: Email domain whitelist (only @school.edu allowed)
  - [ ] Option C: Admin approval required for new signups
- **Files to Modify:** `auth-service/main.py`
- **Status:** ⏳ PENDING DISCUSSION

#### 2. **MongoDB Persistence for Cloud**

- **Problem:** SQLite data lost when auth-service restarts on Render
- **Impact:** All user accounts disappear on redeployment
- **Solution:** Replace SQLite with MongoDB
- **Files to Create/Modify:**
  - [ ] Create `auth-service/database.py` (like backend/database.py)
  - [ ] Modify `auth-service/requirements.txt` (add pymongo, motor)
  - [ ] Modify `auth-service/main.py` (use MongoDB instead of SQLite)
  - [ ] Add `MONGODB_URI` to `auth-service/.env`
- **Status:** ⏳ PENDING DECISION

#### 3. **User Profile Enrichment**

- **Problem:** No way to link users to devices or sensors they manage
- **Solution:** Add user-device mapping
- **Fields Needed:**
  ```
  - assigned_devices: [Device-001, Device-002]
  - role: "admin" | "operator" | "viewer"
  - permissions: ["view_dashboard", "download_data", "manage_devices"]
  ```
- **Files to Modify:** `auth-service/main.py`
- **Status:** ⏳ PENDING DISCUSSION

---

## 🖧 Backend Service (`backend/`)

### Priority: CRITICAL (Already Partially Implemented)

#### 1. **MongoDB Integration - PARTIALLY DONE ✅**

- **Status:** Database layer created, NOT YET DEPLOYED
- **What's Done:**
  - [x] `backend/database.py` created with models and CRUD
  - [x] `backend/requirements.txt` updated (pymongo, motor)
  - [x] `backend/main.py` updated (import and lifecycle)
- **What's Remaining:**
  - [ ] Remove `save_sensor_data()` for all readings (keep only anomalies) - OPTIONAL
  - [ ] Redeploy to Render with `MONGODB_URI` env var
  - [ ] Test data persistence in cloud
- **Files to Modify:** (Render deployment env vars)
- **Status:** ⏳ AWAITING RENDER REDEPLOY

#### 2. **Storage Monitoring & Export - DONE ✅**

- **Status:** Implementation complete
- **New Endpoints:**
  - [x] `GET /api/storage/status` - Real-time storage usage
  - [x] `GET /api/data/export` - Download all collected data
  - [x] `GET /api/statistics/summary` - Collection statistics
- **What's Needed:**
  - [ ] Test endpoints with actual data
  - [ ] Frontend widget to display storage status
- **Files Modified:** `backend/database.py`, `backend/main.py`
- **Status:** ✅ READY FOR TESTING

#### 3. **Daily Data Archive Job**

- **Problem:** Need automatic daily extraction of data
- **Solution:** APScheduler job runs daily at midnight
- **What's Needed:**
  - [ ] Create `backend/archive.py` with:
    - `archive_daily_data()` - exports sensor_data for yesterday
    - `upload_to_cloud()` - sends to AWS S3 or GCS
    - `cleanup_old_data()` - deletes archived data from MongoDB
  - [ ] Update `backend/main.py` - add scheduler job
  - [ ] Add cloud storage config to `.env`
- **Files to Create:** `backend/archive.py`
- **Files to Modify:** `backend/main.py`, `backend/requirements.txt`, `backend/.env`
- **Status:** ⏳ NOT STARTED - PENDING DECISION ON STORAGE (S3, GCS, Azure)

#### 4. **Blockchain Transaction Logging**

- **Problem:** Fraud alerts not consistently written to Hyperledger
- **Improvement:** Ensure every anomaly is recorded on-chain
- **Files to Modify:** `backend/main.py` (process_data endpoint)
- **Status:** ⏳ DISCUSS IF NEEDED

---

## 🎨 Frontend (`frontend/`)

### Priority: MEDIUM (UX Improvements)

#### 1. **Storage Status Dashboard Widget**

- **Problem:** Users don't see how much data is collected
- **Solution:** Dashboard widget showing storage usage
- **What's Needed:**
  - [ ] Create `frontend/src/components/StorageStatus.jsx`
  - [ ] Call `GET /api/storage/status` every 30 seconds
  - [ ] Display:
    - Progress bar (0-500MB)
    - "Storage: 450/500 MB - ALMOST FULL"
    - Red alert when > 90% usage
    - Green download button when ready
  - [ ] Create `frontend/src/components/DataExport.jsx`
    - Button to download via `GET /api/data/export`
- **Files to Create:**
  - [ ] `frontend/src/components/StorageStatus.jsx`
  - [ ] `frontend/src/components/DataExport.jsx`
- **Files to Modify:** `frontend/src/App.jsx` (add widget to dashboard)
- **Status:** ⏳ NOT STARTED

#### 2. **Data Collection Timeline**

- **Problem:** No visibility into how long data collection has been running
- **Solution:** Show "Total collected: 1.2 GB across 10 days"
- **What's Needed:**
  - [ ] Call `GET /api/statistics/summary`
  - [ ] Display in dashboard header
  - [ ] Show reading count: "86,400 readings/day"
  - [ ] Show anomaly rate: "5 anomalies detected"
- **Files to Modify:** `frontend/src/components/Dashboard.jsx`
- **Status:** ⏳ NOT STARTED

#### 3. **User Profile Page**

- **Problem:** No way to see logged-in user info or assigned devices
- **Solution:** User profile page
- **What's Needed:**
  - [ ] Create `frontend/src/pages/Profile.jsx`
  - [ ] Call `GET /api/auth/profile` (requires JWT token)
  - [ ] Display:
    - Username, Full Name, Phone
    - Last Login Time
    - Assigned Devices (once auth-service adds this)
  - [ ] Edit profile option
- **Files to Create:** `frontend/src/pages/Profile.jsx`
- **Files to Modify:** `frontend/src/App.jsx` (add route)
- **Status:** ⏳ BLOCKED - waiting for auth-service changes

#### 4. **Routing Fix - DONE ✅**

- **Status:** `frontend/vercel.json` created and deployed
- [x] Vercel SPA routing configured
- **Status:** ✅ DEPLOYED

---

## 🔗 IoT Simulator (`iot-simulator/`)

### Priority: MEDIUM (Deployment)

#### 1. **Deploy to Render** ✅ APPROVED FOR 2-3 DAYS DEMO

- **Problem:** Currently running locally only
- **Solution:** Deploy simulator to Render as background service
- **Status:** ✅ READY - See [SIMULATOR_DEPLOYMENT.md](SIMULATOR_DEPLOYMENT.md)
- **Timeline:** Deploy now, run 2-3 days, suspend when teacher approves
- **Storage Impact:** ~43 MB/day × 3 days = ~129 MB (383 MB remaining) ✅ SAFE
- **Files Already Ready:**
  - [x] `iot-simulator/Dockerfile` ✅ exists
  - [x] `iot-simulator/requirements.txt` ✅ updated
  - [x] `.env` configured with Render URLs ✅
- **What Mohit Needs to Do:**
  1. Push code to GitHub: `git push`
  2. Go to https://dashboard.render.com
  3. Create new Web Service with Docker
  4. Point to `iot-simulator/Dockerfile`
  5. Add env vars (see SIMULATOR_DEPLOYMENT.md)
  6. Deploy (~5 minutes)
- **Expected Outcome:**
  - Sends 1 sensor reading/second continuously
  - Frontend displays live data in real-time
  - MongoDB accumulates ~43 MB/day
  - Data flow: Simulator → Backend → AI → MongoDB → Frontend
- **Stopping Point:** Render dashboard → "Suspend" service (to stop data collection)

---

## 🔐 Security Improvements

### Priority: HIGH (Before Production)

#### 1. **API Rate Limiting Review**

- **Current:** 60 requests/minute per endpoint
- **Action:** [ ] Review if adequate for simulator load
- **Files:** `backend/main.py`

#### 2. **Secrets Management**

- **Current:** API keys in .env files
- **Improvement:** Move to Render Secrets Manager / Vercel Environment Variables
- **Action:** [ ] Audit all hardcoded secrets
- **Status:** ⏳ PENDING SECURITY REVIEW

---

## 📊 Deployment Checklist

### Before Teacher Demo:

- [ ] Backend MongoDB connected and tested
- [ ] Frontend storage widget working
- [ ] Auth service email verification (if Option A chosen)
- [x] ✅ IoT simulator deployed to Render (APPROVED - see SIMULATOR_DEPLOYMENT.md)
- [ ] All services accessible from Vercel frontend
- [ ] Blockchain queries working on Azure

### After Demo (Production):

- [ ] Daily archive system implemented
- [ ] MongoDB performance optimized
- [ ] User roles/permissions system
- [ ] Email notifications on alerts
- [ ] Mobile app version

---

## 🗺️ Changes Summary by Service

| Service           | Changes Needed                                | Priority | Status         |
| ----------------- | --------------------------------------------- | -------- | -------------- |
| **auth-service**  | Email verification, MongoDB, user profiles    | HIGH     | ⏳ DISCUSSION  |
| **backend**       | Test MongoDB, archive job, blockchain logging | CRITICAL | PARTIAL        |
| **frontend**      | Storage widget, profile page, timeline        | MEDIUM   | ⏳ NOT STARTED |
| **iot-simulator** | Deploy to Render                              | MEDIUM   | ✅ APPROVED    |
| **blockchain**    | Monitor operational status                    | LOW      | ✅ RUNNING     |

---

## 👥 Team Assignment Suggestions

- **Priyanshu:** Backend MongoDB redeploy, archive system
- **Mohit:** IoT simulator Render deployment, testing
- **Vineet:** Frontend storage widget, profile page
- **All:** Code review & testing

---

## 📝 Notes

- All decisions are collaborative - team discusses before implementing
- This document is living - update as decisions are made
- Link to actual PRs once implementations start
- Keep git commits focused on single items from this list
