from __future__ import annotations

from pathlib import Path

from research_portal_harness.indexer import index_downloads, status
from research_portal_harness.manifest import load_manifest, record_download, save_manifest
from research_portal_harness.workspace import get_broker, get_task, init_workspace, load_brokers


def test_init_workspace_creates_configs(tmp_path: Path) -> None:
    created = init_workspace(tmp_path)

    assert tmp_path / "config" / "brokers.json" in created
    assert tmp_path / "config" / "tasks.json" in created
    assert (tmp_path / "data" / "state" / "browser_profiles").is_dir()
    assert get_broker(tmp_path, "bernstein_research")["manual_login"] is True
    assert get_task(tmp_path, "example_research_task")["file_types"] == ["pdf", "xlsx", "xlsm"]


def test_manifest_dedupes_by_hash_and_url(tmp_path: Path) -> None:
    init_workspace(tmp_path)
    broker = get_broker(tmp_path, "bernstein_research")
    path = tmp_path / "data" / "raw" / "task" / "broker" / "report.pdf"
    path.parent.mkdir(parents=True)
    path.write_bytes(b"same content")
    manifest = {"downloads": {}}

    added, first = record_download(manifest, "https://example.com/report.pdf", path, broker, "Report", "download")
    assert added is True
    assert first["sha256"]

    duplicate = tmp_path / "data" / "raw" / "task" / "broker" / "duplicate.pdf"
    duplicate.write_bytes(b"same content")
    added, second = record_download(manifest, "https://example.com/other.pdf", duplicate, broker, "Duplicate", "download")
    assert added is False
    assert second["sha256"] == first["sha256"]
    assert not duplicate.exists()


def test_index_and_status_from_manifest(tmp_path: Path) -> None:
    init_workspace(tmp_path)
    config = load_brokers(tmp_path)
    broker = get_broker(tmp_path, "bernstein_research")
    path = tmp_path / "data" / "raw" / "example_research_task" / broker["id"] / "data.csv"
    path.parent.mkdir(parents=True)
    path.write_text("ticker,price\nABC,12.3\n", encoding="utf-8")
    manifest = load_manifest(tmp_path / config["download_manifest"])
    record_download(manifest, "https://example.com/data.csv", path, broker, "Data", "download")
    save_manifest(tmp_path / config["download_manifest"], manifest)

    index_path = index_downloads(tmp_path, "example_research_task")
    report = status(tmp_path, "example_research_task")

    assert index_path.exists()
    assert report["downloaded_files"] == 1
    assert report["indexed_documents"] == 1
    assert report["by_broker"] == {"bernstein_research": 1}

