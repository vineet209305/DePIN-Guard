#!/bin/bash
# blockchain/complete_setup.sh
# Complete Fabric network setup with signal verification at each step
# Run from inside blockchain/ folder:
#   cd /workspaces/DePIN-Guard/blockchain
#   chmod +x complete_setup.sh
#   ./complete_setup.sh

set -euo pipefail

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
log_error() { echo -e "${RED}[✗]${NC} $1"; exit 1; }
log_step() { echo -e "\n${YELLOW}Step: $1${NC}"; }

# ═══════════════════════════════════════════════════════════════════════════════
# STEP 1: Verify and install prerequisites
# ═══════════════════════════════════════════════════════════════════════════════
log_step "1. Verify prerequisites"

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
  ./install-fabric.sh binary
  export PATH=$PWD/fabric-samples/bin:$PATH
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

cryptogen generate --config="$CONFIG_DIR/crypto-config.yaml" --output="$ORGS_DIR" 2>&1 | tee /tmp/cryptogen.log
if [[ ! -d "$ORGS_DIR/ordererOrganizations" ]]; then
  log_error "cryptogen failed to generate ordererOrganizations"
fi
log_info "cryptogen completed"

# Verify key directory structure exists
for org_path in \
  "$ORGS_DIR/peerOrganizations/manufacturer.example.com/msp/cacerts" \
  "$ORGS_DIR/peerOrganizations/maintenance.example.com/msp/cacerts" \
  "$ORGS_DIR/ordererOrganizations/orderer.example.com/orderers/orderer.orderer.example.com/tls" \
  "$ORGS_DIR/ordererOrganizations/orderer.example.com/msp/cacerts"; do
  if [[ ! -d "$org_path" ]]; then
    log_error "Missing org path: $org_path"
  fi
done
log_info "Directory structure verified"

# Generate TLS certificates with explicit verification and fallback
generate_tls_certs() {
  local cert_dir="$1"
  local cn="$2"
  
  mkdir -p "$cert_dir"
  
  # If certs already exist, skip
  if [[ -f "$cert_dir/server.crt" ]] && [[ -f "$cert_dir/server.key" ]]; then
    echo "  ✓ TLS certs already exist for $cn"
    return 0
  fi
  
  # Generate self-signed cert
  echo "  Generating TLS cert for: $cn"
  openssl req -new -x509 -days 365 -nodes \
    -out "$cert_dir/server.crt" \
    -keyout "$cert_dir/server.key" \
    -subj "/CN=$cn" 2>&1
  
  if [[ ! -f "$cert_dir/server.crt" ]] || [[ ! -f "$cert_dir/server.key" ]]; then
    return 1
  fi
  return 0
}

echo "Verifying/generating TLS certificates..."

# Orderer TLS
if ! generate_tls_certs "$ORGS_DIR/ordererOrganizations/orderer.example.com/orderers/orderer.orderer.example.com/tls" \
  "orderer.orderer.example.com"; then
  log_error "Failed to create orderer TLS certificates"
fi

# Manufacturer peer TLS
if ! generate_tls_certs "$ORGS_DIR/peerOrganizations/manufacturer.example.com/peers/peer0.manufacturer.example.com/tls" \
  "peer0.manufacturer.example.com"; then
  log_error "Failed to create manufacturer peer TLS certificates"
fi

# Maintenance peer TLS
if ! generate_tls_certs "$ORGS_DIR/peerOrganizations/maintenance.example.com/peers/peer0.maintenance.example.com/tls" \
  "peer0.maintenance.example.com"; then
  log_error "Failed to create maintenance peer TLS certificates"
fi

# Final verification
echo "Final TLS certificate verification..."
for cert_file in \
  "$ORGS_DIR/ordererOrganizations/orderer.example.com/orderers/orderer.orderer.example.com/tls/server.crt" \
  "$ORGS_DIR/ordererOrganizations/orderer.example.com/orderers/orderer.orderer.example.com/tls/server.key" \
  "$ORGS_DIR/peerOrganizations/manufacturer.example.com/peers/peer0.manufacturer.example.com/tls/server.crt" \
  "$ORGS_DIR/peerOrganizations/maintenance.example.com/peers/peer0.maintenance.example.com/tls/server.crt"; do
  if [[ ! -f "$cert_file" ]]; then
    echo "  Missing: $cert_file"
    log_error "TLS certificate verification failed"
  else
    echo "  ✓ Found: $(basename $cert_file)"
  fi
done

log_info "All cryptographic material ready (organizations + TLS certificates)"

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
sleep 12

# Verify containers are running
for container in "orderer.example.com" "peer0.manufacturer.example.com" "peer0.maintenance.example.com"; do
  if ! docker ps --format '{{.Names}}' | grep -q "$container"; then
    log_error "Container $container did not start"
  fi
done
log_info "All Fabric containers running"

# Verify ports are open
for port in 7050 7051 9051; do
  if ! nc -z -w 2 localhost $port 2>/dev/null; then
    log_error "Port $port not responding"
  fi
done
log_info "All ports responding (7050, 7051, 9051)"

# ═══════════════════════════════════════════════════════════════════════════════
# STEP 5: Create channel and join peers
# ═══════════════════════════════════════════════════════════════════════════════
log_step "5. Create channel and join peers"

# Paths to certificates
ORDERER_CA="$ORGS_DIR/ordererOrganizations/orderer.example.com/orderers/orderer.orderer.example.com/msp/tlscacerts/tlsca.orderer.example.com-cert.pem"
MFR_TLS="$ORGS_DIR/peerOrganizations/manufacturer.example.com/peers/peer0.manufacturer.example.com/tls/ca.crt"
MFR_MSP="$ORGS_DIR/peerOrganizations/manufacturer.example.com/users/Admin@manufacturer.example.com/msp"
MNT_TLS="$ORGS_DIR/peerOrganizations/maintenance.example.com/peers/peer0.maintenance.example.com/tls/ca.crt"
MNT_MSP="$ORGS_DIR/peerOrganizations/maintenance.example.com/users/Admin@maintenance.example.com/msp"

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

peer channel create \
  -o localhost:7050 \
  --ordererTLSHostnameOverride orderer.orderer.example.com \
  -c "$CHANNEL_NAME" \
  -f "$ARTIFACTS_DIR/${CHANNEL_NAME}.tx" \
  --tls --cafile "$ORDERER_CA" \
  --outputBlock "$ARTIFACTS_DIR/${CHANNEL_NAME}.block" \
  --timeout 30s || \
  log_error "Channel creation failed"
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
  --ordererTLSHostnameOverride orderer.orderer.example.com \
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
  --ordererTLSHostnameOverride orderer.orderer.example.com \
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
  --ordererTLSHostnameOverride orderer.orderer.example.com \
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

HEALTH_RESPONSE=$(curl -s http://127.0.0.1:8000/health)
if echo "$HEALTH_RESPONSE" | grep -q '"ready":true'; then
  log_info "Backend blockchain_status.ready = true ✅"
else
  echo "$HEALTH_RESPONSE" | grep -q '"blockchain_active":true' && \
    log_info "Blockchain module loaded, checking port connectivity..." || \
    log_error "Backend not responding or blockchain module failed"
  
  # Check if ports are still open
  for port in 7050 7051 9051; do
    if ! nc -z -w 2 localhost $port 2>/dev/null; then
      log_error "Port $port unreachable"
    fi
  done
  
  log_error "Backend shows blockchain_active=true but ready=false. Check docker logs."
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
