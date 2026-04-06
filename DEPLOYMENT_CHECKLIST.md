# Deployment Checklist

Use this before deploying to production platforms.

## Pre-Deployment (Local Testing)

- [ ] All services run locally without errors
- [ ] `docker-compose up` builds successfully
- [ ] Each service has a Dockerfile
- [ ] `.env.production` files created for each service
- [ ] Health endpoints respond with 200 OK
- [ ] Frontend can communicate with backend
- [ ] Simulator can send data to backend

## Infrastructure Setup

- [ ] Choose deployment platform (Render/Railway/Heroku/etc.)
- [ ] Create accounts on each platform
- [ ] Git repo is connected and up-to-date
- [ ] Plan hostname/domain strategy

## Environment Variables

For each service, ensure production `.env` includes:

**Backend:**

- [ ] DEPIN_API_KEY (new, secure value)
- [ ] JWT_SECRET_KEY (new, secure value)
- [ ] AI_SERVICE_URL (production URL of AI service)
- [ ] CORS_ALLOWED_ORIGINS (production frontend URL)

**Auth Service:**

- [ ] JWT_SECRET_KEY (same as backend)

**AI Service:**

- [ ] FLASK_ENV=production
- [ ] PORT=5000

**Frontend:**

- [ ] VITE_API_URL (production backend URL)
- [ ] VITE_AUTH_URL (production auth URL)

## Deployment Sequence

1. **Deploy AI Service**
   - [ ] Service running and health check passes
   - [ ] Record public URL

2. **Deploy Auth Service**
   - [ ] Service running and health check passes
   - [ ] Verify JWT_SECRET_KEY matches backend

3. **Deploy Backend**
   - [ ] Set AI_SERVICE_URL to production AI URL
   - [ ] Set CORS_ALLOWED_ORIGINS to include auth and frontend URLs
   - [ ] Service running and health check passes
   - [ ] Test /health endpoint shows blockchain_status (if using)

4. **Deploy Frontend**
   - [ ] Set VITE_API_URL to production backend URL
   - [ ] Set VITE_AUTH_URL to production auth URL
   - [ ] Build completes successfully
   - [ ] Application loads and displays dashboard

## Post-Deployment Testing

- [ ] Frontend loads without errors
- [ ] Signup creates new user
- [ ] Login works with correct credentials
- [ ] Dashboard displays (even if no data)
- [ ] Can view health status of all services
- [ ] (Optional) Simulator sends data successfully

## Monitoring

Set up alerts for:

- [ ] Service uptime monitoring
- [ ] Error rate tracking
- [ ] Response time monitoring
- [ ] Log aggregation (Sentry/LogRocket optional)

## Rollback Plan

- [ ] Keep previous commit SHA for quick rollback
- [ ] Document any database migrations
- [ ] Test rollback procedure once before going live
