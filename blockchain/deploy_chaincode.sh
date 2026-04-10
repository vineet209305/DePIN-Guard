#!/bin/bash
# blockchain/deploy_chaincode.sh
# FIX: MaintenanceMSP -> MaintenanceProviderMSP (both install and approve steps)
# FIX: ordererTLSHostnameOverride uses orderer.orderer.example.com consistently

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BLOCKCHAIN_DIR="$SCRIPT_DIR"
CHANNEL_NAME="mychannel"
CC_NAME="depin_cc"
CC_VERSION="1.0"
CC_SEQUENCE=1

CC_SRC_PATH="$BLOCKCHAIN_DIR/chaincode-go/"
CC_LANG="golang"

export PATH="$PATH:$BLOCKCHAIN_DIR/fabric-samples/bin"
export FABRIC_CFG_PATH="$BLOCKCHAIN_DIR/fabric-samples/config"

ORDERER_CA="$BLOCKCHAIN_DIR/organizations/ordererOrganizations/orderer.depin/orderers/orderer.orderer.depin/msp/tlscacerts/tlsca.orderer.depin-cert.pem"

MFR_TLS="$BLOCKCHAIN_DIR/organizations/peerOrganizations/manufacturer.depin/peers/peer0.manufacturer.depin/tls/ca.crt"
MFR_MSP="$BLOCKCHAIN_DIR/organizations/peerOrganizations/manufacturer.depin/users/Admin@manufacturer.depin/msp"

MNT_TLS="$BLOCKCHAIN_DIR/organizations/peerOrganizations/maintenance.depin/peers/peer0.maintenance.depin/tls/ca.crt"
MNT_MSP="$BLOCKCHAIN_DIR/organizations/peerOrganizations/maintenance.depin/users/Admin@maintenance.depin/msp"

for required_path in "$CC_SRC_PATH" "$ORDERER_CA" "$MFR_TLS" "$MFR_MSP" "$MNT_TLS" "$MNT_MSP"; do
  if [[ ! -e "$required_path" ]]; then
    echo "ERROR: Missing required path: $required_path"
    exit 1
  fi
done

ensure_fabric_image() {
  local image_name="$1"
  if ! docker image inspect "$image_name" >/dev/null 2>&1; then
    echo "INFO: Pulling missing Fabric image: $image_name"
    docker pull "$image_name" || { echo "ERROR: Failed to pull $image_name"; exit 1; }
  fi
}

ensure_fabric_image "hyperledger/fabric-ccenv:2.5"
ensure_fabric_image "hyperledger/fabric-baseos:2.5"

export CORE_PEER_TLS_ENABLED=true

echo ""
echo "=========================================="
echo " DePIN-Guard Chaincode Deployment"
echo "=========================================="

echo ""
echo "📦 Step 1: Packaging chaincode..."
peer lifecycle chaincode package ${CC_NAME}.tar.gz \
  --path ${CC_SRC_PATH} \
  --lang ${CC_LANG} \
  --label ${CC_NAME}_${CC_VERSION}
echo "   Package created: ${CC_NAME}.tar.gz"

echo ""
echo "⚙️  Step 2: Installing on Manufacturer peer (localhost:7051)..."
export CORE_PEER_LOCALMSPID="ManufacturerMSP"
export CORE_PEER_TLS_ROOTCERT_FILE=$MFR_TLS
export CORE_PEER_MSPCONFIGPATH=$MFR_MSP
export CORE_PEER_ADDRESS=localhost:7051
peer lifecycle chaincode install ${CC_NAME}.tar.gz

echo ""
echo "⚙️  Step 3: Installing on Maintenance peer (localhost:9051)..."
# FIX: was MaintenanceMSP — must match configtx.yaml ID field = MaintenanceProviderMSP
export CORE_PEER_LOCALMSPID="MaintenanceProviderMSP"
export CORE_PEER_TLS_ROOTCERT_FILE=$MNT_TLS
export CORE_PEER_MSPCONFIGPATH=$MNT_MSP
export CORE_PEER_ADDRESS=localhost:9051
peer lifecycle chaincode install ${CC_NAME}.tar.gz

