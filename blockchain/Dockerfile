# Use Ubuntu as base image for Hyperledger Fabric
FROM ubuntu:22.04

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    git \
    docker.io \
    docker-compose \
    nodejs \
    npm \
    python3 \
    python3-pip \
    jq \
    openssl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install Docker CLI for the setup (if needed)
RUN docker --version || echo "Docker daemon will be available from host"

# Copy blockchain directory
COPY . /app/

# Make scripts executable
RUN chmod +x /app/complete_setup.sh && \
    chmod +x /app/install-fabric.sh && \
    chmod +x /app/bootstrap.sh && \
    chmod +x /app/createchannel.sh && \
    chmod +x /app/deploy_chaincode.sh

# Set environment variables for Fabric
ENV PATH="/app/fabric-samples/bin:${PATH}"
ENV FABRIC_CFG_PATH="/app"
ENV COMPOSE_PROJECT_NAME="depin-fabric"

# Download Fabric binaries during build
RUN /app/install-fabric.sh binary

# Expose Hyperledger Fabric ports
EXPOSE 7050 7051 7052 7053 7054 7055 7056 7057 7058 7059

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:7050 || exit 1

# Run the blockchain setup
ENTRYPOINT ["/bin/bash", "-c", "/app/complete_setup.sh --reset && tail -f /dev/null"]
