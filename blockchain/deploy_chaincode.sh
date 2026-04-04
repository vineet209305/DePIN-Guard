#!/bin/bash
# blockchain/deploy_chaincode.sh
# FIX: MaintenanceMSP -> MaintenanceProviderMSP (both install and approve steps)
# FIX: ordererTLSHostnameOverride uses orderer.orderer.example.com consistently

set -euo pipefail

CHANNEL_NAME="mychannel"
CC_NAME="depin_cc"
CC_VERSION="1.0"
CC_SEQUENCE=1

CC_SRC_PATH="./chaincode-go/"
CC_LANG="golang"

export FABRIC_CFG_PATH=${PWD}/fabric-samples/config

ORDERER_CA=${PWD}/organizations/ordererOrganizations/orderer.example.com/orderers/orderer.orderer.example.com/msp/tlscacerts/tlsca.orderer.example.com-cert.pem

MFR_TLS=${PWD}/organizations/peerOrganizations/manufacturer.example.com/peers/peer0.manufacturer.example.com/tls/ca.crt
MFR_MSP=${PWD}/organizations/peerOrganizations/manufacturer.example.com/users/Admin@manufacturer.example.com/msp

MNT_TLS=${PWD}/organizations/peerOrganizations/maintenance.example.com/peers/peer0.maintenance.example.com/tls/ca.crt
MNT_MSP=${PWD}/organizations/peerOrganizations/maintenance.example.com/users/Admin@maintenance.example.com/msp

export CORE_PEER_TLS_ENABLED=true

echo ""
echo "=========================================="
echo " DePIN-Guard Chaincode Deployment"
echo "=========================================="

echo ""
echo "📦 Step 1: Packaging chaincode..."
./fabric-samples/bin/peer lifecycle chaincode package ${CC_NAME}.tar.gz \
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
./fabric-samples/bin/peer lifecycle chaincode install ${CC_NAME}.tar.gz

echo ""
echo "⚙️  Step 3: Installing on Maintenance peer (localhost:9051)..."
# FIX: was MaintenanceMSP — must match configtx.yaml ID field = MaintenanceProviderMSP
export CORE_PEER_LOCALMSPID="MaintenanceProviderMSP"
export CORE_PEER_TLS_ROOTCERT_FILE=$MNT_TLS
export CORE_PEER_MSPCONFIGPATH=$MNT_MSP
export CORE_PEER_ADDRESS=localhost:9051
./fabric-samples/bin/peer lifecycle chaincode install ${CC_NAME}.tar.gz

echo ""
echo "🔍 Step 4: Getting Package ID from Manufacturer peer..."
export CORE_PEER_LOCALMSPID="ManufacturerMSP"
export CORE_PEER_TLS_ROOTCERT_FILE=$MFR_TLS
export CORE_PEER_MSPCONFIGPATH=$MFR_MSP
export CORE_PEER_ADDRESS=localhost:7051
./fabric-samples/bin/peer lifecycle chaincode queryinstalled > log.txt 2>&1
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
./fabric-samples/bin/peer lifecycle chaincode approveformyorg \
  -o localhost:7050 \
  --ordererTLSHostnameOverride orderer.orderer.example.com \
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
./fabric-samples/bin/peer lifecycle chaincode approveformyorg \
  -o localhost:7050 \
  --ordererTLSHostnameOverride orderer.orderer.example.com \
  --channelID $CHANNEL_NAME \
  --name $CC_NAME \
  --version $CC_VERSION \
  --package-id $PACKAGE_ID \
  --sequence $CC_SEQUENCE \
  --tls --cafile $ORDERER_CA

echo ""
echo "🔍 Step 7: Checking commit readiness (both orgs must show true)..."
export CORE_PEER_LOCALMSPID="ManufacturerMSP"
export CORE_PEER_TLS_ROOTCERT_FILE=$MFR_TLS
export CORE_PEER_MSPCONFIGPATH=$MFR_MSP
export CORE_PEER_ADDRESS=localhost:7051
./fabric-samples/bin/peer lifecycle chaincode checkcommitreadiness \
  --channelID $CHANNEL_NAME \
  --name $CC_NAME \
  --version $CC_VERSION \
  --sequence $CC_SEQUENCE \
  --tls --cafile $ORDERER_CA \
  --output json

echo ""
echo "🚀 Step 8: Committing chaincode to channel..."
./fabric-samples/bin/peer lifecycle chaincode commit \
  -o localhost:7050 \
  --ordererTLSHostnameOverride orderer.orderer.example.com \
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
./fabric-samples/bin/peer lifecycle chaincode querycommitted \
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