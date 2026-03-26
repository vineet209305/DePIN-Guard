#!/bin/bash

# ====================================================================
# DePIN-Guard: Exact Fix for Chaincode Deployment
# ====================================================================

CHANNEL_NAME="mychannel"
CC_NAME="depin_cc"
CC_VERSION="1.0"
CC_SEQUENCE=1

# 1. FIXED: Correct Chaincode Folder Path
CC_SRC_PATH="./chaincode-go/"
CC_LANG="golang" 

export FABRIC_CFG_PATH=${PWD}/fabric-samples/config

# 2. FIXED: Correct Orderer Custom Path
ORDERER_CA=${PWD}/organizations/ordererOrganizations/orderer.example.com/orderers/orderer.orderer.example.com/msp/tlscacerts/tlsca.orderer.example.com-cert.pem

MFR_TLS=${PWD}/organizations/peerOrganizations/manufacturer.example.com/peers/peer0.manufacturer.example.com/tls/ca.crt
MFR_MSP=${PWD}/organizations/peerOrganizations/manufacturer.example.com/users/Admin@manufacturer.example.com/msp

MNT_TLS=${PWD}/organizations/peerOrganizations/maintenance.example.com/peers/peer0.maintenance.example.com/tls/ca.crt
MNT_MSP=${PWD}/organizations/peerOrganizations/maintenance.example.com/users/Admin@maintenance.example.com/msp

# 3. FIXED: Enable TLS for all CLI commands!
export CORE_PEER_TLS_ENABLED=true

echo "📦 1. Packaging the Chaincode..."
./fabric-samples/bin/peer lifecycle chaincode package ${CC_NAME}.tar.gz --path ${CC_SRC_PATH} --lang ${CC_LANG} --label ${CC_NAME}_${CC_VERSION}

echo "⚙️ 2. Installing Chaincode on Manufacturer Peer..."
export CORE_PEER_LOCALMSPID="ManufacturerMSP"
export CORE_PEER_TLS_ROOTCERT_FILE=$MFR_TLS
export CORE_PEER_MSPCONFIGPATH=$MFR_MSP
export CORE_PEER_ADDRESS=localhost:7051
./fabric-samples/bin/peer lifecycle chaincode install ${CC_NAME}.tar.gz

echo "⚙️ 3. Installing Chaincode on Maintenance Peer..."
export CORE_PEER_LOCALMSPID="MaintenanceMSP"
export CORE_PEER_TLS_ROOTCERT_FILE=$MNT_TLS
export CORE_PEER_MSPCONFIGPATH=$MNT_MSP
export CORE_PEER_ADDRESS=localhost:9051
./fabric-samples/bin/peer lifecycle chaincode install ${CC_NAME}.tar.gz

echo "🔍 4. Getting Package ID..."
./fabric-samples/bin/peer lifecycle chaincode queryinstalled > log.txt
PACKAGE_ID=$(sed -n "/${CC_NAME}_${CC_VERSION}/{s/^Package ID: //; s/, Label:.*$//; p;}" log.txt)
echo "Package ID is: ${PACKAGE_ID}"

echo "✅ 5. Approving for Manufacturer..."
export CORE_PEER_LOCALMSPID="ManufacturerMSP"
export CORE_PEER_TLS_ROOTCERT_FILE=$MFR_TLS
export CORE_PEER_MSPCONFIGPATH=$MFR_MSP
export CORE_PEER_ADDRESS=localhost:7051
./fabric-samples/bin/peer lifecycle chaincode approveformyorg -o localhost:7050 --ordererTLSHostnameOverride orderer.orderer.example.com --channelID $CHANNEL_NAME --name $CC_NAME --version $CC_VERSION --package-id $PACKAGE_ID --sequence $CC_SEQUENCE --tls --cafile $ORDERER_CA

echo "✅ 6. Approving for Maintenance..."
export CORE_PEER_LOCALMSPID="MaintenanceMSP"
export CORE_PEER_TLS_ROOTCERT_FILE=$MNT_TLS
export CORE_PEER_MSPCONFIGPATH=$MNT_MSP
export CORE_PEER_ADDRESS=localhost:9051
./fabric-samples/bin/peer lifecycle chaincode approveformyorg -o localhost:7050 --ordererTLSHostnameOverride orderer.orderer.example.com --channelID $CHANNEL_NAME --name $CC_NAME --version $CC_VERSION --package-id $PACKAGE_ID --sequence $CC_SEQUENCE --tls --cafile $ORDERER_CA

echo "🚀 7. Committing the Chaincode to the Channel..."
./fabric-samples/bin/peer lifecycle chaincode commit -o localhost:7050 --ordererTLSHostnameOverride orderer.orderer.example.com --channelID $CHANNEL_NAME --name $CC_NAME --version $CC_VERSION --sequence $CC_SEQUENCE --tls --cafile $ORDERER_CA --peerAddresses localhost:7051 --tlsRootCertFiles $MFR_TLS --peerAddresses localhost:9051 --tlsRootCertFiles $MNT_TLS

echo "🎉 Chaincode successfully deployed and ready to accept transactions!"