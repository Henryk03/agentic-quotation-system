
import sys
import platform
import subprocess
from pathlib import Path
from typing import Literal


def get_venv_python() -> Path:
    """"""

    venv_path: Path = Path(__file__).parent / ".venv"
    
    if platform.system() == "Windows":
        return venv_path / "Scripts" / "python.exe"
    
    return venv_path / "bin" / "python"



def main() -> Literal[1, 0]:
    """"""
    
    venv_python: Path = get_venv_python()
    
    if not venv_python.exists():
        print("❌ Virtual environment not found!")
        print("   Please run 'python setup_frontend.py' first")

        return 1
    
    try:
        result: subprocess.CompletedProcess = subprocess.run(
            [str(venv_python), "-m", "frontend"],
            cwd=Path(__file__).parent
        )

        if result.returncode != 0:
            return 1
        
        return 0
        
    except KeyboardInterrupt:
        print("\n👋 Frontend stopped by user\n")
        return 0
    
    except Exception as e:
        print(f"\n❌ Error launching frontend: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())