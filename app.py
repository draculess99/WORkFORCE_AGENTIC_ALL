"""
One-click local launcher for Workforce AI Suite.

Usage:
    python app.py

What it does:
    1. Moves into this project folder.
    2. Creates a local .venv if needed.
    3. Installs/updates packages from requirements.txt when requirements change.
    4. Launches the Streamlit multipage app.
    5. Opens the browser automatically.

Notes:
    - This is for local testing on Windows/Mac/Linux.
    - On Railway, keep using railway.toml instead of this file.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import subprocess
import sys
import threading
import time
import venv
import webbrowser
from pathlib import Path

APP_NAME = "Workforce AI Suite"
PROJECT_ROOT = Path(__file__).resolve().parent
REQUIREMENTS_FILE = PROJECT_ROOT / "requirements.txt"
STREAMLIT_ENTRY = PROJECT_ROOT / "streamlit_app.py"
VENV_DIR = PROJECT_ROOT / ".venv"
MARKER_FILE = VENV_DIR / ".workforce_ai_suite_install.json"
DEFAULT_PORT = "8501"
LAUNCHER_VERSION = "1.0"


def print_header() -> None:
    print("\n" + "=" * 72)
    print(f" {APP_NAME} local launcher")
    print("=" * 72)


def require_project_files() -> None:
    missing = []
    if not REQUIREMENTS_FILE.exists():
        missing.append("requirements.txt")
    if not STREAMLIT_ENTRY.exists():
        missing.append("streamlit_app.py")

    if missing:
        raise FileNotFoundError(
            "Missing required project file(s): " + ", ".join(missing) +
            f"\nMake sure app.py is inside the unzipped {APP_NAME} folder."
        )


def python_version_warning() -> None:
    major, minor = sys.version_info[:2]
    if major != 3 or minor < 10:
        raise RuntimeError(
            f"Python {major}.{minor} detected. Please use Python 3.10+; Python 3.11 is recommended."
        )
    if minor >= 13:
        print(
            "Warning: Python 3.13+ detected. Some ML/agent packages may not have wheels yet. "
            "Python 3.11 is the safest version for this project.\n"
        )


def venv_python_path() -> Path:
    if platform.system().lower().startswith("win"):
        return VENV_DIR / "Scripts" / "python.exe"
    return VENV_DIR / "bin" / "python"


def file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def marker_is_current() -> bool:
    if not MARKER_FILE.exists():
        return False
    try:
        data = json.loads(MARKER_FILE.read_text(encoding="utf-8"))
    except Exception:
        return False

    return (
        data.get("requirements_sha256") == file_sha256(REQUIREMENTS_FILE)
        and data.get("launcher_version") == LAUNCHER_VERSION
        and venv_python_path().exists()
    )


def write_marker() -> None:
    MARKER_FILE.write_text(
        json.dumps(
            {
                "app": APP_NAME,
                "launcher_version": LAUNCHER_VERSION,
                "requirements_sha256": file_sha256(REQUIREMENTS_FILE),
                "python": str(venv_python_path()),
                "installed_at_epoch": int(time.time()),
            },
            indent=2,
        ),
        encoding="utf-8",
    )


def run_checked(command: list[str], *, cwd: Path = PROJECT_ROOT) -> None:
    printable = " ".join(f'"{p}"' if " " in p else p for p in command)
    print(f"\n> {printable}")
    subprocess.check_call(command, cwd=str(cwd))


def ensure_virtualenv(force_reinstall: bool = False) -> Path:
    py = venv_python_path()

    if not py.exists():
        print(f"Creating local virtual environment: {VENV_DIR}")
        venv.create(str(VENV_DIR), with_pip=True, clear=False)

    if force_reinstall or not marker_is_current():
        print("Installing/updating Python packages from requirements.txt...")
        run_checked([str(py), "-m", "pip", "install", "--upgrade", "pip", "setuptools", "wheel"])
        run_checked([str(py), "-m", "pip", "install", "-r", str(REQUIREMENTS_FILE)])
        write_marker()
    else:
        print("Packages already installed for the current requirements.txt. Skipping install.")

    return py


def open_browser_later(url: str, delay_seconds: float = 3.0) -> None:
    def _open() -> None:
        time.sleep(delay_seconds)
        print(f"\nOpening browser: {url}\n")
        webbrowser.open(url, new=2)

    thread = threading.Thread(target=_open, daemon=True)
    thread.start()


def launch_streamlit(py: Path, port: str, headless: bool) -> int:
    url = f"http://localhost:{port}"
    if not headless:
        open_browser_later(url)

    command = [
        str(py),
        "-m",
        "streamlit",
        "run",
        str(STREAMLIT_ENTRY),
        "--server.port",
        port,
        "--server.address",
        "localhost",
        "--browser.gatherUsageStats",
        "false",
    ]

    if headless:
        command.extend(["--server.headless", "true"])
    else:
        command.extend(["--server.headless", "false"])

    print("\nStarting Streamlit...")
    print(f"Local URL: {url}")
    print("Press Ctrl+C in this terminal to stop the app.\n")

    process = subprocess.Popen(command, cwd=str(PROJECT_ROOT))
    try:
        return process.wait()
    except KeyboardInterrupt:
        print("\nStopping Streamlit...")
        process.terminate()
        try:
            return process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
            return process.wait()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=f"Launch {APP_NAME} locally.")
    parser.add_argument(
        "--port",
        default=os.environ.get("PORT", DEFAULT_PORT),
        help=f"Local Streamlit port. Default: {DEFAULT_PORT}",
    )
    parser.add_argument(
        "--reinstall",
        action="store_true",
        help="Force reinstall packages from requirements.txt.",
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Do not automatically open the browser.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    os.chdir(PROJECT_ROOT)

    print_header()
    python_version_warning()
    require_project_files()

    py = ensure_virtualenv(force_reinstall=args.reinstall)
    return launch_streamlit(py, port=str(args.port), headless=args.headless)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except subprocess.CalledProcessError as exc:
        print("\nSetup failed while running this command:")
        print(" ".join(exc.cmd if isinstance(exc.cmd, list) else [str(exc.cmd)]))
        print("\nCommon fixes:")
        print("  - Install Python 3.11 from python.org")
        print("  - Re-run: python app.py --reinstall")
        print("  - Make sure your internet connection is working for pip install")
        raise SystemExit(exc.returncode)
    except Exception as exc:
        print(f"\nLauncher error: {exc}")
        raise SystemExit(1)
