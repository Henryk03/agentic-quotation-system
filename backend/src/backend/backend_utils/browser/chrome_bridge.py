
import os
import asyncio
import subprocess
import platform
from pathlib import Path

from playwright.async_api import (
    Playwright,
    Page
)


BACKEND_ROOT: Path = Path(__file__).resolve().parents[4]
USER_DATA_DIR: Path = BACKEND_ROOT / ".automation_profile"

USER_DATA_DIR.mkdir(0o700, exist_ok = True)

SCREEN_WIDTH = 1440
SCREEN_HEIGHT = 900


def launch_chrome_os(
        headless: bool
    ) -> None:
    """"""

    system: str = platform.system().lower()
    full_command: list[str] = []
    headless_options: list[str] = []

    if headless:
        headless_options = [
            "--headless",
            f"{"--disable-gpu" if system == "windows" else ""}"
        ]

    args: list[str] = [
        f"--remote-debugging-port=9222",
        f"--user-data-dir={USER_DATA_DIR}",
        "--no-first-run",
        "--no-default-browser-check",
        *headless_options,
        "https://google.com"
    ]

    try:
        match system:
            case "windows":
                paths: list[str] = [
                    os.path.expandvars(
                        r"%ProgramFiles%\Google\Chrome\Application\chrome.exe"
                    ),
                    os.path.expandvars(
                        r"%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe"
                    ),
                    os.path.expandvars(
                        r"%LocalAppData%\Google\Chrome\Application\chrome.exe"
                    )
                ]

                chrome_path: str = next(
                    (p for p in paths if os.path.exists(p)), 
                    "chrome.exe"
                )
                full_command = [chrome_path] + args

            case "darwin":
                full_command = ["open", "-a", "Google Chrome", "--args"] + args
                
            case "linux":
                paths: list[str] = [
                    "google-chrome", 
                    "google-chrome-stable", 
                    "chromium-browser", 
                    "chromium"
                ]

                chrome_path: str = next(
                    (p for p in paths if subprocess.run(
                        ["which", p], 
                        capture_output=True
                    ).returncode == 0), 
                    "google-chrome"
                )
                full_command = [chrome_path] + args

        subprocess.Popen(
            full_command, 
            stdout=subprocess.DEVNULL, 
            stderr=subprocess.DEVNULL
        )

    except Exception as e:
        print(f"Errore durante il lancio di Chrome: {e}")


async def init_chrome_page(
        async_playwright: Playwright,
        headless: bool,
    ) -> Page:
    """"""

    launch_chrome_os(headless = headless)

    await asyncio.sleep(5)

    browser = await async_playwright.chromium.connect_over_cdp(
        "http://127.0.0.1:9222"
    )
    context = browser.contexts[0]

    page = await context.new_page()

    return page