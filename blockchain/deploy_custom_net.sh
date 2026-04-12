#!/bin/bash
# blockchain/deploy_custom_net.sh
#
# Usage:
#   ./deploy_custom_net.sh          — start network (safe, skips if already running)
#   ./deploy_custom_net.sh --reset  — stop Fabric containers only, regenerate, restart
#   ./deploy_custom_net.sh --teardown — stop and remove Fabric containers and volumes only
#
# FIX: Added create_channel() function — channel creation + both peers joined
# FIX: Orderer FQDN consistently uses orderer.orderer.depin throughout

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BLOCKCHAIN_DIR="$SCRIPT_DIR"
COMPOSE_FILE="$BLOCKCHAIN_DIR/../docker/docker-compose-custom.yaml"
CONFIG_DIR="$BLOCKCHAIN_DIR/config"
ARTIFACTS_DIR="$BLOCKCHAIN_DIR/channel-artifacts"
ORGS_DIR="$BLOCKCHAIN_DIR/organizations"
CHANNEL_NAME="mychannel"
FABRIC_PROJECT_NAME="depin-fabric"

export PATH=$PATH:$BLOCKCHAIN_DIR/fabric-samples/bin
export FABRIC_CFG_PATH="$BLOCKCHAIN_DIR/fabric-samples/config"

wait_for_port() {
  local port="$1"
  local label="$2"
  local timeout_seconds="${3:-60}"
  local elapsed=0

  while ! (exec 3<>"/dev/tcp/localhost/$port") 2>/dev/null; do
    if [[ $elapsed -ge $timeout_seconds ]]; then
      echo "[ERROR] $label on port $port not responding after ${timeout_seconds}s"
      exit 1
    fi
    sleep 2
    elapsed=$((elapsed + 2))
  done
}

MODE="${1:-start}"

case "$MODE" in
  --teardown)
    echo "[TEARDOWN] Stopping and removing DePIN Fabric containers only..."
    docker compose -p "$FABRIC_PROJECT_NAME" -f "$COMPOSE_FILE" down --volumes --remove-orphans 2>/dev/null || true
    echo "[TEARDOWN] Complete."
    exit 0
    ;;
  --reset)
    echo "[RESET] Stopping DePIN Fabric containers only..."
    docker compose -p "$FABRIC_PROJECT_NAME" -f "$COMPOSE_FILE" down --volumes --remove-orphans 2>/dev/null || true
    rm -rf "$ORGS_DIR" "$ARTIFACTS_DIR"
    echo "[RESET] Cleaned. Proceeding to regenerate and restart..."
    ;;
  start)
    echo "[START] Starting DePIN Fabric network..."
    ;;
  *)
    echo "Unknown mode: $MODE"
    echo "Usage: $0 [--reset | --teardown]"
    exit 1
    ;;
esac

# ─── Prerequisite Checks ──────────────────────────────────────────────────────

check_prereqs() {
  echo "[CHECK] Verifying prerequisites..."
  local missing=0
  for tool in cryptogen configtxgen docker peer; do
    if ! command -v "$tool" &>/dev/null; then
      echo "[ERROR] Required tool not found: $tool"
      missing=1
    fi
  done
  if [[ ! -f "$CONFIG_DIR/crypto-config.yaml" ]]; then
    echo "[ERROR] crypto-config.yaml not found at $CONFIG_DIR"
    missing=1
  fi
  if [[ ! -f "$BLOCKCHAIN_DIR/configtx.yaml" ]]; then
    echo "[ERROR] configtx.yaml not found at $BLOCKCHAIN_DIR"
    missing=1
  fi
  if [[ $missing -eq 1 ]]; then
    echo "[ABORT] Prerequisites not met."
    exit 1
  fi
  echo "[CHECK] All prerequisites satisfied."
}

# ─── Artifact Generation ──────────────────────────────────────────────────────

