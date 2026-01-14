
import sys
import platform
import subprocess
from pathlib import Path


def get_venv_python():
    """Get the path to Python in venv."""
    venv_path = Path(__file__).parent / ".venv"
    
    if platform.system() == "Windows":
        return venv_path / "Scripts" / "python.exe"
    return venv_path / "bin" / "python"




def main():
    """Launch backend server using venv"""
    
    # Check if venv exists
    venv_python = get_venv_python()
    
    if not venv_python.exists():
        print("❌ Virtual environment not found!")
        print("   Please run 'python setup_backend.py' first")
        return 1
    
    print("🚀 Starting backend server...\n")
    
    try:
        # Execute backend module using venv's Python
        # Questo chiama src/backend/__main__.py
        result = subprocess.run(
            [str(venv_python), "-m", "backend"],
            cwd=Path(__file__).parent
        )
        return result.returncode
        
    except KeyboardInterrupt:
        print("\n\n👋 Backend server stopped by user")
        return 0
    except Exception as e:
        print(f"\n❌ Error launching backend: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())