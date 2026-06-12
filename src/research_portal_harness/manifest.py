from __future__ import annotations

from pathlib import Path
from typing import Any

from .common import load_json, now_iso, sha256_file, sha256_text, write_json


def manifest_path(root: Path, config: dict[str, Any]) -> Path:
    return root / config.get("download_manifest", "data/state/manifests/download_manifest.json")


def load_manifest(path: Path) -> dict[str, Any]:
    if path.exists():
        return load_json(path)
    return {"downloads": {}, "updated_at": None}


def save_manifest(path: Path, manifest: dict[str, Any]) -> None:
    manifest["updated_at"] = now_iso()
    write_json(path, manifest)


def record_download(
    manifest: dict[str, Any],
    source_url: str,
    local_path: Path,
    broker: dict[str, Any],
    title: str,
    kind: str,
    metadata: dict[str, Any] | None = None,
) -> tuple[bool, dict[str, Any]]:
    digest = sha256_file(local_path)
    url_key = f"url:{sha256_text(source_url)}"
    digest_key = f"sha256:{digest}"
    known = manifest.setdefault("downloads", {})
    if digest_key in known or url_key in known:
        existing = known.get(digest_key) or known[url_key]
        local_path.unlink(missing_ok=True)
        return False, existing

    record = {
        "broker_id": broker["id"],
        "broker": broker["name"],
        "title": title,
        "kind": kind,
        "source_url": source_url,
        "local_path": str(local_path.resolve()),
        "sha256": digest,
        "size_bytes": local_path.stat().st_size,
        "downloaded_at": now_iso(),
        "metadata": metadata or {},
    }
    known[digest_key] = record
    known[url_key] = record
    return True, record


def unique_records(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    rows: list[dict[str, Any]] = []
    for record in manifest.get("downloads", {}).values():
        digest = record.get("sha256") or record.get("source_url")
        if digest in seen:
            continue
        seen.add(digest)
        rows.append(record)
    return rows