generate_crypto() {
  echo "[CRYPTO] Generating cryptographic material..."
  if [[ -d "$ORGS_DIR" && "$MODE" == "start" ]]; then
    echo "[CRYPTO] organizations/ already exists — skipping (use --reset to regenerate)"
    return 0
  fi
  rm -rf "$ORGS_DIR"
  cryptogen generate \
    --config="$CONFIG_DIR/crypto-config.yaml" \
    --output="$ORGS_DIR"
  echo "[CRYPTO] Done — $ORGS_DIR"
}

generate_artifacts() {
  echo "[ARTIFACTS] Generating genesis block and channel tx..."
  mkdir -p "$ARTIFACTS_DIR"
  if [[ -f "$ARTIFACTS_DIR/genesis.block" && "$MODE" == "start" ]]; then
    echo "[ARTIFACTS] Artifacts already exist — skipping (use --reset to regenerate)"
    return 0
  fi

  # FIX: FABRIC_CFG_PATH must point to where configtx.yaml lives for configtxgen
  FABRIC_CFG_PATH="$BLOCKCHAIN_DIR" configtxgen \
    -profile ManufacturerMaintenanceOrdererGenesis \
    -channelID system-channel \
    -outputBlock "$ARTIFACTS_DIR/genesis.block"

  FABRIC_CFG_PATH="$BLOCKCHAIN_DIR" configtxgen \
    -profile ManufacturerMaintenanceChannel \
    -outputCreateChannelTx "$ARTIFACTS_DIR/${CHANNEL_NAME}.tx" \
    -channelID "$CHANNEL_NAME"

  echo "[ARTIFACTS] Genesis block and channel tx written to $ARTIFACTS_DIR"
}

# ─── Network Startup ──────────────────────────────────────────────────────────

start_containers() {
  echo "[DOCKER] Starting Fabric containers..."
  docker compose \
    -p "$FABRIC_PROJECT_NAME" \
    -f "$COMPOSE_FILE" \
    up -d --remove-orphans

  echo "[DOCKER] Waiting for peers and orderer to initialise..."
  wait_for_port 7050 "orderer" 90
  wait_for_port 7051 "manufacturer peer" 90
  wait_for_port 9051 "maintenance peer" 90
  echo "[DOCKER] Waiting briefly for orderer Raft initialization..."
  sleep 5

  local expected_containers=("peer0.manufacturer" "peer0.maintenance" "orderer")
  for container in "${expected_containers[@]}"; do
    if ! docker ps --format '{{.Names}}' | grep -q "$container"; then
      echo "[ERROR] Container $container did not start."
      echo "[ERROR] Run: docker compose -p $FABRIC_PROJECT_NAME -f $COMPOSE_FILE logs"
      exit 1
    fi
  done
  echo "[DOCKER] All Fabric containers are running."
}

# ─── Channel Creation & Peer Join ─────────────────────────────────────────────
# FIX: This entire function was missing — channel never existed before chaincode deploy

