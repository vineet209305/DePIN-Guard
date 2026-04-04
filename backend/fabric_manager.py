import subprocess
import os
import json
import shutil
import socket
from typing import Any, Dict, List

REPO_ROOT    = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BLOCKCHAIN_DIR = os.path.join(REPO_ROOT, "blockchain")
BIN_DIR      = os.path.join(BLOCKCHAIN_DIR, "fabric-samples", "bin")
CONFIG_DIR   = os.path.join(BLOCKCHAIN_DIR, "fabric-samples", "config")

ORDERER_ADDRESS = os.getenv("FABRIC_ORDERER_ADDRESS", "127.0.0.1:7050")
PEER1_ADDRESS   = os.getenv("FABRIC_PEER1_ADDRESS", "127.0.0.1:7051")
PEER2_ADDRESS   = os.getenv("FABRIC_PEER2_ADDRESS", "127.0.0.1:9051")

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
env["PATH"]             = f"{BIN_DIR}{os.pathsep}{env.get('PATH', '')}"
env["FABRIC_CFG_PATH"]  = CONFIG_DIR
env["CORE_PEER_TLS_ENABLED"]     = "true"
env["CORE_PEER_LOCALMSPID"]      = "ManufacturerMSP"
env["CORE_PEER_TLS_ROOTCERT_FILE"] = MFR_TLS
env["CORE_PEER_MSPCONFIGPATH"]   = MFR_MSP
env["CORE_PEER_ADDRESS"]         = PEER1_ADDRESS


def _is_tcp_reachable(address: str, timeout_seconds: float = 1.2) -> bool:
    try:
        host, port_text = address.rsplit(":", 1)
        port = int(port_text)
    except ValueError:
        return False

    try:
        with socket.create_connection((host, port), timeout=timeout_seconds):
            return True
    except OSError:
        return False


class FabricManager:
    def __init__(self):
        self.peer_executable = os.path.join(BIN_DIR, "peer") if os.path.exists(
            os.path.join(BIN_DIR, "peer")) else shutil.which("peer")

        if self.peer_executable:
            print(f"✅ Hyperledger Fabric found at: {self.peer_executable}")
            print(f"🔗 Targeted Peers: {PEER1_ADDRESS} (Manufacturer) & {PEER2_ADDRESS} (Maintenance)")
        else:
            print("⚠️ 'peer' binary not found. Running in SIMULATION MODE.")

    def network_status(self) -> Dict[str, Any]:
        checks = {
            "orderer": _is_tcp_reachable(ORDERER_ADDRESS),
            "peer1": _is_tcp_reachable(PEER1_ADDRESS),
            "peer2": _is_tcp_reachable(PEER2_ADDRESS),
        }
        return {
            "ready": all(checks.values()),
            "addresses": {
                "orderer": ORDERER_ADDRESS,
                "peer1": PEER1_ADDRESS,
                "peer2": PEER2_ADDRESS,
            },
            "checks": checks,
        }

    def submit_transaction(self, function_name: str, args_list: List[str]) -> Dict[str, Any]:
        print(f"⚡ BLOCKCHAIN: Submitting '{function_name}' with {args_list}")

        if not self.peer_executable:
            return {"status": "simulated"}

        status = self.network_status()
        if not status["ready"]:
            error_message = (
                "Fabric network is not reachable from backend. "
                f"Checks={status['checks']} Addresses={status['addresses']}"
            )
            print(f"❌ Transaction Skipped: {error_message}")
            return {"status": "error", "error": error_message, "network": status}

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

            result = subprocess.run(command, env=env, capture_output=True, text=True, timeout=25)

            if result.returncode == 0:
                print("✅ Transaction Successful")
                return {"status": "success", "output": result.stdout}
            else:
                stderr = (result.stderr or "").strip()
                hint = ""
                lowered = stderr.lower()
                if "connection refused" in lowered or "broken pipe" in lowered:
                    hint = (
                        " Ensure Fabric containers and chaincode are running on the backend host. "
                        "Check peer0/orderer container status and port mappings."
                    )
                print(f"❌ Transaction Failed: {stderr}{hint}")
                return {"status": "error", "error": f"{stderr}{hint}"}

        except subprocess.TimeoutExpired:
            timeout_msg = "Fabric invoke timed out after 25s"
            print(f"❌ Transaction Timeout: {timeout_msg}")
            return {"status": "error", "error": timeout_msg}

        except Exception as e:
            print(f"❌ Execution Error: {e}")
            return {"status": "error", "error": str(e)}

    def query_transaction(self, function_name: str, arg: str):
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