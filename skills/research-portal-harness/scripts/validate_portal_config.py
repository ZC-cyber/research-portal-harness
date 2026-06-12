#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from urllib.parse import urlparse


REQUIRED_FIELDS = ["id", "name", "allowed_domains", "start_urls", "manual_login"]


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def host_allowed(url: str, allowed_domains: list[str]) -> bool:
    host = urlparse(url).hostname or ""
    return any(host == domain or host.endswith(f".{domain}") for domain in allowed_domains)


def validate_broker(broker: dict) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    broker_id = broker.get("id", "<missing id>")
    for field in REQUIRED_FIELDS:
        if field not in broker:
            errors.append(f"{broker_id}: missing required field {field}")

    allowed_domains = broker.get("allowed_domains", [])
    start_urls = broker.get("start_urls", [])
    if not isinstance(allowed_domains, list):
        errors.append(f"{broker_id}: allowed_domains must be a list")
        allowed_domains = []
    if not isinstance(start_urls, list):
        errors.append(f"{broker_id}: start_urls must be a list")
        start_urls = []

    if broker.get("manual_login") is not True:
        errors.append(f"{broker_id}: manual_login should be true for authenticated research portals")

    if broker.get("headless") is True:
        errors.append(f"{broker_id}: headless should be false for login and first validation")

    for url in start_urls:
        parsed = urlparse(url)
        if parsed.scheme not in {"https", "http"} or not parsed.hostname:
            errors.append(f"{broker_id}: invalid start URL {url}")
            continue
        if allowed_domains and not host_allowed(url, allowed_domains):
            errors.append(f"{broker_id}: start URL host is not in allowed_domains: {url}")

    risky_keys = {"password", "passwd", "secret", "token", "cookie", "cookies", "session"}
    for key, value in broker.items():
        if key.lower() in risky_keys and value:
            errors.append(f"{broker_id}: do not store {key} in portal config")

    if not broker.get("auth_success_url_patterns") and not broker.get("auth_success_selectors"):
        warnings.append(f"{broker_id}: add an auth success URL pattern or selector before unattended runs")

    return errors, warnings


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a research portal broker config.")
    parser.add_argument("config", type=Path, help="Path to config/brokers.json.")
    parser.add_argument("--broker", help="Validate only one broker id.")
    args = parser.parse_args()

    config = load_json(args.config)
    brokers = config.get("brokers", [])
    if args.broker:
        brokers = [broker for broker in brokers if broker.get("id") == args.broker]
        if not brokers:
            print(f"No broker found with id: {args.broker}")
            return 1

    all_errors: list[str] = []
    all_warnings: list[str] = []
    for broker in brokers:
        errors, warnings = validate_broker(broker)
        all_errors.extend(errors)
        all_warnings.extend(warnings)

    if all_warnings:
        print("Portal config validation warnings:")
        for warning in all_warnings:
            print(f"- {warning}")

    if all_errors:
        print("\nPortal config validation failed:")
        for error in all_errors:
            print(f"- {error}")
        return 1

    print("Portal config validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
