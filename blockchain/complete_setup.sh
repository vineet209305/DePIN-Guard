#!/bin/bash
# blockchain/complete_setup.sh
# Complete Fabric network setup with signal verification at each step
# Run from inside blockchain/ folder:
#   cd ~/DePIN-Guard/blockchain
#   chmod +x complete_setup.sh
#   ./complete_setup.sh [--reset]
#
# Options:
#   --reset   Remove all generated artifacts and clear docker containers before setup

set -euo pipefail

# Parse arguments
RESET_MODE=false
if [[ "${1:-}" == "--reset" ]]; then
  RESET_MODE=true
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BLOCKCHAIN_DIR="$SCRIPT_DIR"
COMPOSE_FILE="$BLOCKCHAIN_DIR/../docker/docker-compose-custom.yaml"
CONFIG_DIR="$BLOCKCHAIN_DIR/config"
ARTIFACTS_DIR="$BLOCKCHAIN_DIR/channel-artifacts"
ORGS_DIR="$BLOCKCHAIN_DIR/organizations"
CHANNEL_NAME="mychannel"
CC_NAME="depin_cc"
CC_VERSION="1.0"
FABRIC_PROJECT_NAME="depin-fabric"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() { echo -e "${GREEN}[✓]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[!]${NC} $1"; }
log_error() { echo -e "${RED}[✗]${NC} $1"; exit 1; }
log_step() { echo -e "\n${YELLOW}Step: $1${NC}"; }

# Reset function
reset_blockchain() {
  log_step "RESET MODE: Cleaning up previous setup"
  
  log_info "Removing docker containers and volumes..."
  docker compose -p "$FABRIC_PROJECT_NAME" -f "$COMPOSE_FILE" down --volumes 2>/dev/null || true
  sleep 2
  
  log_info "Removing generated artifacts..."
  rm -rf "$ARTIFACTS_DIR"
  rm -rf "$ORGS_DIR"
  
  log_info "Blockchain setup has been reset"
  echo ""
}

# If reset mode, clean up first
if [[ "$RESET_MODE" == "true" ]]; then
  reset_blockchain
fi

wait_for_port() {
  local port="$1"
  local label="$2"
  local timeout_seconds="${3:-60}"
  local elapsed=0

  while ! (exec 3<>"/dev/tcp/localhost/$port") 2>/dev/null; do
    if [[ $elapsed -ge $timeout_seconds ]]; then
      log_error "$label on port $port not responding after ${timeout_seconds}s"
    fi
    sleep 2
    elapsed=$((elapsed + 2))
  done
}

ensure_fabric_image() {
  local image_name="$1"
  if ! docker image inspect "$image_name" >/dev/null 2>&1; then
    log_info "Pulling missing Fabric image: $image_name"
    docker pull "$image_name" || log_error "Failed to pull $image_name"
  fi
}

# ═══════════════════════════════════════════════════════════════════════════════
# STEP 1: Verify and install prerequisites
# ═══════════════════════════════════════════════════════════════════════════════
log_step "1. Verify prerequisites"

# Ensure local Fabric binaries are on PATH before checking for them.
export PATH="$BLOCKCHAIN_DIR/fabric-samples/bin:$PATH"

# Check Docker
if ! docker --version &>/dev/null; then
  log_error "Docker not found"
fi
log_info "Docker found: $(docker --version)"

# Check Docker daemon
if ! docker ps >/dev/null 2>&1; then
  log_error "Docker daemon not accessible"
fi
log_info "Docker daemon running"

# ─── Install Fabric binaries if missing ───
if ! command -v cryptogen &>/dev/null; then
  log_info "cryptogen not found, installing Fabric binaries..."
  "$BLOCKCHAIN_DIR/install-fabric.sh" binary
  export PATH="$BLOCKCHAIN_DIR/fabric-samples/bin:$PATH"
fi

if ! command -v cryptogen &>/dev/null; then
  log_error "cryptogen still not available after install"
fi
log_info "cryptogen available"

if ! command -v configtxgen &>/dev/null; then
  log_error "configtxgen not available"
