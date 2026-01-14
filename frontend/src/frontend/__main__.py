"""Entry point for frontend Streamlit app"""

import sys
import subprocess
from pathlib import Path

def main():
    """Launch Streamlit app"""
    
    # Path to the main UI file
    ui_file = Path(__file__).parent / "ui" / "agent_ui.py"
    
    if not ui_file.exists():
        print(f"❌ UI file not found: {ui_file}")
        return 1
    
    print("🚀 Starting Streamlit frontend...\n")
    
    try:
        # Use python -m streamlit instead of streamlit command
        # This ensures proper PYTHONPATH
        subprocess.run([
            sys.executable, "-m", "streamlit", "run",
            str(ui_file),
            "--server.port", "8501",
            "--server.address", "127.0.0.1"
        ], check=True)
    except KeyboardInterrupt:
        print("\n\n👋 Frontend stopped by user")
        return 0
    except ModuleNotFoundError:
        print("❌ Streamlit not installed. Run 'python setup_frontend.py' first.")
        return 1
    except Exception as e:
        print(f"❌ Error launching frontend: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())