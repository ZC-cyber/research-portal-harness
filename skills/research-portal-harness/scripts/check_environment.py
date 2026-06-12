#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import argparse
import shutil
import subprocess
import sys


RUNTIME_MODULES = [
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
    parser = argparse.ArgumentParser(description="Check local prerequisites for Research Portal Harness.")
    parser.add_argument(
        "--strict-runtime",
        action="store_true",
        help="Fail when optional Playwright/PDF/Excel runtime modules are missing.",
    )
    args = parser.parse_args()

    failures: list[str] = []
    warnings: list[str] = []
    print(f"python: {sys.version.split()[0]} ({sys.executable})")

    if sys.version_info < (3, 9):
        failures.append("Python 3.9+ is required for the harness helper scripts.")
    elif sys.version_info < (3, 11):
        warnings.append("Python 3.11+ is recommended for full acquisition workspaces.")

    pip = shutil.which("pip3") or shutil.which("pip")
    print(f"pip: {pip or 'not found'}")
    if not pip:
        failures.append("pip is required.")

    for module in RUNTIME_MODULES:
        ok = module_status(module)
        print(f"module {module}: {'ok' if ok else 'missing'}")
        if not ok and args.strict_runtime:
            failures.append(f"Missing Python module: {module}")
        elif not ok:
            warnings.append(f"Missing optional runtime module: {module}")

    if module_status("playwright"):
        result = subprocess.run(
            [sys.executable, "-m", "playwright", "--version"],
            check=False,
            capture_output=True,
            text=True,
        )
        version = (result.stdout or result.stderr).strip()
        print(f"playwright cli: {version or 'not available'}")

    if warnings:
        print("\nEnvironment check warnings:")
        for warning in warnings:
            print(f"- {warning}")
        if not args.strict_runtime:
            print("- Run again with --strict-runtime before browser/PDF/Excel acquisition.")

    if failures:
        print("\nEnvironment check failed:")
        for failure in failures:
            print(f"- {failure}")
        if shutil.which("uv"):
            print("\nIf your default python is too old, run:")
            print("uv python install 3.11")
            print("uv venv --python 3.11")
            print("source .venv/bin/activate")
        print("\nIf your acquisition workspace has a pyproject.toml, run from that workspace:")
        print("python3 -m pip install -e \".[dev]\"")
        print("Then install a browser: python3 -m playwright install chromium")
        return 1

    if args.strict_runtime:
        print("\nStrict runtime environment check passed.")
    else:
        print("\nBaseline environment check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
