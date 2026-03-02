
import asyncio
import os
import platform
import subprocess
from pathlib import Path

from playwright.async_api import Page, Playwright


BACKEND_ROOT: Path = Path(__file__).resolve().parents[4]
USER_DATA_DIR: Path = BACKEND_ROOT / ".automation_profile"

USER_DATA_DIR.mkdir(0o700, exist_ok = True)


def launch_chrome_os(
        headless: bool
    ) -> None:
    """
    Launch a Chrome-compatible browser with remote debugging enabled.

    The function detects the current operating system and attempts
    to start a Chrome (or Chromium) instance configured with:

    - Remote debugging port 9222
    - A dedicated user data directory
    - Optional headless mode
    - Suppressed first-run and default-browser prompts

    The browser process is started asynchronously using
    `subprocess.Popen` and is not awaited.

    Parameters
    ----------
    headless : bool
        If `True`, launches the browser in headless mode.
        On Windows, GPU acceleration is explicitly disabled
        when headless is enabled.

    Returns
    -------
    None
        The function starts a browser process but does not
        return a handle to it.

    Raises
    ------
    None
        All exceptions are caught internally.

    Notes
    -----
    The function assumes that Chrome or a compatible
    Chromium-based browser is available on the system.
    The remote debugging port is hardcoded to 9222.
    """

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
                        r"%ProgramFiles%\Google\Chrome\Application"
                        r"\chrome.exe"
                    ),
                    os.path.expandvars(
                        r"%ProgramFiles(x86)%\Google\Chrome\Application"
                        r"\chrome.exe"
                    ),
                    os.path.expandvars(
                        r"%LocalAppData%\Google\Chrome\Application"
                        r"\chrome.exe"
                    )
                ]

                chrome_path: str = next(
                    (p for p in paths if os.path.exists(p)), 
                    "chrome.exe"
                )

                full_command = [chrome_path] + args

            case "darwin":
                full_command = (
                    ["open", "-a", "Google Chrome", "--args"] + args
                )
                
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
            stdout = subprocess.DEVNULL, 
            stderr = subprocess.DEVNULL
        )

    except:
        pass


async def init_chrome_page(
        async_playwright: Playwright,
        headless: bool,
    ) -> Page:
    """
    Initialize and return a Playwright page connected to a
    locally launched Chrome instance via CDP.

    The function launches a Chrome process with remote
    debugging enabled, waits briefly for it to become
    available, then connects to it using Playwright's
    `connect_over_cdp` method. A new page is created
    from the first available browser context.

    Parameters
    ----------
    async_playwright : playwright.async_api.Playwright
        Initialized Playwright instance used to connect
        to the running Chrome process.

    headless : bool
        Whether to launch Chrome in headless mode.

    Returns
    -------
    playwright.async_api.Page
        A newly created page within the connected
        browser context.

    Raises
    ------
    playwright.async_api.Error
        Raised if the connection to the CDP endpoint
        fails.

    Notes
    -----
    The function assumes that the remote debugging port
    (9222) is available and not already in use.
    """

    launch_chrome_os(headless = headless)

    await asyncio.sleep(5)

    browser = await async_playwright.chromium.connect_over_cdp(
        "http://127.0.0.1:9222"
    )
    context = browser.contexts[0]

    page = await context.new_page()

    return page