echo ""
echo "🔍 Step 4: Getting Package ID from Manufacturer peer..."
export CORE_PEER_LOCALMSPID="ManufacturerMSP"
export CORE_PEER_TLS_ROOTCERT_FILE=$MFR_TLS
export CORE_PEER_MSPCONFIGPATH=$MFR_MSP
export CORE_PEER_ADDRESS=localhost:7051
peer lifecycle chaincode queryinstalled > log.txt 2>&1
cat log.txt
PACKAGE_ID=$(sed -n "/${CC_NAME}_${CC_VERSION}/{s/^Package ID: //; s/, Label:.*$//; p;}" log.txt)
if [ -z "$PACKAGE_ID" ]; then
  echo "ERROR: Could not extract Package ID. Check log.txt for details."
  exit 1
fi
echo "   Package ID: ${PACKAGE_ID}"

echo ""
echo "✅ Step 5: Approving for Manufacturer org..."
export CORE_PEER_LOCALMSPID="ManufacturerMSP"
export CORE_PEER_TLS_ROOTCERT_FILE=$MFR_TLS
export CORE_PEER_MSPCONFIGPATH=$MFR_MSP
export CORE_PEER_ADDRESS=localhost:7051
peer lifecycle chaincode approveformyorg \
  -o localhost:7050 \
  --ordererTLSHostnameOverride orderer.orderer.depin \
  --channelID $CHANNEL_NAME \
  --name $CC_NAME \
  --version $CC_VERSION \
  --package-id $PACKAGE_ID \
  --sequence $CC_SEQUENCE \
  --tls --cafile $ORDERER_CA

echo ""
echo "✅ Step 6: Approving for Maintenance org..."
# FIX: was MaintenanceMSP — must be MaintenanceProviderMSP
export CORE_PEER_LOCALMSPID="MaintenanceProviderMSP"
export CORE_PEER_TLS_ROOTCERT_FILE=$MNT_TLS
export CORE_PEER_MSPCONFIGPATH=$MNT_MSP
export CORE_PEER_ADDRESS=localhost:9051
peer lifecycle chaincode approveformyorg \
  -o localhost:7050 \
  --ordererTLSHostnameOverride orderer.orderer.depin \ Checking commit readiness (both orgs must show true)..."
export CORE_PEER_LOCALMSPID="ManufacturerMSP"
export CORE_PEER_TLS_ROOTCERT_FILE=$MFR_TLS
export CORE_PEER_MSPCONFIGPATH=$MFR_MSP
export CORE_PEER_ADDRESS=localhost:7051
peer lifecycle chaincode checkcommitreadiness \
  --channelID $CHANNEL_NAME \
  --name $CC_NAME \
  --version $CC_VERSION \
  --sequence $CC_SEQUENCE \
  --tls --cafile $ORDERER_CA \
  --output json

echo ""
echo "🚀 Step 8: Committing chaincode to channel..."
peer lifecycle chaincode commit \
  -o localhost:7050 \
  --ordererTLSHostnameOverride orderer.orderer.depin \
  --channelID $CHANNEL_NAME \
  --name $CC_NAME \
  --version $CC_VERSION \
  --sequence $CC_SEQUENCE \
  --tls --cafile $ORDERER_CA \
  --peerAddresses localhost:7051 \
  --tlsRootCertFiles $MFR_TLS \
  --peerAddresses localhost:9051 \
  --tlsRootCertFiles $MNT_TLS

echo ""
echo "🔍 Step 9: Verifying committed chaincode..."
peer lifecycle chaincode querycommitted \
  --channelID $CHANNEL_NAME \
  --name $CC_NAME \
  --tls --cafile $ORDERER_CA

echo ""
echo "=========================================="
echo " Chaincode deployed successfully!"
echo " Channel : $CHANNEL_NAME"
echo " Name    : $CC_NAME"
echo " Version : $CC_VERSION"
echo "=========================================="