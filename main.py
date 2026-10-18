"""Main launcher for JARVIS Personal Assistant."""
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.interface.cli import run_cli
from app.interface.web.server import start_server

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] in ["--web", "-w", "web"]:
        print("Iniciando JARVIS Web Dashboard em http://127.0.0.1:8080...")
        start_server()
    else:
        run_cli()
