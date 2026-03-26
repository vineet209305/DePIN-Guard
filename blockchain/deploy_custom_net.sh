#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "🧹 Cleaning up old containers and corrupted files..."
# Added sudo here to prevent Permission Denied errors
docker rm -f $(docker ps -aq) 2>/dev/null || true
sudo rm -rf organizations channel-artifacts
mkdir -p channel-artifacts

# ── Locate binaries ──────────────────────────────────────────
PEER_BIN=""
if   [ -f "${SCRIPT_DIR}/fabric-samples/bin/peer" ]; then
    PEER_BIN="${SCRIPT_DIR}/fabric-samples/bin/peer"
elif [ -f "${SCRIPT_DIR}/bin/peer" ]; then
    PEER_BIN="${SCRIPT_DIR}/bin/peer"
else
    PEER_BIN="peer"
fi
echo "✅ Using peer binary: $PEER_BIN"

# ── configtxgen needs FABRIC_CFG_PATH pointing to the blockchain dir ──
export FABRIC_CFG_PATH="${SCRIPT_DIR}"

echo "🔑 Generating fresh crypto material..."
cryptogen generate --config=./config/crypto-config.yaml --output="organizations"

echo "📦 Generating genesis block..."
configtxgen -profile TwoOrgsOrdererGenesis -channelID system-channel \
    -outputBlock ./channel-artifacts/genesis.block

echo "📄 Generating channel transaction..."
configtxgen -profile TwoOrgsChannel \
    -outputCreateChannelTx ./channel-artifacts/channel.tx \
    -channelID mychannel

echo "🚀 Starting network..."
docker-compose -f ../docker/docker-compose.yml up -d

echo "⏳ Waiting 10 seconds for peers to fully initialize..."
sleep 10

# ── Switch to fabric-samples/config for peer CLI commands ──
export FABRIC_CFG_PATH="${SCRIPT_DIR}/fabric-samples/config"

ORDERER_CA="${SCRIPT_DIR}/organizations/ordererOrganizations/orderer.example.com/orderers/orderer.orderer.example.com/msp/tlscacerts/tlsca.orderer.example.com-cert.pem"
MFR_TLS="${SCRIPT_DIR}/organizations/peerOrganizations/manufacturer.example.com/peers/peer0.manufacturer.example.com/tls/ca.crt"
MFR_MSP="${SCRIPT_DIR}/organizations/peerOrganizations/manufacturer.example.com/users/Admin@manufacturer.example.com/msp"
MNT_TLS="${SCRIPT_DIR}/organizations/peerOrganizations/maintenance.example.com/peers/peer0.maintenance.example.com/tls/ca.crt"
MNT_MSP="${SCRIPT_DIR}/organizations/peerOrganizations/maintenance.example.com/users/Admin@maintenance.example.com/msp"

echo "🌍 Creating channel 'mychannel' as Manufacturer Admin..."
export CORE_PEER_LOCALMSPID="ManufacturerMSP"
export CORE_PEER_TLS_ENABLED=true
export CORE_PEER_TLS_ROOTCERT_FILE="$MFR_TLS"
export CORE_PEER_MSPCONFIGPATH="$MFR_MSP"
export CORE_PEER_ADDRESS=localhost:7051

$PEER_BIN channel create \
    -o localhost:7050 \
    -c mychannel \
    -f ./channel-artifacts/channel.tx \
    --outputBlock ./channel-artifacts/mychannel.block \
    --tls --cafile "$ORDERER_CA" \
    || { echo "❌ Channel create failed"; exit 1; }

echo "🤝 Joining Manufacturer Peer..."
$PEER_BIN channel join -b ./channel-artifacts/mychannel.block \
    || echo "⚠️ Manufacturer join failed (may already be joined)"

echo "🤝 Joining Maintenance Peer..."
export CORE_PEER_LOCALMSPID="MaintenanceMSP"
export CORE_PEER_TLS_ROOTCERT_FILE="$MNT_TLS"
export CORE_PEER_MSPCONFIGPATH="$MNT_MSP"
export CORE_PEER_ADDRESS=localhost:9051

$PEER_BIN channel join -b ./channel-artifacts/mychannel.block \
    || echo "⚠️ Maintenance join failed (may already be joined)"

echo "✅ Channel created and peers joined!"
echo "🐳 Running containers:"
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"