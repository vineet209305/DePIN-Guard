#!/bin/bash

echo "🧹 Cleaning up old containers..."
docker rm -f $(docker ps -aq) 2>/dev/null || true

echo "🔑 Generating crypto material..."
cryptogen generate --config=./config/crypto-config.yaml --output="organizations"

echo "📦 Generating genesis block..."
configtxgen -profile TwoOrgsOrdererGenesis -channelID system-channel -outputBlock ./channel-artifacts/genesis.block

echo "📄 Generating channel transaction..."
configtxgen -profile TwoOrgsChannel -outputCreateChannelTx ./channel-artifacts/channel.tx -channelID mychannel

echo "🚀 Starting network..."
docker-compose -f ../docker/docker-compose-custom.yaml up -d

echo "✅ Network is up!"
