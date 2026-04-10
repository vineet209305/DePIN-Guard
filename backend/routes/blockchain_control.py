import subprocess
import os
from fastapi import APIRouter, HTTPException, Depends, Security
from fastapi.security import APIKeyHeader
from pydantic import BaseModel
import time

router = APIRouter()

# Blockchain control paths
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DOCKER_COMPOSE_FILE = os.path.join(REPO_ROOT, "docker", "docker-compose-custom.yaml")
PROJECT_NAME = "depin-fabric"

# ───────────────────────────────────────────────────────────────────────────
# Pydantic Models
# ───────────────────────────────────────────────────────────────────────────
class BlockchainStatus(BaseModel):
    status: str  # "running", "stopped", "error"
    message: str
    containers: list = []
    ports: dict = {}

class BlockchainAction(BaseModel):
    action: str  # "start", "stop", "restart"

# ───────────────────────────────────────────────────────────────────────────
# Helper Functions
# ───────────────────────────────────────────────────────────────────────────

def _run_command(cmd: list, timeout: int = 60) -> tuple[bool, str]:
    """Run shell command and return (success, output)"""
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=os.path.dirname(DOCKER_COMPOSE_FILE)
        )
        return result.returncode == 0, result.stdout + result.stderr
    except subprocess.TimeoutExpired:
        return False, f"Command timed out after {timeout}s"
    except Exception as e:
        return False, str(e)

def _get_container_status() -> dict:
    """Get status of all Fabric containers"""
    success, output = _run_command(["docker", "ps", "--format", "{{.Names}}\\t{{.Status}}"])
    
    containers = {}
    if success and output.strip():
        for line in output.strip().split('\n'):
            if line:
                parts = line.split('\t')
                if len(parts) == 2:
                    name, status = parts
                    if 'depin' in name.lower() or 'fabric' in name.lower():
                        containers[name] = status
    
    return containers

def _get_exposed_ports() -> dict:
    """Get exposed ports from running containers"""
    success, output = _run_command(["docker", "ps", "--format", "{{.Names}}\\t{{.Ports}}"])
    
    ports = {}
    if success and output.strip():
        for line in output.strip().split('\n'):
            if line:
                parts = line.split('\t')
                if len(parts) == 2:
                    name, port_info = parts
                    if 'depin' in name.lower() or 'fabric' in name.lower():
                        ports[name] = port_info
    
    return ports

# ───────────────────────────────────────────────────────────────────────────
# Routes
# ───────────────────────────────────────────────────────────────────────────

@router.get("/blockchain/status")
async def get_blockchain_status() -> BlockchainStatus:
    """
    Get current blockchain status
    Returns: running/stopped/error + container details
    """
    containers = _get_container_status()
    ports = _get_exposed_ports()
    
    if not containers:
        return BlockchainStatus(
            status="stopped",
            message="Blockchain containers are not running",
            containers=[],
            ports={}
        )
    
    running_count = sum(1 for status in containers.values() if "Up" in status)
    expected_count = 3  # orderer + 2 peers
    
    if running_count == expected_count:
        return BlockchainStatus(
            status="running",
            message=f"All {expected_count} Fabric containers running",
            containers=list(containers.keys()),
            ports=ports
        )
    else:
        return BlockchainStatus(
            status="partial",
            message=f"Only {running_count}/{expected_count} containers running",
            containers=list(containers.keys()),
            ports=ports
        )

@router.post("/blockchain/start")
async def start_blockchain() -> BlockchainStatus:
    """
    Start Hyperledger Fabric blockchain containers
    Equivalent to: docker compose -p depin-fabric -f docker/docker-compose-custom.yaml up -d
    """
    try:
        # First check if already running
        existing = _get_container_status()
        if existing:
            running_count = sum(1 for status in existing.values() if "Up" in status)
            if running_count >= 2:
                return BlockchainStatus(
                    status="running",
                    message="Blockchain is already running",
                    containers=list(existing.keys()),
                    ports=_get_exposed_ports()
                )
        
        # Start containers
        print(f"[BLOCKCHAIN] Starting Docker Compose from {DOCKER_COMPOSE_FILE}")
        success, output = _run_command([
            "docker", "compose",
            "-p", PROJECT_NAME,
            "-f", DOCKER_COMPOSE_FILE,
            "up", "-d", "--remove-orphans"
        ], timeout=120)
        
        if not success:
            raise Exception(f"docker compose up failed: {output}")
        
        # Wait for containers to be ready
        print("[BLOCKCHAIN] Waiting for containers to start...")
        time.sleep(5)
        
        # Verify startup
        containers = _get_container_status()
        ports = _get_exposed_ports()
        
        if containers:
            running_count = sum(1 for status in containers.values() if "Up" in status)
            return BlockchainStatus(
                status="running" if running_count >= 2 else "partial",
                message=f"Blockchain started ({running_count} containers up)",
                containers=list(containers.keys()),
                ports=ports
            )
        else:
            raise Exception("Containers started but status check failed")
    
    except Exception as e:
        print(f"[BLOCKCHAIN ERROR] {str(e)}")
        return BlockchainStatus(
            status="error",
            message=f"Failed to start blockchain: {str(e)}",
            containers=[],
            ports={}
        )

@router.post("/blockchain/stop")
async def stop_blockchain() -> BlockchainStatus:
    """
    Stop Hyperledger Fabric blockchain containers
    Equivalent to: docker compose -p depin-fabric -f docker/docker-compose-custom.yaml down
    """
    try:
        print(f"[BLOCKCHAIN] Stopping Docker Compose")
        success, output = _run_command([
            "docker", "compose",
            "-p", PROJECT_NAME,
            "-f", DOCKER_COMPOSE_FILE,
            "down"
        ], timeout=60)
        
        if not success:
            raise Exception(f"docker compose down failed: {output}")
        
        time.sleep(2)
        
        # Verify stopped
        containers = _get_container_status()
        
        if not containers:
            return BlockchainStatus(
                status="stopped",
                message="Blockchain stopped successfully",
                containers=[],
                ports={}
            )
        else:
            return BlockchainStatus(
                status="partial",
                message=f"Some containers still running: {list(containers.keys())}",
                containers=list(containers.keys()),
                ports=_get_exposed_ports()
            )
    
    except Exception as e:
        print(f"[BLOCKCHAIN ERROR] {str(e)}")
        return BlockchainStatus(
            status="error",
            message=f"Failed to stop blockchain: {str(e)}",
            containers=_get_container_status(),
            ports=_get_exposed_ports()
        )

@router.post("/blockchain/restart")
async def restart_blockchain() -> BlockchainStatus:
    """
    Restart Hyperledger Fabric blockchain (stop + start)
    """
    try:
        # Stop
        await stop_blockchain()
        time.sleep(3)
        
        # Start
        return await start_blockchain()
    
    except Exception as e:
        print(f"[BLOCKCHAIN ERROR] {str(e)}")
        return BlockchainStatus(
            status="error",
            message=f"Failed to restart blockchain: {str(e)}",
            containers=[],
            ports={}
        )
