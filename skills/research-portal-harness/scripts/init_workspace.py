#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path


COMMON_PORTALS = [
    "goldman_sachs_marquee",
    "morgan_stanley_matrix",
    "jpm_markets",
    "ubs_neo",
    "citi_velocity",
    "bofa_baml_research",
    "bernstein_research",
    "barclays_live",
    "jefferies_research",
    "evercore_isi",
    "wolfe_research",
    "melius_research",
    "capital_iq_pro",
    "factset",
]


def write_json_if_missing(path: Path, data: object) -> None:
    if path.exists():
        print(f"exists: {path}")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    print(f"created: {path}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Initialize a local research portal harness workspace.")
    parser.add_argument("workspace", type=Path, help="Workspace directory to create or update.")
    args = parser.parse_args()

    root = args.workspace.expanduser().resolve()
    for directory in [
        root / "config",
        root / "data" / "raw",
        root / "data" / "indexes",
        root / "data" / "exports",
        root / "data" / "reports",
        root / "data" / "state" / "browser_profiles",
        root / "data" / "state" / "manifests",
    ]:
        directory.mkdir(parents=True, exist_ok=True)
        print(f"dir: {directory}")

    brokers = {
        "browser_profile_dir": str(root / "data" / "state" / "browser_profiles"),
        "download_manifest": "data/state/manifests/download_manifest.json",
        "headless": False,
        "manual_login_timeout_ms": 300000,
        "max_downloads_per_run": 50,
        "file_extensions": [".pdf", ".xls", ".xlsx", ".xlsm", ".csv", ".zip", ".json"],
        "brokers": [
            {
                "id": portal,
                "name": portal.replace("_", " ").title(),
                "allowed_domains": [],
                "start_urls": [],
                "manual_login": True,
                "enabled": False,
                "notes": "Fill official URL and allowed domains after observing the user's entitled portal.",
            }
            for portal in COMMON_PORTALS
        ],
    }
    tasks = {
        "tasks": [
            {
                "id": "example_research_task",
                "description": "Replace with tickers, companies, sectors, themes, date range, and file types.",
                "tickers": [],
                "company_terms": [],
                "industry_terms": [],
                "file_types": ["pdf", "xlsx", "xlsm"],
                "date_range_days": 730,
            }
        ]
    }

    write_json_if_missing(root / "config" / "brokers.json", brokers)
    write_json_if_missing(root / "config" / "tasks.json", tasks)
    print("\nNext: fill one portal recipe, then run login-only in a visible browser.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

