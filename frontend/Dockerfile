# Multi-stage build for React + Vite
# Stage 1: Build
FROM node:20-alpine AS builder

WORKDIR /app

# Accept build arguments for Vite environment variables
ARG VITE_API_URL=http://localhost:8000
ARG VITE_API_KEY=''
ARG VITE_AUTH_URL=http://localhost:8001

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci

# Copy application code
COPY . .

# Build the Vite app (creates dist/) with environment variables
RUN VITE_API_URL=${VITE_API_URL} VITE_API_KEY=${VITE_API_KEY} VITE_AUTH_URL=${VITE_AUTH_URL} npm run build

# Stage 2: Serve
FROM node:20-alpine

WORKDIR /app

# Install serve to run the built app
RUN npm install -g serve

# Copy built files from builder stage
COPY --from=builder /app/dist ./dist

# Expose port
EXPOSE 5173

# Health check - verify web server is responding
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:5173/ || exit 1

# Serve the built app
CMD ["serve", "-s", "dist", "-l", "5173"]
