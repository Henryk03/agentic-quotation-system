
import sys
import platform
import subprocess
from pathlib import Path
from typing import Literal


MIN_PY = (3, 13)
MAX_PY = (3, 14)


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


def get_venv_python() -> None:
    """"""

    venv_path = Path(".venv")

    if platform.system() == "Windows":
        return venv_path / "Scripts" / "python.exe"
    
    return venv_path / "bin" / "python"


def prompt(
        question: str,
        default: str = None,
        secret: bool = False
    ) -> str:
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

    env_file = Path(".env")
    
    if env_file.exists():
        print()
        overwrite = input(
            "⚠️  .env file already exists. Overwrite? (y/N): "
        ).lower()

        if overwrite != 'y':
            print("✅ Keeping existing .env file")
            return True
    
    print("\n" + "="*60)
    print("📝 Environment Configuration")
    print("="*60)
    print("\nPress Enter to use [default] values\n")
    
    config = {}
    
    print("🛠️  Development cofiguration")
    cli_mode = prompt("Enable CLI mode? (true/false)", default="true")
    config['CLI_MODE'] = cli_mode.lower()
    
    log_level = prompt("Log level (DEBUG/INFO/WARNING/ERROR)", default="INFO")
    config['LOG_LEVEL'] = log_level.upper()
    
    print("\n🔑 Google Gemini API Key")
    print("Get your key at: https://makersuite.google.com/app/apikey")
    api_key = prompt("Google API Key", secret=True)
    config['GOOGLE_API_KEY'] = api_key or "your_api_key_here"
    
    print("\n🌐 Server Configuration")
    host = prompt("Server host", default="0.0.0.0")
    config['HOST'] = host
    port = prompt("Server port", default="8080")
    config['PORT'] = port

    print("\n" + "🗄️ Database configuration")
    db_url = prompt("Database URL")
    config['DB_URL'] = db_url or "protocol://user:password@host:port/db_name"

    print("\n🎭 Playwright Configuration")
    headless = prompt("Run browser in headless mode? (true/false)", default="true")
    config['HEADLESS'] = headless.lower()
    
    print(f"\n💾 Writing configuration to .env...")
    
    env_content = (
        "# Backend Environment Variables\n"
        "\n"
        "# Development\n"
        f"CLI_MODE={config['CLI_MODE']}\n"
        f"LOG_LEVEL={config['LOG_LEVEL']}\n"
        "\n"
        "# Google Gemini API\n"
        f"GOOGLE_API_KEY={config['GOOGLE_API_KEY']}\n"
        "\n"
        "# Server Configuration\n"
        f"HOST={config['HOST']}\n"
        f"PORT={config['PORT']}\n"
        "\n"
        "# Database configuration\n"
        f"DATABASE_URL={config['DB_URL']}\n"
        "\n"
        "# Playwright\n"
        f"HEADLESS={config['HEADLESS']}\n"
    )
    
    env_file.write_text(env_content)
    print("✅ .env file created successfully")
    
    if config['GOOGLE_API_KEY'] == "your_api_key_here":
        print("⚠️ Warning: Remember to add your Google API Key to .env!")
    
    return True


def create_env_file_from_template() -> bool:
    """"""

    env_file = Path(".env")
    env_example = Path(".env.example")
    
    default_content = (
        "# Backend Environment Variables\n"
        "\n"
        "# Development\n"
        "CLI_MODE=false\n"
        "LOG_LEVEL=INFO\n"
        "\n"
        "# Google Gemini API\n"
        "GOOGLE_API_KEY=your_api_key_here\n"
        "\n"
        "# Server Configuration\n"
        "HOST=0.0.0.0\n"
        "PORT=8080\n"
        "\n"
        "# Database configuration\n"
        f"DATABASE_URL=protocol://user:password@host:port/db_name\n"
        "\n"
        "# Playwright\n"
        "HEADLESS=true\n"
    )

    if env_file.exists():
        print(f"\n✅ {env_file.name} file already exists.")
        content = env_file.read_text()

        if (
                "your_api_key_here" in content
            ) or (
                "GOOGLE_API_KEY=" not in content
            ):
            print("⚠️  Action required: Update your GOOGLE_API_KEY in the .env file.")

        if (
            "protocol://user:password@host:port/db_name" in content
            ) or (
                "DATABASE_URL=" not in content
            ):
            print("⚠️  Action required: Update the DATABASE_URL in the .env file.")

        return True
    
    try:
        if env_example.exists():
            import shutil
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

    print("\n🔧 Setting up backend environment...\n")


    # 0. Check Pyhton version
    if not check_python_version():
        return 1


    # 1. Create venv
    venv_path = Path(".venv")
    if not venv_path.exists():
        if not run_command(
            [sys.executable, "-m", "venv", ".venv"], 
            "📁 Creating virtual environment"
            ):

            return 1
        
    else:
        print("✅ Virtual environment already exists")
    
    venv_python = get_venv_python()
    

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
    

    # 4. Install Playwright browsers
    if not run_command(
        [str(venv_python), "-m", "playwright", "install", "chromium"],
        "🌐 Playwright browser installation (this may take a minute)"
        ):

        return 1
    

    # 5. Configure .env
    print("\n" + "="*60)
    configure_mode = input("Configure .env interactively? (Y/n): ").lower()
    print("="*60)
    
    if configure_mode in ['', 'y', 'yes']:
        if not create_env_file_interactive():
            return 1
        
    else:
        if not create_env_file_from_template():
            return 1
    
    print("\n" + "="*60)
    print("✅ Setup complete!")
    print("="*60)
    print("\n🚀 To start the backend, run: python launch_backend.py\n")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())