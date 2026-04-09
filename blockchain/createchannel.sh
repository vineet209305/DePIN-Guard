#!/bin/bash
# blockchain/create_channel.sh
# Run this ONCE after deploy_custom_net.sh starts the containers.
# If channel already exists the join command will say "already joined" — that is safe.
#
# Usage (run from inside the blockchain/ folder):
#   cd blockchain
#   ./create_channel.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BLOCKCHAIN_DIR="$SCRIPT_DIR"
ARTIFACTS_DIR="$BLOCKCHAIN_DIR/channel-artifacts"
ORGS_DIR="$BLOCKCHAIN_DIR/organizations"
CHANNEL_NAME="mychannel"

export PATH="$PATH:$BLOCKCHAIN_DIR/fabric-samples/bin"
# FABRIC_CFG_PATH must point to where core.yaml lives (needed by peer commands)
export FABRIC_CFG_PATH="$BLOCKCHAIN_DIR/fabric-samples/config"
export CORE_PEER_TLS_ENABLED=true

ORDERER_CA="$ORGS_DIR/ordererOrganizations/orderer.example.com/orderers/orderer.orderer.example.com/msp/tlscacerts/tlsca.orderer.example.com-cert.pem"
MFR_TLS="$ORGS_DIR/peerOrganizations/manufacturer.example.com/peers/peer0.manufacturer.example.com/tls/ca.crt"
MFR_MSP="$ORGS_DIR/peerOrganizations/manufacturer.example.com/users/Admin@manufacturer.example.com/msp"
MNT_TLS="$ORGS_DIR/peerOrganizations/maintenance.example.com/peers/peer0.maintenance.example.com/tls/ca.crt"
MNT_MSP="$ORGS_DIR/peerOrganizations/maintenance.example.com/users/Admin@maintenance.example.com/msp"

# ─── Verify required files exist ─────────────────────────────────────────────
echo "[CHECK] Verifying artifacts and certificates..."

for f in "$ORDERER_CA" "$MFR_TLS" "$MFR_MSP" "$MNT_TLS" "$MNT_MSP"; do
  if [[ ! -e "$f" ]]; then
    echo "[ERROR] Missing: $f"
    echo "        Run ./deploy_custom_net.sh first to generate crypto material."
    exit 1
  fi
done

if [[ ! -f "$ARTIFACTS_DIR/${CHANNEL_NAME}.tx" ]]; then
  echo "[ERROR] Missing channel tx: $ARTIFACTS_DIR/${CHANNEL_NAME}.tx"
  echo "        Run ./deploy_custom_net.sh first to generate artifacts."
  exit 1
fi

# ─── Verify containers are reachable ─────────────────────────────────────────
echo "[CHECK] Checking peer and orderer connectivity..."
for addr in "localhost:7050" "localhost:7051" "localhost:9051"; do
  host="${addr%%:*}"
  port="${addr##*:}"
  if ! (exec 3<>"/dev/tcp/$host/$port") 2>/dev/null; then
    echo "[ERROR] Cannot reach $addr — ensure Docker containers are running."
    echo "        Run: docker ps | grep -E 'orderer|peer'"
    exit 1
  fi
done
echo "[CHECK] All containers reachable."

# ─── Set Manufacturer identity ────────────────────────────────────────────────
use_manufacturer() {
  export CORE_PEER_LOCALMSPID="ManufacturerMSP"
  export CORE_PEER_TLS_ROOTCERT_FILE="$MFR_TLS"
  export CORE_PEER_MSPCONFIGPATH="$MFR_MSP"
  export CORE_PEER_ADDRESS="localhost:7051"
}

# ─── Set Maintenance identity ─────────────────────────────────────────────────
use_maintenance() {
  export CORE_PEER_LOCALMSPID="MaintenanceProviderMSP"
  export CORE_PEER_TLS_ROOTCERT_FILE="$MNT_TLS"
  export CORE_PEER_MSPCONFIGPATH="$MNT_MSP"
  export CORE_PEER_ADDRESS="localhost:9051"
}

# ─── Step 1: Create the channel ───────────────────────────────────────────────
echo ""
echo "Step 1: Creating channel '$CHANNEL_NAME'..."
use_manufacturer

# Remove stale block file so peer channel create writes a fresh one
rm -f "$ARTIFACTS_DIR/${CHANNEL_NAME}.block"

peer channel create \
  -o localhost:7050 \
  --ordererTLSHostnameOverride orderer.orderer.example.com \
  -c "$CHANNEL_NAME" \
  -f "$ARTIFACTS_DIR/${CHANNEL_NAME}.tx" \
  --tls --cafile "$ORDERER_CA" \
  --outputBlock "$ARTIFACTS_DIR/${CHANNEL_NAME}.block" \
  --timeout 30s

echo "   Channel created. Block saved to $ARTIFACTS_DIR/${CHANNEL_NAME}.block"

# ─── Step 2: Join Manufacturer peer ──────────────────────────────────────────
echo ""
echo "Step 2: Joining Manufacturer peer (localhost:7051)..."
use_manufacturer
peer channel join -b "$ARTIFACTS_DIR/${CHANNEL_NAME}.block"
echo "   Manufacturer peer joined."

# ─── Step 3: Join Maintenance peer ───────────────────────────────────────────
echo ""
echo "Step 3: Joining Maintenance peer (localhost:9051)..."
use_maintenance
peer channel join -b "$ARTIFACTS_DIR/${CHANNEL_NAME}.block"
echo "   Maintenance peer joined."

# ─── Step 4: Update anchor peers (best effort) ────────────────────────────────
echo ""
echo "Step 4: Updating anchor peers (best effort)..."

use_manufacturer

ANCHOR_TX_MFR="$ARTIFACTS_DIR/ManufacturerMSPanchors.tx"

# Generate anchor peer update tx inline using configtxgen
FABRIC_CFG_PATH="$BLOCKCHAIN_DIR" configtxgen \
  -profile ManufacturerMaintenanceChannel \
  -outputAnchorPeersUpdate "$ANCHOR_TX_MFR" \
  -channelID "$CHANNEL_NAME" \
  -asOrg ManufacturerMSP 2>/dev/null || true

if [[ -f "$ANCHOR_TX_MFR" ]]; then
  peer channel update \
    -o localhost:7050 \
    --ordererTLSHostnameOverride orderer.orderer.example.com \
    -c "$CHANNEL_NAME" \
    -f "$ANCHOR_TX_MFR" \
    --tls --cafile "$ORDERER_CA" && echo "   Manufacturer anchor peer updated." \
    || echo "   Anchor peer update skipped (non-critical for demo)."
else
  echo "   Anchor peer tx not generated — skipping (non-critical)."
fi

# ─── Step 5: Verify both peers are on the channel ────────────────────────────
echo ""
echo "Step 5: Verifying channel membership..."

use_manufacturer
echo -n "   Manufacturer peer — "
peer channel list 2>/dev/null | grep -q "$CHANNEL_NAME" \
  && echo "JOINED $CHANNEL_NAME ✅" \
  || echo "NOT on channel ❌"

use_maintenance
echo -n "   Maintenance peer  — "
peer channel list 2>/dev/null | grep -q "$CHANNEL_NAME" \
  && echo "JOINED $CHANNEL_NAME ✅" \
  || echo "NOT on channel ❌"

echo ""
echo "══════════════════════════════════════════════"
echo " Channel setup complete."
echo " Next: cd blockchain && ./deploy_chaincode.sh"
echo "══════════════════════════════════════════════"