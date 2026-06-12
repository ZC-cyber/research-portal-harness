from __future__ import annotations

from pathlib import Path

from .common import now_iso, write_json


ACK_PATH = Path("data/state/safety_ack.json")


def safety_ack_path(root: Path) -> Path:
    return root / ACK_PATH


def has_safety_ack(root: Path) -> bool:
    return safety_ack_path(root).exists()


def write_safety_ack(root: Path) -> Path:
    path = safety_ack_path(root)
    write_json(
        path,
        {
            "acknowledged_at": now_iso(),
            "terms": [
                "I will only acquire research materials I am entitled to access.",
                "I will not paste passwords, one-time codes, cookies, or session tokens into chat.",
                "I will not bypass access controls, CAPTCHA, paywalls, entitlement checks, or rate limits.",
                "I am responsible for following my portal licenses and compliance rules.",
            ],
        },
    )
    return path

