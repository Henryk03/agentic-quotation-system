
import sys
import shutil
import platform
import subprocess
from pathlib import Path
from typing import Literal


MIN_PY = (3, 13)
MAX_PY = (3, 14)


def clean_cache() -> bool:
    """"""

    print("🧹 Cleaning cache...", end=" ", flush=True)

    try:
        count = 0

        for path in Path(".").rglob("__pycache__"):
            if path.is_dir():
                shutil.rmtree(path)
                count += 1
        
        print(f"✅")
        return True
        
    except Exception as e:
        print(f"❌ Error during cache cleanup: {e}")
        return False


def check_python_version() -> bool:
    """"""

    v = sys.version_info

    if not (MIN_PY <= (v.major, v.minor) < MAX_PY):
        print(
            f"❌ Python {v.major}.{v.minor} not supported."
            "\n"
            f"   Required: >= {MIN_PY[0]}.{MIN_PY[1]} and < {MAX_PY[0]}.{MAX_PY[1]}"
        )

        return False

    print(f"✅ Python {v.major}.{v.minor} OK")
    return True


def run_command(
        cmd: list[str],
        description: str,
        silent: bool = True
    ) -> bool:
    """"""

    print(f"{description}...", end=" ", flush=True)

    try:
        stdout_dest = subprocess.DEVNULL if silent else None
        stderr_dest = subprocess.DEVNULL if silent else None

        subprocess.run(
            cmd,
            check=True,
            stdout=stdout_dest,
            stderr=stderr_dest
        )

        print(f"✅")
        return True
    
    except subprocess.CalledProcessError as e:
        print(f"❌ Error during {description}: {e}")
        return False


def get_venv_python() -> Path:
    """"""

    venv_path = Path(".venv")

    if platform.system() == "Windows":
        return venv_path / "Scripts" / "python.exe"
    
    return venv_path / "bin" / "python"


def prompt(
        question: str,
        default: str | None = None,
        secret: bool = False
    ) -> str | None:
    """Prompt user for input with optional default value."""

    if default:
        question_text = f"{question} [{default}]: "

    else:
        question_text = f"{question}: "
    
    if secret:
        import getpass
        value = getpass.getpass(question_text)

    else:
        value = input(question_text).strip()
    
    return value if value else default


def create_env_file_interactive() -> bool:
    """"""

    env_file: Path = Path(".env")
    
    if env_file.exists():
        print()
        overwrite = input(
            "⚠️  .env file already exists. Overwrite? (y/N): "
        ).lower()

        if overwrite not in ["", "y", "yes"]:
            print("✅ Keeping existing .env file")
            return True
    
    print("\n" + "="*60)
    print("📝 Environment Configuration")
    print("="*60)
    print("\nPress Enter to use [default] values\n")
    
    config = {}
    
    print("\n🌐 Server Connection")
    host = prompt("Server host", default="0.0.0.0")
    config["SERVER"] = host
    port = prompt("Server port", default="8080")
    config["PORT"] = port

    print("\n🎈 Streamlit Configuration")
    streamlit_host = prompt("Streamlit host", default="127.0.0.1")
    config["STREAMLIT_HOST"] = streamlit_host 
    streamlit_port = prompt("Streamlit port", default="8501")
    config["STREAMLIT_PORT"] = streamlit_port
    
    print(f"\n💾 Writing configuration to .env...")
    
    env_content = (
        "# Frontend Environment Variables\n"
        "\n"
        "# Server Connection\n"
        f"HOST={config["HOST"]}\n"
        f"PORT={config["PORT"]}\n"
        "\n"
        "# Streamlit Configuration\n"
        f"STREAMLIT_HOST={config['STREAMLIT_HOST']}\n"
        f"STREAMLIT_PORT={config['STREAMLIT_PORT']}\n"
    )
    
    env_file.write_text(env_content)
    print("✅ .env file created successfully")
    
    return True


def create_env_file_from_template() -> bool:
    """"""

    env_file = Path(".env")
    env_example = Path(".env.example")
    
    default_content = (
        "# Frontend Environment Variables\n"
        "\n"
        "# Server Connection\n"
        "HOST=0.0.0.0\n"
        "PORT=8080\n"
        "\n"
        "# Streamlit Configuration\n"
        "STREAMLIT_HOST=127.0.0.1\n"
        "STREAMLIT_PORT=8501\n"
    )

    if env_file.exists():
        print(f"\n✅ {env_file.name} file already exists.")

        return True
    
    try:
        if env_example.exists():
            shutil.copy(env_example, env_file)
            print(f"✅ {env_file.name} created from {env_example.name}")

        else:
            env_file.write_text(default_content)
            print(f"\n✅ {env_file.name} template created from scratch")
        
        print("👉 Edit .env to set your configuration before running the app")
        return True

    except Exception as e:
        print(f"❌ Error creating .env file: {e}")
        return False



def main() -> Literal[1, 0]:
    """"""

    print("\n🔧 Setting up frontend environment...\n")

    venv_existed: bool = False


    # initial cleanup
    if not clean_cache():
        return 1


    # 0. Check Pyhton version
    if not check_python_version():
        return 1


    # 1. Create venv
    venv_path: Path = Path(".venv")

    if venv_path.exists():
        overwrite = input(
            "⚠️  Virtual environment already exists.\n"
            "    Recreate it? (y/N): "
        ).lower()

        if overwrite in ("y", "yes"):
            print("🗑️ Removing existing virtual environment...")
            shutil.rmtree(venv_path)

        else:
            venv_existed = True
            print("✅ Keeping existing virtual environment")

    if not venv_path.exists():
        if not run_command(
            [sys.executable, "-m", "venv", ".venv"],
            "📁 Creating virtual environment"
        ):
            return 1
    
    venv_python: Path = get_venv_python()
    

    if not venv_existed:
        # 2. Upgrade pip
        if not run_command(
            [str(venv_python), "-m", "pip", "install", "--upgrade", "pip"], 
            "📦 Pip upgrade"
        ):

            return 1
        

        # 3. Install package in editable mode
        if not run_command(
            [str(venv_python), "-m", "pip", "install", "-e", "."], 
            "📦 Package installation (this may take a while)"
        ):

            return 1
    

    # 5. Configure .env
    print("\n" + "="*60)
    configure_mode = input("Configure .env interactively? (Y/n): ").lower()
    print("="*60)
    
    if configure_mode in ["", "y", "yes"]:
        if not create_env_file_interactive():
            return 1
        
    else:
        if not create_env_file_from_template():
            return 1
 
    print("\n" + "="*60)
    print("✅ Setup complete!")
    print("="*60)
    print("\n🚀 To start the backend, run: python launch_backend.py\n")

    print(
        "⚠️  Make sure to have Google Chrome installed in your system\n"
        "   before running the app.\n"
    )
    
    return 0


if __name__ == "__main__":
    sys.exit(main())