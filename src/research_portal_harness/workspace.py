from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any

from .common import load_json, write_json


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


def default_workspace_config(root: Path) -> dict[str, Any]:
    return {
        "browser_profile_dir": "data/state/browser_profiles",
        "download_manifest": "data/state/manifests/download_manifest.json",
        "headless": False,
        "manual_login_timeout_ms": 300000,
        "manual_login_poll_ms": 2000,
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
                "auth_pending_url_patterns": ["login", "signin", "sso", "mfa"],
                "auth_success_url_patterns": [],
                "auth_success_selectors": [],
                "notes": "Fill official URL and allowed domains after observing the entitled portal.",
            }
            for portal in COMMON_PORTALS
        ],
    }


def default_tasks_config() -> dict[str, Any]:
    return {
        "tasks": [
            {
                "id": "example_research_task",
                "description": "Replace with tickers, companies, sectors, themes, date range, and file types.",
                "tickers": [],
                "company_terms": [],
                "industry_terms": [],
                "file_types": ["pdf", "xlsx", "xlsm"],
                "date_range_days": 730,
                "max_downloads_per_portal": 25,
            }
        ]
    }


def init_workspace(root: Path) -> list[Path]:
    root = root.expanduser().resolve()
    created: list[Path] = []
    for directory in [
        root / "config",
        root / "data" / "raw",
        root / "data" / "indexes",
        root / "data" / "exports",
        root / "data" / "reports",
        root / "data" / "state" / "browser_profiles",
        root / "data" / "state" / "manifests",
        root / "data" / "state" / "search_candidates",
    ]:
        directory.mkdir(parents=True, exist_ok=True)
        created.append(directory)

    brokers_path = root / "config" / "brokers.json"
    if not brokers_path.exists():
        write_json(brokers_path, default_workspace_config(root))
        created.append(brokers_path)

    tasks_path = root / "config" / "tasks.json"
    if not tasks_path.exists():
        write_json(tasks_path, default_tasks_config())
        created.append(tasks_path)

    return created


def load_brokers(root: Path) -> dict[str, Any]:
    return load_json(root / "config" / "brokers.json")


def save_brokers(root: Path, config: dict[str, Any]) -> None:
    write_json(root / "config" / "brokers.json", config)


def load_tasks(root: Path) -> dict[str, Any]:
    return load_json(root / "config" / "tasks.json")


def get_broker(root: Path, broker_id: str) -> dict[str, Any]:
    for broker in load_brokers(root).get("brokers", []):
        if broker.get("id") == broker_id:
            return broker
    raise KeyError(f"Unknown portal: {broker_id}")


def get_task(root: Path, task_id: str) -> dict[str, Any]:
    for task in load_tasks(root).get("tasks", []):
        if task.get("id") == task_id:
            return task
    raise KeyError(f"Unknown task: {task_id}")


def upsert_broker(root: Path, broker: dict[str, Any]) -> None:
    config = load_brokers(root)
    brokers = config.setdefault("brokers", [])
    for index, existing in enumerate(brokers):
        if existing.get("id") == broker["id"]:
            brokers[index] = {**existing, **broker}
            save_brokers(root, config)
            return
    brokers.append(broker)
    save_brokers(root, config)


def copy_example_configs(repo_root: Path, workspace_root: Path) -> None:
    examples = repo_root / "examples"
    config = workspace_root / "config"
    if examples.exists():
        for source in examples.glob("*.json"):
            target = config / source.name.replace(".example", "")
            if not target.exists():
                shutil.copyfile(source, target)

