#!/bin/bash
# blockchain-init.sh — DePIN-Guard Hyperledger Fabric Network Initializer
#
# Runs as an ephemeral init container ONLY.
# Generates crypto material and channel artifacts, then exits cleanly.
# Orderer and peer containers start AFTER this exits with code 0.
#
# Idempotent: safe to re-run on existing volumes.

set -euo pipefail

# ═══════════════════════════════════════════════════════════════════════════
# CONFIGURATION — override via docker-compose environment section
# ═══════════════════════════════════════════════════════════════════════════

CHANNEL_NAME="${CHANNEL_NAME:-mychannel}"
SYSTEM_CHANNEL="${SYSTEM_CHANNEL:-system-channel}"

ORGS_DIR="${ORGS_DIR:-/root/organizations}"
ARTIFACTS_DIR="${ARTIFACTS_DIR:-/root/channel-artifacts}"
CONFIG_DIR="${CONFIG_DIR:-/root/fabric-config}"

# Must match profile names in configtx.yaml EXACTLY
GENESIS_PROFILE="${GENESIS_PROFILE:-ManufacturerMaintenanceOrdererGenesis}"
CHANNEL_PROFILE="${CHANNEL_PROFILE:-ManufacturerMaintenanceChannel}"

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BLUE='\033[0;34m'; NC='\033[0m'

log_info()  { echo -e "${GREEN}[OK]${NC} $1"; }
log_warn()  { echo -e "${YELLOW}[!!]${NC} $1"; }
log_error() { echo -e "${RED}[ERR] $1${NC}"; exit 1; }
log_step()  { echo -e "\n${BLUE}=== Step: $1 ===${NC}"; }
log_debug() { echo -e "     -> $1"; }