fi
log_info "configtxgen available"

if ! command -v peer &>/dev/null; then
  log_error "peer CLI not available"
fi
log_info "peer CLI available"

# ─── Set PATH for remaining steps ───
export PATH=$BLOCKCHAIN_DIR/fabric-samples/bin:$PATH
export FABRIC_CFG_PATH=$BLOCKCHAIN_DIR

# ═══════════════════════════════════════════════════════════════════════════════
# STEP 2: Regenerate crypto material (organizations)
# ═══════════════════════════════════════════════════════════════════════════════
log_step "2. Generate cryptographic material"

rm -rf "$ORGS_DIR"
mkdir -p "$ORGS_DIR"

echo "Running cryptogen from: $CONFIG_DIR/crypto-config.yaml"
echo "Output to: $ORGS_DIR"

# Try cryptogen, but don't fail if it doesn't create full structure
cryptogen generate --config="$CONFIG_DIR/crypto-config.yaml" --output="$ORGS_DIR" 2>&1 | tee /tmp/cryptogen.log
CRYPTOGEN_SUCCESS=$?

if [[ $CRYPTOGEN_SUCCESS -eq 0 ]] && [[ -d "$ORGS_DIR/ordererOrganizations" ]]; then
  log_info "cryptogen completed successfully"
else
  echo "⚠️  cryptogen did not complete fully, creating directory structure manually..."
fi

# Create required directory structure regardless of cryptogen success
mkdir -p "$ORGS_DIR/ordererOrganizations/orderer.depin/orderers/orderer.orderer.depin/tls"
mkdir -p "$ORGS_DIR/ordererOrganizations/orderer.depin/msp/cacerts"
mkdir -p "$ORGS_DIR/ordererOrganizations/orderer.depin/orderers/orderer.orderer.depin/msp/tlscacerts"
mkdir -p "$ORGS_DIR/peerOrganizations/manufacturer.depin/peers/peer0.manufacturer.depin/tls"
mkdir -p "$ORGS_DIR/peerOrganizations/manufacturer.depin/msp/cacerts"
mkdir -p "$ORGS_DIR/peerOrganizations/maintenance.depin/peers/peer0.maintenance.depin/tls"
mkdir -p "$ORGS_DIR/peerOrganizations/maintenance.depin/msp/cacerts"

log_info "Directory structure ensured"

# Generate TLS certificates with explicit verification and comprehensive fallback
generate_tls_certs() {
  local cert_dir="$1"
  local cn="$2"
  
  # Ensure directory exists
  if ! mkdir -p "$cert_dir" 2>&1; then
    echo "  ✗ Failed to create directory: $cert_dir"
    return 1
  fi
  
  # If certs already exist and have content, skip
  if [[ -f "$cert_dir/server.crt" ]] && [[ -f "$cert_dir/server.key" ]] && [[ -s "$cert_dir/server.crt" ]]; then
    if [[ ! -f "$cert_dir/ca.crt" ]]; then
      cp "$cert_dir/server.crt" "$cert_dir/ca.crt"
    fi
    echo "  ✓ TLS certs already exist for $cn"
    return 0
  fi
  
  # Try to generate self-signed cert with openssl
  echo "  Generating TLS cert for: $cn"
  
  # Remove old empty/corrupt files
  rm -f "$cert_dir/server.crt" "$cert_dir/server.key" "$cert_dir/ca.crt"
  
  if command -v openssl &>/dev/null; then
    # Generate private key first
    if openssl genrsa -out "$cert_dir/server.key" 2048 2>/dev/null; then
      # Then generate certificate
      if openssl req -new -x509 -key "$cert_dir/server.key" -out "$cert_dir/server.crt" \
        -days 365 -subj "/CN=$cn" 2>/dev/null; then
        
        # Verify files exist and have content
        if [[ -s "$cert_dir/server.crt" ]] && [[ -s "$cert_dir/server.key" ]]; then
          cp "$cert_dir/server.crt" "$cert_dir/ca.crt"
          echo "    ✓ OpenSSL generation successful"
          return 0
        fi
      fi
    fi
  fi

  echo "    ✗ OpenSSL generation failed"
  return 1
}

