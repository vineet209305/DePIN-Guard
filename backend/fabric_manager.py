import subprocess
import os
import json
import shutil

REPO_ROOT    = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BLOCKCHAIN_DIR = os.path.join(REPO_ROOT, "blockchain")
BIN_DIR      = os.path.join(BLOCKCHAIN_DIR, "fabric-samples", "bin")
CONFIG_DIR   = os.path.join(BLOCKCHAIN_DIR, "fabric-samples", "config")

# Certificate paths — our custom network (not test-network)
MFR_TLS  = os.path.join(BLOCKCHAIN_DIR, "organizations", "peerOrganizations",
                         "manufacturer.example.com", "peers",
                         "peer0.manufacturer.example.com", "tls", "ca.crt")
MFR_MSP  = os.path.join(BLOCKCHAIN_DIR, "organizations", "peerOrganizations",
                         "manufacturer.example.com", "users",
                         "Admin@manufacturer.example.com", "msp")
MNT_TLS  = os.path.join(BLOCKCHAIN_DIR, "organizations", "peerOrganizations",
                         "maintenance.example.com", "peers",
                         "peer0.maintenance.example.com", "tls", "ca.crt")
ORDERER_CA = os.path.join(BLOCKCHAIN_DIR, "organizations", "ordererOrganizations",
                           "orderer.example.com", "orderers",
                           "orderer.orderer.example.com", "msp", "tlscacerts",
                           "tlsca.orderer.example.com-cert.pem")

env = os.environ.copy()
env["PATH"]             = f"{BIN_DIR}:{env['PATH']}"
env["FABRIC_CFG_PATH"]  = CONFIG_DIR
env["CORE_PEER_TLS_ENABLED"]     = "true"
env["CORE_PEER_LOCALMSPID"]      = "ManufacturerMSP"
env["CORE_PEER_TLS_ROOTCERT_FILE"] = MFR_TLS
env["CORE_PEER_MSPCONFIGPATH"]   = MFR_MSP
env["CORE_PEER_ADDRESS"]         = "localhost:7051"

ORDERER_ADDRESS = "localhost:7050"
PEER1_ADDRESS   = "localhost:7051"
PEER2_ADDRESS   = "localhost:9051"


class FabricManager:
    def __init__(self):
        self.peer_executable = os.path.join(BIN_DIR, "peer") if os.path.exists(
            os.path.join(BIN_DIR, "peer")) else shutil.which("peer")

        if self.peer_executable:
            print(f"✅ Hyperledger Fabric found at: {self.peer_executable}")
            print(f"🔗 Targeted Peers: {PEER1_ADDRESS} (Manufacturer) & {PEER2_ADDRESS} (Maintenance)")
        else:
            print("⚠️ 'peer' binary not found. Running in SIMULATION MODE.")

    def submit_transaction(self, function_name, args_list):
        print(f"⚡ BLOCKCHAIN: Submitting '{function_name}' with {args_list}")

        if not self.peer_executable:
            return {"status": "simulated"}

        cmd_args_json = json.dumps({"Args": [function_name] + args_list})

        try:
            command = [
                self.peer_executable, "chaincode", "invoke",
                "-o", ORDERER_ADDRESS,
                "--ordererTLSHostnameOverride", "orderer.example.com",
                "--tls", "--cafile", ORDERER_CA,
                "-C", "mychannel",
                "-n", "depin_cc",
                "--peerAddresses", PEER1_ADDRESS,
                "--tlsRootCertFiles", MFR_TLS,
                "--peerAddresses", PEER2_ADDRESS,
                "--tlsRootCertFiles", MNT_TLS,
                "-c", cmd_args_json
            ]

            result = subprocess.run(command, env=env, capture_output=True, text=True)

            if result.returncode == 0:
                print("✅ Transaction Successful")
                return {"status": "success", "output": result.stdout}
            else:
                print(f"❌ Transaction Failed: {result.stderr}")
                return {"status": "error", "error": result.stderr}

        except Exception as e:
            print(f"❌ Execution Error: {e}")
            return {"status": "error", "error": str(e)}

    def query_transaction(self, function_name, arg):
        if not self.peer_executable:
            return []

        print(f"🔍 BLOCKCHAIN: Querying '{function_name}' for {arg}")
        cmd_args_json = json.dumps({"Args": [function_name, arg]})

        try:
            command = [
                self.peer_executable, "chaincode", "query",
                "-C", "mychannel", "-n", "depin_cc",
                "-c", cmd_args_json
            ]
            result = subprocess.run(command, env=env, capture_output=True, text=True)
            if result.returncode == 0:
                return json.loads(result.stdout)
            return []
        except Exception as e:
            print(f"❌ Query Error: {e}")
            return []


fabric_client = FabricManager()