
import sys
import subprocess
from pathlib import Path
from typing import Literal

from frontend.config import settings



def main() -> Literal[0, 1]:
    """"""
    
    ui_file: Path = Path(__file__).parent / "ui" / "agent_ui.py"
    
    if not ui_file.exists():
        print(f"❌ UI file not found: {ui_file}")
        return 1
    
    print("\n🚀 Starting Streamlit frontend...\n")
    
    try:
        subprocess.run(
            [
                sys.executable, "-m", "streamlit", "run", str(ui_file),
                "--server.port", str(settings.STREAMLIT_PORT),
                "--server.address", str(settings.STREAMLIT_HOST)
            ], 
            check=True)

    except KeyboardInterrupt:
        print("\n\n👋 Shutdown requested")
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