echo "Verifying/generating TLS certificates..."

# Create each TLS cert, with explicit error reporting
for tls_entry in \
  "$ORGS_DIR/ordererOrganizations/orderer.depin/orderers/orderer.orderer.depin/tls:orderer.orderer.depin" \
  "$ORGS_DIR/peerOrganizations/manufacturer.depin/peers/peer0.manufacturer.depin/tls:peer0.manufacturer.depin" \
  "$ORGS_DIR/peerOrganizations/maintenance.depin/peers/peer0.maintenance.depin/tls:peer0.maintenance.depin"; do
  
  IFS=':' read -r cert_dir cn <<< "$tls_entry"
  echo "Processing: $cn"
  if ! generate_tls_certs "$cert_dir" "$cn"; then
    log_error "Failed to create TLS certificates for $cn at $cert_dir"
  fi
done

# Ensure the orderer CA file exists at the path used later in the script.
if [[ -f "$ORGS_DIR/ordererOrganizations/orderer.depin/orderers/orderer.orderer.depin/tls/ca.crt" ]]; then
  cp "$ORGS_DIR/ordererOrganizations/orderer.depin/orderers/orderer.orderer.depin/tls/ca.crt" \
    "$ORGS_DIR/ordererOrganizations/orderer.depin/orderers/orderer.orderer.depin/msp/tlscacerts/tlsca.orderer.depin-cert.pem"
elif [[ -f "$ORGS_DIR/ordererOrganizations/orderer.depin/orderers/orderer.orderer.depin/tls/server.crt" ]]; then
  cp "$ORGS_DIR/ordererOrganizations/orderer.depin/orderers/orderer.orderer.depin/tls/server.crt" \
    "$ORGS_DIR/ordererOrganizations/orderer.depin/orderers/orderer.orderer.depin/msp/tlscacerts/tlsca.orderer.depin-cert.pem"
fi

echo ""
echo "Final TLS certificate verification..."
CERT_COUNT=0
CERT_ERROR=0
for cert_file in \
  "$ORGS_DIR/ordererOrganizations/orderer.depin/orderers/orderer.orderer.depin/tls/server.crt" \
  "$ORGS_DIR/ordererOrganizations/orderer.depin/orderers/orderer.orderer.depin/tls/server.key" \
  "$ORGS_DIR/peerOrganizations/manufacturer.depin/peers/peer0.manufacturer.depin/tls/server.crt" \
  "$ORGS_DIR/peerOrganizations/maintenance.depin/peers/peer0.maintenance.depin/tls/server.crt"; do
  if [[ ! -f "$cert_file" ]]; then
    echo "  ✗ MISSING: $cert_file"
    CERT_ERROR=$((CERT_ERROR + 1))
  elif [[ ! -s "$cert_file" ]]; then
    echo "  ✗ EMPTY: $cert_file (file exists but has no content)"
    CERT_ERROR=$((CERT_ERROR + 1))
  else
    CERT_COUNT=$((CERT_COUNT + 1))
    echo "  ✓ Found: $(basename "$cert_file") in $(basename $(dirname "$cert_file"))"
  fi
done

if [[ $CERT_ERROR -gt 0 ]]; then
  log_error "Certificate verification failed: $CERT_ERROR certificates missing or empty"
fi

echo "Generated $CERT_COUNT valid certificates successfully"
log_info "All cryptographic material ready"

# ═══════════════════════════════════════════════════════════════════════════════
# STEP 3: Generate channel artifacts
# ═══════════════════════════════════════════════════════════════════════════════
log_step "3. Generate channel artifacts"

rm -rf "$ARTIFACTS_DIR"
mkdir -p "$ARTIFACTS_DIR"

FABRIC_CFG_PATH="$BLOCKCHAIN_DIR" configtxgen \
  -profile ManufacturerMaintenanceOrdererGenesis \
  -channelID system-channel \
  -outputBlock "$ARTIFACTS_DIR/genesis.block" || \
  log_error "genesis.block generation failed"
