from __future__ import annotations

from pathlib import Path

from research_portal_harness.indexer import index_downloads, status
from research_portal_harness.mock_portal import run_mock_portal
from research_portal_harness.portal import discover, fetch
from research_portal_harness.safety import write_safety_ack
from research_portal_harness.workspace import get_broker, get_task, init_workspace, load_brokers, save_brokers, upsert_broker


def test_mock_portal_end_to_end(tmp_path: Path) -> None:
    init_workspace(tmp_path)
    write_safety_ack(tmp_path)
    with run_mock_portal() as base_url:
        broker = {
            "id": "mock_research",
            "name": "Mock Research Portal",
            "allowed_domains": ["127.0.0.1"],
            "start_urls": [f"{base_url}/research"],
            "manual_login": False,
            "enabled": True,
            "auth_success_url_patterns": ["research"],
            "auth_success_selectors": [],
            "exclude_url_patterns": ["terms"],
            "exclude_title_patterns": ["Terms"],
        }
        upsert_broker(tmp_path, broker)
        broker = get_broker(tmp_path, "mock_research")
        task = get_task(tmp_path, "example_research_task")

        candidates = discover(tmp_path, broker, task, headless=True)
        assert len(candidates) >= 3

        result = fetch(tmp_path, broker, task, max_downloads=10, headless=True)
        assert result.downloaded == 3

    index_path = index_downloads(tmp_path, "example_research_task")
    report = status(tmp_path, "example_research_task")
    assert index_path.exists()
    assert report["downloaded_files"] == 3
    assert report["indexed_documents"] == 3

