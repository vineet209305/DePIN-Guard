#!/bin/bash
# blockchain/init_only.sh
# Only generate certificates and channel artifacts (no container waiting)
# For use in blockchain-init container

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BLOCKCHAIN_DIR="$SCRIPT_DIR"
CONFIG_DIR="$BLOCKCHAIN_DIR/config"
ARTIFACTS_DIR="$BLOCKCHAIN_DIR/channel-artifacts"
ORGS_DIR="$BLOCKCHAIN_DIR/organizations"
CHANNEL_NAME="mychannel"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() { echo -e "${GREEN}[✓]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[!]${NC} $1"; }
log_error() { echo -e "${RED}[✗]${NC} $1"; exit 1; }
log_step() { echo -e "\n${YELLOW}═══ Step: $1 ═══${NC}"; }

# ═══════════════════════════════════════════════════════════════════════════════
# STEP 1: Verify prerequisites
# ═══════════════════════════════════════════════════════════════════════════════
log_step "1. Verify Prerequisites"

export PATH="$BLOCKCHAIN_DIR/fabric-samples/bin:$PATH"

# Check required binaries
for cmd in cryptogen configtxgen; do
  if ! command -v $cmd &>/dev/null; then
    log_error "$cmd not found in PATH"
  fi
  log_info "$cmd available"
done

# ═══════════════════════════════════════════════════════════════════════════════
# STEP 2: Generate cryptographic material
# ═══════════════════════════════════════════════════════════════════════════════
log_step "2. Generate Cryptographic Material"

rm -rf "$ORGS_DIR"
mkdir -p "$ORGS_DIR"

echo "Running cryptogen with config: $CONFIG_DIR/crypto-config.yaml"
cryptogen generate --config="$CONFIG_DIR/crypto-config.yaml" --output="$ORGS_DIR" 2>&1 || \
  log_error "cryptogen failed"

# Create required directory structure
mkdir -p "$ORGS_DIR/ordererOrganizations/orderer.example.com/orderers/orderer.orderer.example.com/tls"
mkdir -p "$ORGS_DIR/ordererOrganizations/orderer.example.com/msp/cacerts"
mkdir -p "$ORGS_DIR/ordererOrganizations/orderer.example.com/msp/tlscacerts"
mkdir -p "$ORGS_DIR/peerOrganizations/manufacturer.example.com/peers/peer0.manufacturer.example.com/tls"
mkdir -p "$ORGS_DIR/peerOrganizations/manufacturer.example.com/msp/cacerts"
mkdir -p "$ORGS_DIR/peerOrganizations/maintenance.example.com/peers/peer0.maintenance.example.com/tls"
mkdir -p "$ORGS_DIR/peerOrganizations/maintenance.example.com/msp/cacerts"

log_info "Directory structure created"

# Ensure cert files exist with proper permissions
chmod -R 755 "$ORGS_DIR"
chmod -R 644 "$ORGS_DIR"/**/tls/*.crt 2>/dev/null || true
chmod -R 644 "$ORGS_DIR"/**/tls/*.pem 2>/dev/null || true
chmod -R 644 "$ORGS_DIR"/**/msp/**/*.pem 2>/dev/null || true

log_info "Cryptographic material generated successfully"

# Verify critical certs
required_certs=(
  "$ORGS_DIR/ordererOrganizations/orderer.example.com/orderers/orderer.orderer.example.com/tls/server.crt"
  "$ORGS_DIR/ordererOrganizations/orderer.example.com/orderers/orderer.orderer.example.com/tls/server.key"
  "$ORGS_DIR/peerOrganizations/manufacturer.example.com/peers/peer0.manufacturer.example.com/tls/server.crt"
  "$ORGS_DIR/peerOrganizations/maintenance.example.com/peers/peer0.maintenance.example.com/tls/server.crt"
)

for cert in "${required_certs[@]}"; do
  [[ -f "$cert" ]] || log_error "Missing required cert: $cert"
done

log_info "All required certificates verified"

# ═══════════════════════════════════════════════════════════════════════════════
# STEP 3: Generate channel artifacts
# ═══════════════════════════════════════════════════════════════════════════════
log_step "3. Generate Channel Artifacts"

rm -rf "$ARTIFACTS_DIR"
mkdir -p "$ARTIFACTS_DIR"

export FABRIC_CFG_PATH="$BLOCKCHAIN_DIR"

echo "Generating genesis.block..."
FABRIC_CFG_PATH="$BLOCKCHAIN_DIR" configtxgen \
  -profile ManufacturerMaintenanceOrdererGenesis \
  -channelID system-channel \
  -outputBlock "$ARTIFACTS_DIR/genesis.block" || \
  log_error "genesis.block generation failed"

log_info "genesis.block created"

echo "Generating ${CHANNEL_NAME}.tx..."
FABRIC_CFG_PATH="$BLOCKCHAIN_DIR" configtxgen \
  -profile ManufacturerMaintenanceChannel \
  -outputCreateChannelTx "$ARTIFACTS_DIR/${CHANNEL_NAME}.tx" \
  -channelID "$CHANNEL_NAME" || \
  log_error "channel tx generation failed"

log_info "mychannel.tx created"

# Verify artifacts
[[ -f "$ARTIFACTS_DIR/genesis.block" ]] || log_error "genesis.block not found"
[[ -f "$ARTIFACTS_DIR/${CHANNEL_NAME}.tx" ]] || log_error "channel tx not found"

log_info "All channel artifacts verified"

# ═══════════════════════════════════════════════════════════════════════════════
# COMPLETION
# ═══════════════════════════════════════════════════════════════════════════════
log_step "Initialization Complete"

echo ""
echo "Generated artifacts:"
du -sh "$ORGS_DIR" "$ARTIFACTS_DIR"
echo ""

log_info "Blockchain initialization artifacts ready for Docker deployment"
exit 0