log_info "genesis.block created"

FABRIC_CFG_PATH="$BLOCKCHAIN_DIR" configtxgen \
  -profile ManufacturerMaintenanceChannel \
  -outputCreateChannelTx "$ARTIFACTS_DIR/${CHANNEL_NAME}.tx" \
  -channelID "$CHANNEL_NAME" || \
  log_error "mychannel.tx generation failed"
log_info "mychannel.tx created"

# Verify files exist
[[ -f "$ARTIFACTS_DIR/genesis.block" ]] || log_error "genesis.block not created"
[[ -f "$ARTIFACTS_DIR/${CHANNEL_NAME}.tx" ]] || log_error "mychannel.tx not created"
log_info "Channel artifacts verified"

# ═══════════════════════════════════════════════════════════════════════════════
# STEP 4: Start Docker containers
# ═══════════════════════════════════════════════════════════════════════════════
log_step "4. Start Docker containers"

docker compose -p "$FABRIC_PROJECT_NAME" -f "$COMPOSE_FILE" down --volumes 2>/dev/null || true
sleep 2

docker compose -p "$FABRIC_PROJECT_NAME" -f "$COMPOSE_FILE" up -d --remove-orphans || \
  log_error "docker-compose up failed"

# Wait for containers to start
for port_label in "7050:orderer" "7051:manufacturer peer" "9051:maintenance peer"; do
  IFS=':' read -r port label <<< "$port_label"
  wait_for_port "$port" "$label" 90
done

# Verify containers are running
for container in "orderer.orderer.depin" "peer0.manufacturer.depin" "peer0.maintenance.depin"; do
  if ! docker ps --format '{{.Names}}' | grep -q "$container"; then
    log_error "Container $container did not start"
  fi
done
log_info "All Fabric containers running"

# Verify ports are open
for port in 7050 7051 9051; do
  if ! (exec 3<>"/dev/tcp/localhost/$port") 2>/dev/null; then
    log_error "Port $port not responding"
  fi
done
log_info "All ports responding (7050, 7051, 9051)"

# ═══════════════════════════════════════════════════════════════════════════════
# STEP 5: Create channel and join peers
# ═══════════════════════════════════════════════════════════════════════════════
log_step "5. Create channel and join peers"

echo "Waiting briefly for orderer Raft initialization..."
sleep 5

# Paths to certificates
ORDERER_CA="$ORGS_DIR/ordererOrganizations/orderer.depin/orderers/orderer.orderer.depin/msp/tlscacerts/tlsca.orderer.depin-cert.pem"
MFR_TLS="$ORGS_DIR/peerOrganizations/manufacturer.depin/peers/peer0.manufacturer.depin/tls/ca.crt"
MFR_MSP="$ORGS_DIR/peerOrganizations/manufacturer.depin/users/Admin@manufacturer.depin/msp"
MNT_TLS="$ORGS_DIR/peerOrganizations/maintenance.depin/peers/peer0.maintenance.depin/tls/ca.crt"
MNT_MSP="$ORGS_DIR/peerOrganizations/maintenance.depin/users/Admin@maintenance.depin/msp"

# Verify certs exist
for cert in "$ORDERER_CA" "$MFR_TLS" "$MFR_MSP" "$MNT_TLS" "$MNT_MSP"; do
  if [[ ! -e "$cert" ]]; then
    log_error "Missing certificate: $cert"
  fi
done

export CORE_PEER_TLS_ENABLED=true

# Create channel
export CORE_PEER_LOCALMSPID="ManufacturerMSP"
export CORE_PEER_TLS_ROOTCERT_FILE="$MFR_TLS"
export CORE_PEER_MSPCONFIGPATH="$MFR_MSP"
export CORE_PEER_ADDRESS="localhost:7051"
export FABRIC_CFG_PATH="$BLOCKCHAIN_DIR/fabric-samples/config"

rm -f "$ARTIFACTS_DIR/${CHANNEL_NAME}.block"

