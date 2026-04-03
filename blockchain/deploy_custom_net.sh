#!/bin/bash
#
# blockchain/deploy_custom_net.sh
#
# Usage:
#   ./deploy_custom_net.sh          — start network (safe, skips if already running)
#   ./deploy_custom_net.sh --reset  — stop Fabric containers only, regenerate, restart
#   ./deploy_custom_net.sh --teardown — stop and remove Fabric containers and volumes only
#
# NEVER touches containers outside the depin-fabric Docker network.

set -euo pipefail

# ─── Configuration ────────────────────────────────────────────────────────────

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BLOCKCHAIN_DIR="$SCRIPT_DIR"
COMPOSE_FILE="$BLOCKCHAIN_DIR/../docker/docker-compose-custom.yaml"
CONFIG_DIR="$BLOCKCHAIN_DIR/config"
ARTIFACTS_DIR="$BLOCKCHAIN_DIR/channel-artifacts"
ORGS_DIR="$BLOCKCHAIN_DIR/organizations"
CHANNEL_NAME="mychannel"
CHAINCODE_NAME="depin-guard"
FABRIC_PROJECT_NAME="depin-fabric"

export PATH=$PATH:$BLOCKCHAIN_DIR/fabric-samples/bin

# ─── Mode Parsing ─────────────────────────────────────────────────────────────

MODE="${1:-start}"

case "$MODE" in
  --teardown)
    echo "[TEARDOWN] Stopping and removing DePIN Fabric containers only..."
    docker compose -p "$FABRIC_PROJECT_NAME" -f "$COMPOSE_FILE" down --volumes --remove-orphans 2>/dev/null || true
    echo "[TEARDOWN] Complete. Non-Fabric containers untouched."
    exit 0
    ;;
  --reset)
    echo "[RESET] Stopping DePIN Fabric containers only..."
    docker compose -p "$FABRIC_PROJECT_NAME" -f "$COMPOSE_FILE" down --volumes --remove-orphans 2>/dev/null || true
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
  for tool in cryptogen configtxgen docker; do
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
    echo "[ABORT] Prerequisites not met. Fix errors above before retrying."
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

  echo "[CRYPTO] Cryptographic material generated at $ORGS_DIR"
}

generate_artifacts() {
  echo "[ARTIFACTS] Generating genesis block and channel tx..."

  mkdir -p "$ARTIFACTS_DIR"

  if [[ -f "$ARTIFACTS_DIR/genesis.block" && "$MODE" == "start" ]]; then
    echo "[ARTIFACTS] Artifacts already exist — skipping (use --reset to regenerate)"
    return 0
  fi

  FABRIC_CFG_PATH="$BLOCKCHAIN_DIR" configtxgen \
    -profile ManufacturerMaintenanceOrdererGenesis \
    -channelID system-channel \
    -outputBlock "$ARTIFACTS_DIR/genesis.block"

  FABRIC_CFG_PATH="$BLOCKCHAIN_DIR" configtxgen \
    -profile ManufacturerMaintenanceChannel \
    -outputCreateChannelTx "$ARTIFACTS_DIR/${CHANNEL_NAME}.tx" \
    -channelID "$CHANNEL_NAME"

  echo "[ARTIFACTS] Genesis block and channel tx written."
}

# ─── Network Startup ──────────────────────────────────────────────────────────

start_containers() {
  echo "[DOCKER] Starting Fabric containers..."

  docker compose \
    -p "$FABRIC_PROJECT_NAME" \
    -f "$COMPOSE_FILE" \
    up -d --remove-orphans

  echo "[DOCKER] Waiting for peers and orderer to become ready..."
  sleep 8

  # Verify containers actually started
  local expected_containers=("peer0.manufacturer" "peer0.maintenance" "orderer")
  for container in "${expected_containers[@]}"; do
    if ! docker ps --format '{{.Names}}' | grep -q "$container"; then
      echo "[ERROR] Container $container did not start."
      echo "[ERROR] Check logs: docker compose -p $FABRIC_PROJECT_NAME logs"
      exit 1
    fi
  done

  echo "[DOCKER] All Fabric containers running."
}

# ─── Main Execution ───────────────────────────────────────────────────────────

main() {
  check_prereqs
  generate_crypto
  generate_artifacts
  start_containers

  echo ""
  echo "══════════════════════════════════════════════"
  echo " DePIN-Guard Fabric Network is RUNNING"
  echo " Channel artifacts: $ARTIFACTS_DIR"
  echo " Organizations:     $ORGS_DIR"
  echo " To reset:    $0 --reset"
  echo " To teardown: $0 --teardown"
  echo "══════════════════════════════════════════════"
}

main
