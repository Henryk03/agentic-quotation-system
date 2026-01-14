
import sys
import subprocess
from pathlib import Path

def get_venv_python():
    """Get the path to Python in venv."""
    venv_path = Path(__file__).parent / ".venv"
    
    if sys.platform == "win32":
        return venv_path / "Scripts" / "python.exe"
    return venv_path / "bin" / "python"

def check_python_version():
    """Quick Python version check"""
    version = sys.version_info
    if version.major != 3 or version.minor != 13:
        print("❌ Python 3.13.x is required to run the frontend")
        print(f"   Current: {version.major}.{version.minor}.{version.micro}")
        return False
    return True

def main():
    """Launch frontend using venv"""
    
    # Check Python version
    if not check_python_version():
        return 1
    
    # Check if venv exists
    venv_python = get_venv_python()
    
    if not venv_python.exists():
        print("❌ Virtual environment not found!")
        print("   Please run 'python setup_frontend.py' first")
        return 1
    
    print("🚀 Starting frontend...\n")
    
    try:
        # Execute frontend module using venv's Python
        result = subprocess.run(
            [str(venv_python), "-m", "frontend"],
            cwd=Path(__file__).parent
        )
        return result.returncode
        
    except KeyboardInterrupt:
        print("\n\n👋 Frontend stopped by user")
        return 0
    except Exception as e:
        print(f"\n❌ Error launching frontend: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())