# Retry channel creation if orderer is still initializing
for attempt in {1..10}; do
  peer channel create \
    -o localhost:7050 \
    --ordererTLSHostnameOverride orderer.orderer.depin \
    -c "$CHANNEL_NAME" \
    -f "$ARTIFACTS_DIR/${CHANNEL_NAME}.tx" \
    --tls --cafile "$ORDERER_CA" \
    --outputBlock "$ARTIFACTS_DIR/${CHANNEL_NAME}.block" \
    --timeout 30s && break
  
  if [[ $attempt -lt 10 ]]; then
    echo "Channel creation attempt $attempt failed; retrying in 3 seconds..."
    sleep 3
  else
    log_error "Channel creation failed after 10 attempts"
  fi
done
log_info "Channel created: $CHANNEL_NAME"

# Join Manufacturer peer
peer channel join -b "$ARTIFACTS_DIR/${CHANNEL_NAME}.block" || \
  log_error "Manufacturer peer join failed"
log_info "Manufacturer peer joined"

# Join Maintenance peer
export CORE_PEER_LOCALMSPID="MaintenanceProviderMSP"
export CORE_PEER_TLS_ROOTCERT_FILE="$MNT_TLS"
export CORE_PEER_MSPCONFIGPATH="$MNT_MSP"
export CORE_PEER_ADDRESS="localhost:9051"

peer channel join -b "$ARTIFACTS_DIR/${CHANNEL_NAME}.block" || \
  log_error "Maintenance peer join failed"
log_info "Maintenance peer joined"

# ═══════════════════════════════════════════════════════════════════════════════
# STEP 6: Deploy chaincode
# ═══════════════════════════════════════════════════════════════════════════════
log_step "6. Deploy chaincode"

ensure_fabric_image "hyperledger/fabric-ccenv:2.5"
ensure_fabric_image "hyperledger/fabric-baseos:2.5"

cd "$BLOCKCHAIN_DIR"
export FABRIC_CFG_PATH="$BLOCKCHAIN_DIR/fabric-samples/config"

# Package chaincode
peer lifecycle chaincode package ${CC_NAME}.tar.gz \
  --path ./chaincode-go/ \
  --lang golang \
  --label ${CC_NAME}_${CC_VERSION} || \
  log_error "Chaincode packaging failed"
log_info "Chaincode packaged"

# Install on Manufacturer
export CORE_PEER_LOCALMSPID="ManufacturerMSP"
export CORE_PEER_TLS_ROOTCERT_FILE="$MFR_TLS"
export CORE_PEER_MSPCONFIGPATH="$MFR_MSP"
export CORE_PEER_ADDRESS="localhost:7051"

peer lifecycle chaincode install ${CC_NAME}.tar.gz || \
  log_error "Chaincode install on Manufacturer failed"
log_info "Chaincode installed on Manufacturer"

# Install on Maintenance
export CORE_PEER_LOCALMSPID="MaintenanceProviderMSP"
export CORE_PEER_TLS_ROOTCERT_FILE="$MNT_TLS"
export CORE_PEER_MSPCONFIGPATH="$MNT_MSP"
export CORE_PEER_ADDRESS="localhost:9051"

peer lifecycle chaincode install ${CC_NAME}.tar.gz || \
  log_error "Chaincode install on Maintenance failed"
log_info "Chaincode installed on Maintenance"

# Get package ID and approve
export CORE_PEER_LOCALMSPID="ManufacturerMSP"
export CORE_PEER_TLS_ROOTCERT_FILE="$MFR_TLS"
export CORE_PEER_MSPCONFIGPATH="$MFR_MSP"
export CORE_PEER_ADDRESS="localhost:7051"

PACKAGE_ID=$(peer lifecycle chaincode queryinstalled | grep ${CC_NAME}_${CC_VERSION} | cut -d' ' -f3 | cut -d',' -f1) || \
  log_error "Failed to get package ID"
log_info "Package ID: $PACKAGE_ID"

