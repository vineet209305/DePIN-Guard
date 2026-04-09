FROM hyperledger/fabric-tools:2.5

# Install required tools
RUN apt-get update && apt-get install -y \
    curl \
    netcat \
    jq \
    && rm -rf /var/lib/apt/lists/*

# Copy init scripts
COPY blockchain-init.sh /scripts/blockchain-init.sh
COPY check-peer.sh /scripts/check-peer.sh
COPY check-orderer.sh /scripts/check-orderer.sh

RUN chmod +x /scripts/*.sh

WORKDIR /root

CMD ["/scripts/blockchain-init.sh"]
