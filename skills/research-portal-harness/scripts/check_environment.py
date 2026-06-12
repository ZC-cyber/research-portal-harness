#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import shutil
import subprocess
import sys


REQUIRED_MODULES = [
    "playwright",
    "bs4",
    "fitz",
    "openpyxl",
    "pandas",
    "rich",
    "typer",
    "yaml",
]


def module_status(name: str) -> bool:
    return importlib.util.find_spec(name) is not None


def main() -> int:
    failures: list[str] = []
    print(f"python: {sys.version.split()[0]} ({sys.executable})")

    if sys.version_info < (3, 11):
        failures.append("Python 3.11+ is required.")

    pip = shutil.which("pip3") or shutil.which("pip")
    print(f"pip: {pip or 'not found'}")
    if not pip:
        failures.append("pip is required.")

    for module in REQUIRED_MODULES:
        ok = module_status(module)
        print(f"module {module}: {'ok' if ok else 'missing'}")
        if not ok:
            failures.append(f"Missing Python module: {module}")

    if module_status("playwright"):
        result = subprocess.run(
            [sys.executable, "-m", "playwright", "--version"],
            check=False,
            capture_output=True,
            text=True,
        )
        version = (result.stdout or result.stderr).strip()
        print(f"playwright cli: {version or 'not available'}")

    if failures:
        print("\nEnvironment check failed:")
        for failure in failures:
            print(f"- {failure}")
        if shutil.which("uv"):
            print("\nIf your default python is too old, run:")
            print("uv python install 3.11")
            print("uv venv --python 3.11")
            print("source .venv/bin/activate")
        print("\nFor this repo, run: python3 -m pip install -e \".[dev]\"")
        print("Then install a browser: python3 -m playwright install chromium")
        return 1

    print("\nEnvironment check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
