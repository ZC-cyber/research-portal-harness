from __future__ import annotations

from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from .common import url_allowed
from .safety import has_safety_ack
from .workspace import load_brokers


def diagnose_portal(root: Path, broker: dict[str, Any]) -> list[dict[str, str]]:
    checks: list[dict[str, str]] = []

    def add(status: str, check: str, detail: str) -> None:
        checks.append({"status": status, "check": check, "detail": detail})

    if has_safety_ack(root):
        add("ok", "safety_ack", "First-run safety acknowledgement exists.")
    else:
        add("warn", "safety_ack", "Run `rph safety-ack` before real portal acquisition.")

    allowed_domains = broker.get("allowed_domains", [])
    if allowed_domains:
        add("ok", "allowed_domains", ", ".join(allowed_domains))
    else:
        add("fail", "allowed_domains", "No allowed domains configured.")

    start_urls = broker.get("start_urls", [])
    if not start_urls:
        add("fail", "start_urls", "No start URL configured.")
    for url in start_urls:
        parsed = urlparse(url)
        if parsed.scheme not in {"http", "https"} or not parsed.hostname:
            add("fail", "start_url", f"Invalid URL: {url}")
        elif allowed_domains and not url_allowed(url, allowed_domains):
            add("fail", "start_url", f"Outside allowed domains: {url}")
        else:
            add("ok", "start_url", url)

    if broker.get("manual_login", True):
        add("ok", "manual_login", "Visible browser login is enabled.")
    else:
        add("warn", "manual_login", "Manual login is disabled; verify this is intended.")

    if broker.get("auth_success_url_patterns") or broker.get("auth_success_selectors"):
        add("ok", "auth_success", "Success indicators configured.")
    else:
        add("warn", "auth_success", "Add URL patterns or selectors before unattended runs.")

    if broker.get("download_selectors"):
        add("ok", "download_selectors", f"{len(broker['download_selectors'])} selectors configured.")
    else:
        add("warn", "download_selectors", "Using generic download selectors only.")

    return checks


def diagnose_workspace(root: Path, broker_id: str | None = None) -> dict[str, Any]:
    config = load_brokers(root)
    brokers = config.get("brokers", [])
    if broker_id:
        brokers = [broker for broker in brokers if broker.get("id") == broker_id]
        if not brokers:
            raise KeyError(f"Unknown portal: {broker_id}")
    return {
        "workspace": str(root),
        "portals": {
            broker["id"]: diagnose_portal(root, broker)
            for broker in brokers
        },
    }

