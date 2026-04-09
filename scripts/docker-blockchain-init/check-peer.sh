#!/bin/bash
# check-peer.sh
# Health check for Peers
# Used by docker-compose healthcheck

PEER_HOST="${PEER_HOST:-peer0.manufacturer.depin}"
PEER_PORT="${PEER_PORT:-7051}"

# Check if peer port is listening
if nc -z "$PEER_HOST" "$PEER_PORT" 2>/dev/null; then
  exit 0
else
  exit 1
fi
