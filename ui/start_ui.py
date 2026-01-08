
import os
import subprocess
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
os.environ["PYTHONPATH"] = str(PROJECT_ROOT)

UI_SCRIPT = PROJECT_ROOT / "ui" / "agent_ui.py"

subprocess.run(["streamlit", "run", str(UI_SCRIPT)])