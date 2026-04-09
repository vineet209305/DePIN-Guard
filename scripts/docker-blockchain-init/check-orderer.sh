#!/bin/bash
# check-orderer.sh
# Health check for Orderer
# Used by docker-compose healthcheck

ORDERER_HOST="${ORDERER_HOST:-orderer.depin}"
ORDERER_PORT="${ORDERER_PORT:-7050}"

# Check if orderer port is listening
if nc -z "$ORDERER_HOST" "$ORDERER_PORT" 2>/dev/null; then
  exit 0
else
  exit 1
fi
