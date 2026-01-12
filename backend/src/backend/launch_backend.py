import sys
import subprocess
from pathlib import Path
import venv
import importlib

# Percorsi
BASE_DIR = Path(__file__).parent
VENV_DIR = BASE_DIR / ".venv"
SRC_DIR = BASE_DIR.parent  # directory principale del progetto

# Modulo e funzione del server
SERVER_MODULE = "backend.server.websocket_server"
SERVER_FUNCTION = "start_server"

def create_venv(venv_path: Path):
    """Crea il virtual environment se non esiste."""
    print(f"Creating virtual environment at {venv_path}...")
    venv.create(venv_path, with_pip=True)
    print("Virtual environment created.")

def run_in_venv(venv_path: Path, command: list):
    """Esegue un comando all'interno del venv."""
    if sys.platform == "win32":
        python_bin = venv_path / "Scripts" / "python.exe"
    else:
        python_bin = venv_path / "bin" / "python"

    full_command = [str(python_bin)] + command
    subprocess.check_call(full_command)

def install_dependencies(venv_path: Path):
    """Installa le dipendenze del progetto."""
    print("Installing dependencies...")
    run_in_venv(venv_path, ["-m", "pip", "install", "--upgrade", "pip", "setuptools", "wheel"])
    
    # Installa dal pyproject.toml corretto
    run_in_venv(venv_path, ["-m", "pip", "install", str(BASE_DIR.parent)])  # BASE_DIR.parent = backend/
    print("Dependencies installed.")

def main():
    if not VENV_DIR.exists():
        create_venv(VENV_DIR)
        install_dependencies(VENV_DIR)
    else:
        print(f"Using existing virtual environment at {VENV_DIR}")

    # Aggiungi il src al path per poter importare il server
    sys.path.insert(0, str(SRC_DIR / "src"))

    # Importa dinamicamente il modulo del server
    server_module = importlib.import_module(SERVER_MODULE)
    start_func = getattr(server_module, SERVER_FUNCTION)

    # Lancia il server
    print("Starting backend server...")
    start_func()

if __name__ == "__main__":
    main()