create_channel() {
  echo "[CHANNEL] Setting up ${CHANNEL_NAME}..."

  if [[ -f "$ARTIFACTS_DIR/${CHANNEL_NAME}.block" && "$MODE" == "start" ]]; then
    echo "[CHANNEL] Channel block already exists — skipping creation (use --reset to redo)"
    return 0
  fi

  local ORDERER_CA="$ORGS_DIR/ordererOrganizations/orderer.depin/orderers/orderer.orderer.depin/msp/tlscacerts/tlsca.orderer.depin-cert.pem"

  # --- Switch to Manufacturer identity ---
  export CORE_PEER_TLS_ENABLED=true
  export CORE_PEER_LOCALMSPID="ManufacturerMSP"
  export CORE_PEER_TLS_ROOTCERT_FILE="$ORGS_DIR/peerOrganizations/manufacturer.depin/peers/peer0.manufacturer.depin/tls/ca.crt"
  export CORE_PEER_MSPCONFIGPATH="$ORGS_DIR/peerOrganizations/manufacturer.depin/users/Admin@manufacturer.depin/msp"
  export CORE_PEER_ADDRESS="localhost:7051"

  echo "[CHANNEL] Creating channel $CHANNEL_NAME..."
  peer channel create \
    -o localhost:7050 \
    --ordererTLSHostnameOverride orderer.orderer.depin \
    -c "$CHANNEL_NAME" \
    -f "$ARTIFACTS_DIR/${CHANNEL_NAME}.tx" \
    --tls --cafile "$ORDERER_CA" \
    --outputBlock "$ARTIFACTS_DIR/${CHANNEL_NAME}.block"

  echo "[CHANNEL] Joining Manufacturer peer (localhost:7051)..."
  peer channel join -b "$ARTIFACTS_DIR/${CHANNEL_NAME}.block"

  # --- Switch to Maintenance identity ---
  export CORE_PEER_LOCALMSPID="MaintenanceProviderMSP"
  export CORE_PEER_TLS_ROOTCERT_FILE="$ORGS_DIR/peerOrganizations/maintenance.depin/peers/peer0.maintenance.depin/tls/ca.crt"
  export CORE_PEER_MSPCONFIGPATH="$ORGS_DIR/peerOrganizations/maintenance.depin/users/Admin@maintenance.depin/msp"
  export CORE_PEER_ADDRESS="localhost:9051"

  echo "[CHANNEL] Joining Maintenance peer (localhost:9051)..."
  peer channel join -b "$ARTIFACTS_DIR/${CHANNEL_NAME}.block"

  echo "[CHANNEL] Both peers joined $CHANNEL_NAME successfully."

  # --- Update anchor peers ---
  echo "[CHANNEL] Updating anchor peers..."
  export CORE_PEER_LOCALMSPID="ManufacturerMSP"
  export CORE_PEER_TLS_ROOTCERT_FILE="$ORGS_DIR/peerOrganizations/manufacturer.depin/peers/peer0.manufacturer.depin/tls/ca.crt"
  export CORE_PEER_MSPCONFIGPATH="$ORGS_DIR/peerOrganizations/manufacturer.depin/users/Admin@manufacturer.depin/msp"
  export CORE_PEER_ADDRESS="localhost:7051"

  FABRIC_CFG_PATH="$BLOCKCHAIN_DIR" configtxgen \
    -profile ManufacturerMaintenanceChannel \
    -outputAnchorPeersUpdate "$ARTIFACTS_DIR/ManufacturerMSPanchors.tx" \
    -channelID "$CHANNEL_NAME" \
    -asOrg ManufacturerMSP 2>/dev/null || true

  if [[ -f "$ARTIFACTS_DIR/ManufacturerMSPanchors.tx" ]]; then
    peer channel update \
      -o localhost:7050 \
      --ordererTLSHostnameOverride orderer.orderer.depin \
      -c "$CHANNEL_NAME" \
      -f "$ARTIFACTS_DIR/ManufacturerMSPanchors.tx" \
      --tls --cafile "$ORDERER_CA"
    echo "[CHANNEL] Manufacturer anchor peer updated."
  fi
}

# ─── Main ─────────────────────────────────────────────────────────────────────

main() {
  check_prereqs
  generate_crypto
  generate_artifacts
  start_containers
  create_channel   # FIX: was missing — added here

  echo ""
  echo "══════════════════════════════════════════════"
  echo " DePIN-Guard Fabric Network is RUNNING"
  echo ""
  echo " Channel  : $CHANNEL_NAME"
  echo " Artifacts: $ARTIFACTS_DIR"
  echo " Orgs     : $ORGS_DIR"
  echo ""
  echo " Next step: cd blockchain && ./deploy_chaincode.sh"
  echo ""
  echo " To reset    : $0 --reset"
  echo " To teardown : $0 --teardown"
  echo "══════════════════════════════════════════════"
}

main
