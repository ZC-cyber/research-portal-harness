from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse, urlunparse


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def append_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def safe_filename(value: str, fallback: str = "download") -> str:
    value = re.sub(r"[\\/:*?\"<>|\r\n\t]+", "_", value).strip(" ._")
    value = re.sub(r"\s+", " ", value)
    if not value:
        value = fallback
    return value[:180]


def redact_url(value: str) -> str:
    parsed = urlparse(value)
    return urlunparse((parsed.scheme, parsed.netloc, parsed.path, "", "", ""))


def host_matches(host: str, domain: str) -> bool:
    return host == domain or host.endswith(f".{domain}")


def url_allowed(url: str, allowed_domains: list[str]) -> bool:
    host = urlparse(url).hostname or ""
    return bool(host and any(host_matches(host, domain) for domain in allowed_domains))


def matches_any(value: str, patterns: list[str]) -> bool:
    return any(re.search(pattern, value, flags=re.IGNORECASE) for pattern in patterns)

