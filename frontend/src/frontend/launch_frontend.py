
import os
import sys
import subprocess
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
VENV_DIR = PROJECT_ROOT / ".venv"


def venv_python() -> Path:
    """"""

    if os.name == "nt":
        return VENV_DIR / "Scripts" / "python.exe"
    
    return VENV_DIR / "bin" / "python"


def running_inside_venv() -> bool:
    """"""

    return sys.prefix != sys.base_prefix


def create_venv() -> None:
    """"""

    print("[INFO] Creating frontend virtual environment...")
    subprocess.check_call([sys.executable, "-m", "venv", str(VENV_DIR)])

    python = venv_python()
    subprocess.check_call([python, "-m", "pip", "install", "--upgrade", "pip"])
    subprocess.check_call([python, "-m", "pip", "install", "-e", str(PROJECT_ROOT)])


def relaunch_inside_venv() -> None:
    """"""
    
    python = venv_python()
    print("[INFO] Relaunching frontend inside virtual environment...")
    subprocess.check_call([python, __file__])
    sys.exit(0)



def main() -> None:
    if not VENV_DIR.exists():
        create_venv()

    if not running_inside_venv():
        relaunch_inside_venv()

    # --- ORA SEI DENTRO IL VENV ---
    print("[INFO] Starting Agentic frontend UI...")

    ui_entrypoint = (
        Path(__file__).parent / "ui" / "agent_ui.py"
    )

    subprocess.run(
        [
            sys.executable,
            "-m",
            "streamlit",
            "run",
            str(ui_entrypoint),
        ],
        check=True,
    )


if __name__ == "__main__":
    main()