# Helper: copy all files from src to dst
copy_dir_contents() {
    local src="$1" dst="$2" label="$3"
    if [[ -d "$src" ]] && ls -A "$src" 2>/dev/null | grep -q .; then
        cp "$src"/* "$dst/" 2>/dev/null \
            && log_debug "Copied: $label" \
            || log_warn  "Partial copy failed: $label"
    else
        log_warn "Source empty or missing — skipping: $label"
    fi
}

# ═══════════════════════════════════════════════════════════════════════════
# STEP 0: Preflight
# ═══════════════════════════════════════════════════════════════════════════

log_step "0. Preflight Checks"

for bin in cryptogen configtxgen; do
    command -v "$bin" &>/dev/null \
        || log_error "'$bin' not found. Use hyperledger/fabric-tools image."
    log_info "$bin found: $(command -v "$bin")"
done

[[ -d "$CONFIG_DIR" ]]                    || log_error "Config dir missing: $CONFIG_DIR"
[[ -f "$CONFIG_DIR/crypto-config.yaml" ]] || log_error "Missing: $CONFIG_DIR/crypto-config.yaml"
[[ -f "$CONFIG_DIR/configtx.yaml" ]]      || log_error "Missing: $CONFIG_DIR/configtx.yaml"

# Warn early if profile names won't be found — avoids cryptic configtxgen errors
grep -q "$GENESIS_PROFILE" "$CONFIG_DIR/configtx.yaml" \
    || log_warn "Profile '$GENESIS_PROFILE' not found in configtx.yaml"
grep -q "$CHANNEL_PROFILE" "$CONFIG_DIR/configtx.yaml" \
    || log_warn "Profile '$CHANNEL_PROFILE' not found in configtx.yaml"

log_info "Preflight passed"

# ═══════════════════════════════════════════════════════════════════════════
# STEP 1: Generate cryptographic material (idempotent)
# ═══════════════════════════════════════════════════════════════════════════

log_step "1. Generate Cryptographic Material"

# FIX: Use dynamic discovery instead of hardcoded path like
#      "orderer.orderer.example.com" — works with any domain in crypto-config.yaml
ORDERER_CERT_EXISTS=false
if find "$ORGS_DIR/ordererOrganizations" -name "server.crt" -path "*/tls/*" 2>/dev/null \
        | grep -q .; then
    ORDERER_CERT_EXISTS=true
fi

if [[ "$ORDERER_CERT_EXISTS" == "true" ]]; then
    log_info "Crypto material exists — skipping cryptogen"
else
    log_info "Running cryptogen..."
    mkdir -p "$ORGS_DIR"

    # FIX: wrap find in a subshell so set -e doesn't kill script if dir is empty
    if [[ -d "$ORGS_DIR" ]]; then
        find "$ORGS_DIR" -mindepth 1 -delete 2>/dev/null || true
    fi

    cryptogen generate \
        --config="$CONFIG_DIR/crypto-config.yaml" \
        --output="$ORGS_DIR" \
        || log_error "cryptogen failed. Check crypto-config.yaml."

    log_info "Cryptographic material generated"
fi

# ═══════════════════════════════════════════════════════════════════════════
# STEP 2: Generate channel artifacts (idempotent)
# ═══════════════════════════════════════════════════════════════════════════

log_step "2. Generate Channel Artifacts"

GENESIS_FILE="$ARTIFACTS_DIR/genesis.block"
# FIX: was hardcoded "$ARTIFACTS_DIR/mychannel.tx" — breaks when CHANNEL_NAME != mychannel
CHANNEL_TX_FILE="$ARTIFACTS_DIR/${CHANNEL_NAME}.tx"

if [[ -f "$GENESIS_FILE" ]] && [[ -f "$CHANNEL_TX_FILE" ]]; then
    log_info "Artifacts exist — skipping configtxgen"
else
    mkdir -p "$ARTIFACTS_DIR"
    export FABRIC_CFG_PATH="$CONFIG_DIR"

    log_debug "FABRIC_CFG_PATH = $FABRIC_CFG_PATH"
    log_debug "Genesis profile : $GENESIS_PROFILE"
    log_debug "Channel profile : $CHANNEL_PROFILE"

    log_info "Generating genesis block..."
    configtxgen \
        -profile "$GENESIS_PROFILE" \
        -channelID "$SYSTEM_CHANNEL" \
        -outputBlock "$GENESIS_FILE" \
        || log_error "configtxgen genesis failed. Verify '$GENESIS_PROFILE' in configtx.yaml."

    log_info "Generating channel transaction..."
    configtxgen \
        -profile "$CHANNEL_PROFILE" \
        -outputCreateChannelTx "$CHANNEL_TX_FILE" \
        -channelID "$CHANNEL_NAME" \
        || log_error "configtxgen channel tx failed. Verify '$CHANNEL_PROFILE' in configtx.yaml."

    log_info "Channel artifacts generated"
fi

# Copy genesis.block to organizations dir for unified volume mount
log_info "Copying genesis.block to organizations directory..."
cp "$GENESIS_FILE" "$ORGS_DIR/genesis.block" \
    || log_error "Failed to copy genesis.block"

# Copy core.yaml to organizations dir for peer configuration
log_info "Setting up peer core.yaml..."
if [[ -f "$CONFIG_DIR/core.yaml" ]]; then
    cp "$CONFIG_DIR/core.yaml" "$ORGS_DIR/core.yaml" \
        && log_debug "Copied core.yaml" \
        || log_warn "Failed to copy core.yaml"
else
    log_warn "core.yaml not found in $CONFIG_DIR"
fi

# ═══════════════════════════════════════════════════════════════════════════
# STEP 3: Flatten certificate structure for Docker volume mounts
#
# FIX: ALL mkdir -p calls happen HERE, before any cp operations.
# Original script created "$ORGS_DIR/tls" in Step 4 but tried to
# copy into it in Step 3 — the directory didn't exist yet.
# ═══════════════════════════════════════════════════════════════════════════

log_step "3. Flatten Certificate Structure"

# Create ALL destination dirs before any copy
mkdir -p \
    "$ORGS_DIR/signcerts" \
    "$ORGS_DIR/cacerts" \
    "$ORGS_DIR/admincerts" \
    "$ORGS_DIR/keystore" \
    "$ORGS_DIR/tlscacerts" \
    "$ORGS_DIR/tls" \
    "$ORGS_DIR/msp/signcerts" \
    "$ORGS_DIR/msp/cacerts" \
    "$ORGS_DIR/msp/keystore" \
    "$ORGS_DIR/msp/admincerts"

# Discover orderer paths dynamically
ORDERER_ORG_DIR=$(find "$ORGS_DIR/ordererOrganizations" \
    -maxdepth 1 -mindepth 1 -type d 2>/dev/null | head -1)
[[ -n "$ORDERER_ORG_DIR" ]] \
    || log_error "No orderer org found in $ORGS_DIR/ordererOrganizations"

ORDERER_NODE_DIR=$(find "$ORDERER_ORG_DIR/orderers" \
    -maxdepth 1 -mindepth 1 -type d 2>/dev/null | head -1)
[[ -n "$ORDERER_NODE_DIR" ]] \
    || log_error "No orderer node found in $ORDERER_ORG_DIR/orderers"

ORDERER_MSP_DIR="$ORDERER_NODE_DIR/msp"
ORDERER_TLS_DIR="$ORDERER_NODE_DIR/tls"
log_debug "Orderer node: $ORDERER_NODE_DIR"

[[ -d "$ORDERER_MSP_DIR" ]] || log_error "Orderer MSP not found: $ORDERER_MSP_DIR"
[[ -d "$ORDERER_TLS_DIR" ]] || log_error "Orderer TLS not found: $ORDERER_TLS_DIR"

# Orderer MSP
log_info "Copying orderer MSP..."
copy_dir_contents "$ORDERER_MSP_DIR/signcerts" "$ORGS_DIR/signcerts" "orderer signcerts"
copy_dir_contents "$ORDERER_MSP_DIR/cacerts"   "$ORGS_DIR/cacerts"   "orderer cacerts"
copy_dir_contents "$ORDERER_MSP_DIR/keystore"  "$ORGS_DIR/keystore"  "orderer keystore"

# admincerts — FIX: original used fragile [[ "$(ls -A ...)" ]] quoting
if [[ -d "$ORDERER_MSP_DIR/admincerts" ]] \
        && ls -A "$ORDERER_MSP_DIR/admincerts" 2>/dev/null | grep -q .; then
    copy_dir_contents "$ORDERER_MSP_DIR/admincerts" "$ORGS_DIR/admincerts" "orderer admincerts"
else
    # Try orderer admin user signcert
    ADMIN_CERT=$(find "$ORDERER_ORG_DIR/users" \
        -name "*.pem" -path "*/signcerts/*" 2>/dev/null | head -1)
    if [[ -n "$ADMIN_CERT" ]]; then
        cp "$ADMIN_CERT" "$ORGS_DIR/admincerts/" \
            && log_debug "admincerts: used orderer admin user cert" \
            || log_warn  "admincerts: copy of admin user cert failed"
    else
        # Last resort: use signcert
        FIRST_SIGNCERT=$(find "$ORGS_DIR/signcerts" -type f 2>/dev/null | head -1)
        if [[ -n "$FIRST_SIGNCERT" ]]; then
            cp "$FIRST_SIGNCERT" "$ORGS_DIR/admincerts/" \
                && log_debug "admincerts: fallback to signcert" \
                || log_warn  "admincerts: fallback copy failed"
        else
            log_warn "admincerts is empty — orderer may refuse to start"
        fi
    fi
fi

# Orderer TLS
log_info "Copying orderer TLS..."
for tls_file in ca.crt server.crt server.key; do
    if [[ -f "$ORDERER_TLS_DIR/$tls_file" ]]; then
        cp "$ORDERER_TLS_DIR/$tls_file" "$ORGS_DIR/tls/$tls_file"
        log_debug "Copied TLS: $tls_file"
    else
        log_warn "Orderer TLS file missing: $tls_file"
    fi
done
# Also put ca.crt in tlscacerts for peer TLS root verification
[[ -f "$ORDERER_TLS_DIR/ca.crt" ]] \
    && cp "$ORDERER_TLS_DIR/ca.crt" "$ORGS_DIR/tlscacerts/ca.crt" || true

# Create NodeOU config file for orderer MSP (needed when admincerts is empty but NodeOU is enabled)
log_info "Creating orderer NodeOU configuration..."
mkdir -p "$ORGS_DIR"

# Discover the actual CA certificate file in cacerts directory
CA_CERT=$(find "$ORGS_DIR/cacerts" -name "*.pem" -type f 2>/dev/null | head -1)
if [[ -n "$CA_CERT" ]]; then
    CA_CERT_NAME=$(basename "$CA_CERT")
    log_debug "Using CA cert: $CA_CERT_NAME"
else
    CA_CERT_NAME="ca.pem"
    log_warn "No CA cert found, using default name: $CA_CERT_NAME"
fi

cat > "$ORGS_DIR/config.yaml" <<EOF
NodeOUs:
  Enable: true
  ClientOUIdentifier:
    Certificate: cacerts/$CA_CERT_NAME
    OrganizationalUnitIdentifier: client
  PeerOUIdentifier:
    Certificate: cacerts/$CA_CERT_NAME
    OrganizationalUnitIdentifier: peer
  AdminOUIdentifier:
    Certificate: cacerts/$CA_CERT_NAME
    OrganizationalUnitIdentifier: admin
  OrdererOUIdentifier:
    Certificate: cacerts/$CA_CERT_NAME
    OrganizationalUnitIdentifier: orderer
EOF
log_debug "Orderer NodeOU config created with cert: $CA_CERT_NAME"

# Peer root MSP
log_info "Copying peer MSP..."
PEER0_MSP=$(find "$ORGS_DIR/peerOrganizations" \
    -maxdepth 4 -name "msp" -type d 2>/dev/null | head -1)
if [[ -n "$PEER0_MSP" ]]; then
    log_debug "Peer MSP source: $PEER0_MSP"
    copy_dir_contents "$PEER0_MSP/signcerts" "$ORGS_DIR/msp/signcerts" "peer msp signcerts"
    copy_dir_contents "$PEER0_MSP/cacerts"   "$ORGS_DIR/msp/cacerts"   "peer msp cacerts"
    copy_dir_contents "$PEER0_MSP/keystore"  "$ORGS_DIR/msp/keystore"  "peer msp keystore"
    log_info "Peer MSP copied"
else
    log_warn "No peer MSP directory found — peer root msp not copied"
fi

# Create NodeOU config file for peer MSP (needed when admincerts is empty but NodeOU is enabled)
log_info "Creating NodeOU configuration..."
mkdir -p "$ORGS_DIR/msp"

# Discover the actual CA certificate file in peer msp/cacerts directory
PEER_CA_CERT=$(find "$ORGS_DIR/msp/cacerts" -name "*.pem" -type f 2>/dev/null | head -1)
if [[ -n "$PEER_CA_CERT" ]]; then
    PEER_CA_CERT_NAME=$(basename "$PEER_CA_CERT")
    log_debug "Using peer CA cert: $PEER_CA_CERT_NAME"
else
    PEER_CA_CERT_NAME="ca.pem"
    log_warn "No peer CA cert found, using default name: $PEER_CA_CERT_NAME"
fi

cat > "$ORGS_DIR/msp/config.yaml" <<EOF
NodeOUs:
  Enable: true
  ClientOUIdentifier:
    Certificate: cacerts/$PEER_CA_CERT_NAME
    OrganizationalUnitIdentifier: client
  PeerOUIdentifier:
    Certificate: cacerts/$PEER_CA_CERT_NAME
    OrganizationalUnitIdentifier: peer
  AdminOUIdentifier:
    Certificate: cacerts/$PEER_CA_CERT_NAME
    OrganizationalUnitIdentifier: admin
  OrdererOUIdentifier:
    Certificate: cacerts/$PEER_CA_CERT_NAME
    OrganizationalUnitIdentifier: orderer
EOF
log_debug "Peer NodeOU config created with cert: $PEER_CA_CERT_NAME"

# ═══════════════════════════════════════════════════════════════════════════
# STEP 4: Verify — exit non-zero if critical files are missing
# ═══════════════════════════════════════════════════════════════════════════

log_step "4. Verify Artifacts"

ERRORS=0

check_file() {
    local path="$1" label="$2"
    if [[ -f "$path" ]]; then
        local sz; sz=$(du -sh "$path" 2>/dev/null | cut -f1)
        printf "  OK      %s (%s)\n" "$label" "$sz"
    else
        printf "  MISSING %s\n" "$label"
        ERRORS=$((ERRORS + 1))
    fi
}

check_dir_nonempty() {
    local path="$1" label="$2"
    local count; count=$(find "$path" -maxdepth 1 -type f 2>/dev/null | wc -l)
    if [[ "$count" -gt 0 ]]; then
        printf "  OK      %s (%d file(s))\n" "$label" "$count"
    else
        printf "  EMPTY   %s\n" "$label"
        ERRORS=$((ERRORS + 1))
    fi
}

echo ""
echo "Channel artifacts:"
check_file "$ORGS_DIR/genesis.block"  "genesis.block (in organizations)"
check_file "$CHANNEL_TX_FILE"         "${CHANNEL_NAME}.tx"

echo ""
echo "Orderer flat MSP:"
check_dir_nonempty "$ORGS_DIR/signcerts"  "signcerts"
check_dir_nonempty "$ORGS_DIR/cacerts"    "cacerts"
check_dir_nonempty "$ORGS_DIR/admincerts" "admincerts"
check_dir_nonempty "$ORGS_DIR/keystore"   "keystore"
check_dir_nonempty "$ORGS_DIR/tlscacerts" "tlscacerts"

echo ""
echo "Orderer TLS:"
check_file "$ORGS_DIR/tls/ca.crt"     "tls/ca.crt"
check_file "$ORGS_DIR/tls/server.crt" "tls/server.crt"
check_file "$ORGS_DIR/tls/server.key" "tls/server.key"

echo ""
echo "Peer root MSP:"
check_dir_nonempty "$ORGS_DIR/msp/signcerts" "msp/signcerts"
check_dir_nonempty "$ORGS_DIR/msp/cacerts"   "msp/cacerts"

echo ""
# FIX: original only printed warnings — now exits non-zero so docker-compose
#      knows the init container actually failed
if [[ $ERRORS -gt 0 ]]; then
    log_error "Verification failed: $ERRORS artifact(s) missing (see above)"
fi

# ═══════════════════════════════════════════════════════════════════════════
# DONE
# ═══════════════════════════════════════════════════════════════════════════

log_step "Done"
echo ""
echo "  CHANNEL_NAME  : $CHANNEL_NAME"
echo "  ARTIFACTS_DIR : $ARTIFACTS_DIR"
echo "  ORGS_DIR      : $ORGS_DIR"
echo ""
log_info "Init container finished. Blockchain services may now start."
echo ""

exit 0