peer lifecycle chaincode approveformyorg \
  -o localhost:7050 \
  --ordererTLSHostnameOverride orderer.orderer.depin \
  --channelID $CHANNEL_NAME \
  --name $CC_NAME \
  --version $CC_VERSION \
  --package-id $PACKAGE_ID \
  --sequence 1 \
  --tls --cafile "$ORDERER_CA" || \
  log_error "Chaincode approveformyorg on Manufacturer failed"
log_info "Chaincode approved by Manufacturer"

# Approve on Maintenance
export CORE_PEER_LOCALMSPID="MaintenanceProviderMSP"
export CORE_PEER_TLS_ROOTCERT_FILE="$MNT_TLS"
export CORE_PEER_MSPCONFIGPATH="$MNT_MSP"
export CORE_PEER_ADDRESS="localhost:9051"

peer lifecycle chaincode approveformyorg \
  -o localhost:7050 \
  --ordererTLSHostnameOverride orderer.orderer.depin \
  --channelID $CHANNEL_NAME \
  --name $CC_NAME \
  --version $CC_VERSION \
  --package-id $PACKAGE_ID \
  --sequence 1 \
  --tls --cafile "$ORDERER_CA" || \
  log_error "Chaincode approveformyorg on Maintenance failed"
log_info "Chaincode approved by Maintenance"

# Commit chaincode
export CORE_PEER_LOCALMSPID="ManufacturerMSP"
export CORE_PEER_TLS_ROOTCERT_FILE="$MFR_TLS"
export CORE_PEER_MSPCONFIGPATH="$MFR_MSP"
export CORE_PEER_ADDRESS="localhost:7051"

peer lifecycle chaincode commit \
  -o localhost:7050 \
  --ordererTLSHostnameOverride orderer.orderer.depin \
  --channelID $CHANNEL_NAME \
  --name $CC_NAME \
  --version $CC_VERSION \
  --sequence 1 \
  --tls --cafile "$ORDERER_CA" \
  --peerAddresses localhost:7051 \
  --tlsRootCertFiles "$MFR_TLS" \
  --peerAddresses localhost:9051 \
  --tlsRootCertFiles "$MNT_TLS" || \
  log_error "Chaincode commit failed"
log_info "Chaincode committed to channel"

# ═══════════════════════════════════════════════════════════════════════════════
# STEP 7: Verify backend blockchain connectivity
# ═══════════════════════════════════════════════════════════════════════════════
log_step "7. Verify backend blockchain connectivity"

HEALTH_RESPONSE=$(curl -s --max-time 5 http://127.0.0.1:8000/health || true)
if echo "$HEALTH_RESPONSE" | grep -q '"ready":true'; then
  log_info "Backend blockchain_status.ready = true ✅"
else
  if echo "$HEALTH_RESPONSE" | grep -q '"blockchain_active":true'; then
    log_warn "Backend blockchain module is loaded but not ready yet"
  else
    log_warn "Backend not responding yet; blockchain network is up"
  fi
  log_warn "You can start the backend separately and re-check /health later"
fi

# ═══════════════════════════════════════════════════════════════════════════════
# SUCCESS
# ═══════════════════════════════════════════════════════════════════════════════
echo ""
echo -e "${GREEN}══════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}✓ DePIN-Guard Fabric Network Setup COMPLETE${NC}"
echo -e "${GREEN}══════════════════════════════════════════════════════${NC}"
echo ""
echo -e "Channel:         ${YELLOW}$CHANNEL_NAME${NC}"
echo -e "Chaincode:       ${YELLOW}$CC_NAME v$CC_VERSION${NC}"
echo -e "Orderer:         ${YELLOW}localhost:7050${NC}"
echo -e "Manufacturer:    ${YELLOW}localhost:7051${NC}"
echo -e "Maintenance:     ${YELLOW}localhost:9051${NC}"
echo -e "Backend Health:  ${YELLOW}http://localhost:8000/health${NC}"
echo ""
echo "Next steps:"
echo "  1. Restart backend: cd /workspaces/DePIN-Guard/backend && uvicorn main:app --reload"
echo "  2. Create backend tunnel for Vineet: cloudflared tunnel --url http://localhost:8000"
echo "  3. Test data flow: send simulator data and check blockchain transactions"
echo ""
