
import subprocess
import sys
from pathlib import Path
from typing import Literal

from frontend.config import settings


def main() -> Literal[0, 1]:
    """
    Launch the Streamlit frontend application.

    The function verifies that the UI entrypoint file exists and then
    starts Streamlit as a subprocess using the configured host and port.

    Returns
    -------
    Literal[0, 1]
        Exit status code:
        - 0 if the application exits normally.
        - 1 if an error occurs (missing UI file, Streamlit not installed,
          or subprocess failure).
    """

    ui_file: Path = Path(__file__).parent / "ui" / "agent_ui.py"

    if not ui_file.exists():
        print(f"UI file not found: {ui_file}")
        return 1

    print("\nstarting streamlit frontend...\n")

    command: list[str] = [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        str(ui_file),
        "--server.port",
        str(settings.STREAMLIT_PORT),
        "--server.address",
        str(settings.STREAMLIT_HOST),
    ]

    try:
        subprocess.run(command, check = True)

    except KeyboardInterrupt:
        print("\nshutdown requested")
        return 0

    except ModuleNotFoundError:
        print(
            "streamlit is not installed. install frontend "
            "dependencies first."
        )
        return 1

    except subprocess.CalledProcessError as exc:
        print(
            f"streamlit exited with error code {exc.returncode}"
        )        
        return 1

    except Exception as exc:
        print(
            f"unexpected error while launching frontend: {exc}"
        )
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())