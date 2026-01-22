
import sys
import platform
import subprocess
from pathlib import Path
from typing import Literal


sys.path.append(str(Path(__file__).parent / "src"))

try:
    from backend.config import settings

except ImportError:
    print("Error")
    print()

    sys.exit(1)


def get_venv_python() -> Path:
    """"""

    venv_path = Path(__file__).parent / ".venv"
    
    if platform.system() == "Windows":
        return venv_path / "Scripts" / "python.exe"
    
    return venv_path / "bin" / "python"



def main() -> Literal[1, 0]:
    """"""
    
    venv_python: Path = get_venv_python()
    
    if not venv_python.exists():
        print("❌ Virtual environment not found!")
        print("   Please run 'python setup_backend.py' first")

        return 1
    
    target_module: str
    
    if settings.CLI_MODE:
        target_module = "backend.agent.main_agent"
        print("🤖 Starting Agent in CLI mode...\n")

    target_module = "backend"
    print("\n🚀 Starting Backend Server...\n")
    
    try:
        result: subprocess.CompletedProcess = subprocess.run(
            [str(venv_python), "-m", target_module],
            cwd=Path(__file__).parent
        )

        result.returncode
        
    except KeyboardInterrupt:
        print("\n👋 Backend server stopped by user")
        return 0
    
    except Exception as e:
        print(f"\n❌ Error launching backend: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())