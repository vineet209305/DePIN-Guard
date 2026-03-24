import subprocess
import threading
import sys
import os
import time
import signal
 
# ─── ANSI Color Codes ───
RESET  = "\033[0m"
BOLD   = "\033[1m"
RED    = "\033[91m"
GREEN  = "\033[92m"
YELLOW = "\033[93m"
BLUE   = "\033[94m"
CYAN   = "\033[96m"
MAGENTA= "\033[95m"
WHITE  = "\033[97m"
 
# ─── Service Config ───
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
 
SERVICES = [
    {
        "name":    "AI Service",
        "color":   MAGENTA,
        "dir":     os.path.join(BASE_DIR, "ai-service"),
        "cmd":     [sys.executable, "app.py"],
        "port":    5000,
        "wait":    3,   # seconds to wait before starting next service
    },
    {
        "name":    "Auth Service",
        "color":   YELLOW,
        "dir":     os.path.join(BASE_DIR, "auth-service"),
        "cmd":     [sys.executable, "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"],
        "port":    8001,
        "wait":    2,
    },
    {
        "name":    "Backend",
        "color":   BLUE,
        "dir":     os.path.join(BASE_DIR, "backend"),
        "cmd":     [sys.executable, "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"],
        "port":    8000,
        "wait":    3,
    },
    {
        "name":    "Frontend",
        "color":   CYAN,
        "dir":     os.path.join(BASE_DIR, "frontend"),
        "cmd":     ["npm", "run", "dev"],
        "port":    5173,
        "wait":    4,
    },
    {
        "name":    "IoT Simulator",
        "color":   GREEN,
        "dir":     os.path.join(BASE_DIR, "iot-simulator"),
        "cmd":     [sys.executable, "simulator.py"],
        "port":    None,
        "wait":    0,
    },
]
 
processes = []
 
def prefix_output(process, name, color):
    """Read subprocess output and print with colored service name prefix."""
    prefix = f"{color}{BOLD}[{name}]{RESET} "
    try:
        for line in iter(process.stdout.readline, b""):
            try:
                decoded = line.decode("utf-8", errors="replace").rstrip()
                if decoded:
                    print(f"{prefix}{decoded}")
            except Exception:
                pass
    except Exception:
        pass
 
def start_service(service):
    """Start a single service and return the process."""
    name   = service["name"]
    color  = service["color"]
    cwd    = service["dir"]
    cmd    = service["cmd"]
 
    print(f"\n{color}{BOLD}{'─'*50}{RESET}")
    print(f"{color}{BOLD}  Starting: {name}{RESET}")
    if service["port"]:
        print(f"{color}  URL: http://localhost:{service['port']}{RESET}")
    print(f"{color}{BOLD}{'─'*50}{RESET}")
 
    # Check directory exists
    if not os.path.isdir(cwd):
        print(f"{RED}  ✗ Directory not found: {cwd}{RESET}")
        return None
 
    try:
        proc = subprocess.Popen(
            cmd,
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            bufsize=1,
        )
 
        # Start output reader thread
        t = threading.Thread(
            target=prefix_output,
            args=(proc, name, color),
            daemon=True
        )
        t.start()
 
        print(f"{color}  ✓ PID {proc.pid} — {name} started{RESET}")
        return proc
 
    except FileNotFoundError as e:
        print(f"{RED}  ✗ Command not found: {cmd[0]}{RESET}")
        print(f"{RED}    Make sure all dependencies are installed.{RESET}")
        print(f"{RED}    Error: {e}{RESET}")
        return None
    except Exception as e:
        print(f"{RED}  ✗ Failed to start {name}: {e}{RESET}")
        return None
 
def check_env():
    """Check that critical files exist before launching."""
    print(f"\n{WHITE}{BOLD}DePIN-Guard — Pre-flight Check{RESET}")
    print(f"{WHITE}{'='*50}{RESET}\n")
 
    checks = [
        (os.path.join(BASE_DIR, "ai-service", "app.py"),              "AI Service app.py"),
        (os.path.join(BASE_DIR, "ai-service", "lstm_autoencoder.pth"),"AI Model weights (lstm_autoencoder.pth)"),
        (os.path.join(BASE_DIR, "ai-service", "scaler.save"),         "AI Scaler (scaler.save)"),
        (os.path.join(BASE_DIR, "ai-service", "threshold.txt"),       "Anomaly Threshold (threshold.txt)"),
        (os.path.join(BASE_DIR, "auth-service", "main.py"),           "Auth Service main.py"),
        (os.path.join(BASE_DIR, "backend", "main.py"),                "Backend main.py"),
        (os.path.join(BASE_DIR, "frontend", "package.json"),          "Frontend package.json"),
        (os.path.join(BASE_DIR, "iot-simulator", "simulator.py"),     "IoT Simulator simulator.py"),
    ]
 
    all_ok = True
    for path, label in checks:
        exists = os.path.isfile(path)
        icon   = f"{GREEN}✓{RESET}" if exists else f"{RED}✗{RESET}"
        status = f"{GREEN}Found{RESET}" if exists else f"{RED}MISSING{RESET}"
        print(f"  {icon} {label:<45} {status}")
        if not exists:
            all_ok = False
 
    # Check .env file
    env_path = os.path.join(BASE_DIR, ".env")
    if os.path.isfile(env_path):
        print(f"  {GREEN}✓{RESET} .env file{' '*42} {GREEN}Found{RESET}")
    else:
        print(f"  {YELLOW}⚠{RESET} .env file{' '*42} {YELLOW}Missing (using defaults){RESET}")
 
    print()
 
    if not all_ok:
        print(f"{RED}{BOLD}  Some required files are missing!{RESET}")
        print(f"{YELLOW}  Run these first:{RESET}")
        print(f"{YELLOW}    cd ai-service && python train.py && python threshold.py{RESET}")
        print()
        resp = input(f"{YELLOW}  Continue anyway? (y/N): {RESET}").strip().lower()
        if resp != "y":
            sys.exit(1)
    else:
        print(f"  {GREEN}{BOLD}All checks passed!{RESET}\n")
 
