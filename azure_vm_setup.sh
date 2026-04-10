#!/bin/bash
# azure_vm_setup.sh
# Run this on the Azure VM after SSH-ing in
# VM: Ubuntu 22.04 LTS, Standard_D4s_v5 (4 vCPU, 16GB RAM)
# Usage: bash azure_vm_setup.sh

set -e

echo "======================================================"
echo " DePIN-Guard Blockchain — Azure VM Setup"
echo " Ubuntu 22.04 LTS | 4-vCPU | 16GB RAM"
echo "======================================================"
echo ""

# ── STEP 1: System update ──────────────────────────────────
echo "[1/8] Updating system packages..."
sudo apt-get update -y && sudo apt-get upgrade -y

# ── STEP 2: Install Docker ─────────────────────────────────
echo "[2/8] Installing Docker..."
sudo apt-get install -y ca-certificates curl gnupg lsb-release git jq openssl
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
  https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update -y
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
sudo usermod -aG docker $USER

echo "Docker version: $(docker --version)"

# ── STEP 3: Install Go 1.21 ────────────────────────────────
echo "[3/8] Installing Go..."
wget -q https://go.dev/dl/go1.21.13.linux-amd64.tar.gz
sudo rm -rf /usr/local/go
sudo tar -C /usr/local -xzf go1.21.13.linux-amd64.tar.gz
rm go1.21.13.linux-amd64.tar.gz
echo 'export PATH=$PATH:/usr/local/go/bin' >> ~/.bashrc
export PATH=$PATH:/usr/local/go/bin
echo "Go version: $(go version)"

# ── STEP 4: Clone repo ─────────────────────────────────────
echo "[4/8] Cloning DePIN-Guard repository..."
cd ~
git clone https://github.com/MohitSingh-2335/DePIN-Guard.git
cd DePIN-Guard

# ── STEP 5: Install Fabric binaries ────────────────────────
echo "[5/8] Installing Hyperledger Fabric binaries..."
cd blockchain
chmod +x install-fabric.sh complete_setup.sh deploy_chaincode.sh
./install-fabric.sh binary
export PATH=$PWD/fabric-samples/bin:$PATH
echo "export PATH=$HOME/DePIN-Guard/blockchain/fabric-samples/bin:\$PATH" >> ~/.bashrc

# ── STEP 6: Pull Fabric Docker images ──────────────────────
echo "[6/8] Pulling Fabric Docker images (3-5 minutes)..."
docker pull hyperledger/fabric-peer:2.5
docker pull hyperledger/fabric-orderer:2.5
docker pull hyperledger/fabric-ccenv:2.5
docker pull hyperledger/fabric-baseos:2.5
docker pull couchdb:3.3.3

# ── STEP 7: Run blockchain setup ──────────────────────────
echo "[7/8] Running blockchain complete setup..."
cd ~/DePIN-Guard/blockchain
./complete_setup.sh --reset

# ── STEP 8: Verify ─────────────────────────────────────────
echo "[8/8] Verifying deployment..."
echo ""
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
echo ""
echo "======================================================"
echo " ✅ Blockchain Deployment Successful!"
echo "======================================================"
echo ""
echo "Ports open on VM:"
echo "  7050  — Orderer"
echo "  7051  — Manufacturer peer"
echo "  9051  — Maintenance peer"
echo "  5984  — CouchDB (Manufacturer)"
echo "  7984  — CouchDB (Maintenance)"
echo ""
echo "To get Azure VM public IP:"
echo "  curl -s ifconfig.me"
echo ""
echo "For backend connection from Priyanshu:"
echo "  Set FABRIC_ORDERER_ADDRESS=<VM_PUBLIC_IP>:7050"
echo "  Set FABRIC_PEER1_ADDRESS=<VM_PUBLIC_IP>:7051"
echo "  Set FABRIC_PEER2_ADDRESS=<VM_PUBLIC_IP>:9051"
echo ""
echo "Containers running:"
docker ps --format "{{.Names}}"
echo ""