def shutdown(signum=None, frame=None):
    """Gracefully shut down all services."""
    print(f"\n\n{YELLOW}{BOLD}{'='*50}{RESET}")
    print(f"{YELLOW}{BOLD}  Shutting down all DePIN-Guard services...{RESET}")
    print(f"{YELLOW}{BOLD}{'='*50}{RESET}\n")
 
    for i, proc in enumerate(processes):
        if proc and proc.poll() is None:
            name = SERVICES[i]["name"] if i < len(SERVICES) else f"Service {i}"
            color = SERVICES[i]["color"] if i < len(SERVICES) else WHITE
            try:
                proc.terminate()
                proc.wait(timeout=3)
                print(f"  {color}✓ {name} stopped{RESET}")
            except subprocess.TimeoutExpired:
                proc.kill()
                print(f"  {RED}✗ {name} force-killed{RESET}")
            except Exception as e:
                print(f"  {RED}✗ Error stopping service: {e}{RESET}")
 
    print(f"\n{GREEN}{BOLD}  All services stopped. Goodbye!{RESET}\n")
    sys.exit(0)
 
def print_banner():
    banner = f"""
{CYAN}{BOLD}
  ██████╗ ███████╗██████╗ ██╗███╗   ██╗      ██████╗ ██╗   ██╗ █████╗ ██████╗ ██████╗
  ██╔══██╗██╔════╝██╔══██╗██║████╗  ██║     ██╔════╝ ██║   ██║██╔══██╗██╔══██╗██╔══██╗
  ██║  ██║█████╗  ██████╔╝██║██╔██╗ ██║     ██║  ███╗██║   ██║███████║██████╔╝██║  ██║
  ██║  ██║██╔══╝  ██╔═══╝ ██║██║╚██╗██║     ██║   ██║██║   ██║██╔══██║██╔══██╗██║  ██║
  ██████╔╝███████╗██║     ██║██║ ╚████║     ╚██████╔╝╚██████╔╝██║  ██║██║  ██║██████╔╝
  ╚═════╝ ╚══════╝╚═╝     ╚═╝╚═╝  ╚═══╝      ╚═════╝  ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝╚═════╝
{RESET}
{WHITE}         Decentralized IoT Monitoring | Blockchain + AI + Security{RESET}
{WHITE}         Team: Mohit | Prateek | Priyanshu | Vineet{RESET}
"""
    print(banner)
 
def print_urls():
    print(f"\n{GREEN}{BOLD}{'='*50}")
    print(f"  🚀 DePIN-Guard is LIVE!")
    print(f"{'='*50}{RESET}\n")
    print(f"  {CYAN}Dashboard:    http://localhost:5173{RESET}")
    print(f"  {BLUE}Backend API:  http://localhost:8000{RESET}")
    print(f"  {BLUE}API Docs:     http://localhost:8000/docs{RESET}")
    print(f"  {MAGENTA}AI Service:   http://localhost:5000{RESET}")
    print(f"  {YELLOW}Auth Service: http://localhost:8001{RESET}")
    print(f"\n  {WHITE}Login: admin / securepass{RESET}")
    print(f"\n  {RED}Press Ctrl+C to stop all services{RESET}\n")
 
def main():
    print_banner()
    check_env()
 
    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGINT,  shutdown)
    signal.signal(signal.SIGTERM, shutdown)
 
    print(f"{WHITE}{BOLD}Starting services...{RESET}")
 
    for service in SERVICES:
        proc = start_service(service)
        processes.append(proc)
 
        wait = service.get("wait", 2)
        if wait > 0:
            print(f"  {WHITE}Waiting {wait}s for {service['name']} to initialize...{RESET}")
            time.sleep(wait)
 
    print_urls()
 
    # Keep main thread alive
    try:
        while True:
            # Check if any critical service died
            for i, proc in enumerate(processes):
                if proc and proc.poll() is not None:
                    name  = SERVICES[i]["name"] if i < len(SERVICES) else f"Service {i}"
                    color = SERVICES[i]["color"] if i < len(SERVICES) else WHITE
                    code  = proc.poll()
                    print(f"\n{RED}{BOLD}  ⚠ {name} exited with code {code}!{RESET}")
                    print(f"{YELLOW}  Check the output above for errors.{RESET}\n")
                    processes[i] = None   # mark as dead, don't re-check
            time.sleep(5)
    except KeyboardInterrupt:
        shutdown()
 
if __name__ == "__main__":
    main()