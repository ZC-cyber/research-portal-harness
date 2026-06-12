from __future__ import annotations

import json
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

import typer

from .common import url_allowed, write_json
from .indexer import index_downloads, status as status_report
from .portal import discover, fetch as fetch_portal, login as login_portal
from .workspace import get_broker, get_task, init_workspace, load_brokers, upsert_broker

app = typer.Typer(help="Research Portal Harness execution CLI.")


def _root(workspace: Optional[Path]) -> Path:
    return (workspace or Path.cwd()).expanduser().resolve()


@app.command()
def init(workspace: Path = typer.Argument(..., help="Workspace directory to create or update.")) -> None:
    """Initialize a local acquisition workspace."""
    created = init_workspace(workspace)
    for path in created:
        typer.echo(f"created: {path}")


@app.command("add-portal")
def add_portal(
    portal_id: str = typer.Argument(..., help="Stable lowercase portal id."),
    name: str = typer.Option(..., "--name", help="Human-readable portal name."),
    login_url: str = typer.Option(..., "--login-url", help="Official login or portal URL."),
    allowed_domain: list[str] = typer.Option(None, "--allowed-domain", help="Allowed domain. May be repeated."),
    workspace: Optional[Path] = typer.Option(None, "--workspace", "-w", help="Workspace root."),
) -> None:
    """Add or update a portal recipe."""
    root = _root(workspace)
    parsed = urlparse(login_url)
    domains = allowed_domain or ([parsed.hostname] if parsed.hostname else [])
    if not parsed.scheme or not parsed.hostname:
        raise typer.BadParameter("login-url must be an absolute URL")
    broker = {
        "id": portal_id,
        "name": name,
        "allowed_domains": domains,
        "start_urls": [login_url],
        "manual_login": True,
        "enabled": True,
        "auth_pending_url_patterns": ["login", "signin", "sso", "mfa"],
        "auth_success_url_patterns": [],
        "auth_success_selectors": [],
        "download_selectors": [
            "a[download]",
            "a[href*='download' i]",
            "a[href*='pdf' i]",
            "button:has-text('Download')",
            "button:has-text('PDF')",
            "button:has-text('Excel')",
        ],
        "exclude_url_patterns": ["privacy", "terms", "logout", "support"],
        "exclude_title_patterns": ["Terms of Use", "Privacy", "Support"],
    }
    if not url_allowed(login_url, domains):
        raise typer.BadParameter("login-url host must be covered by allowed-domain")
    upsert_broker(root, broker)
    typer.echo(f"portal saved: {portal_id}")


@app.command()
def login(
    portal_id: str = typer.Argument(..., help="Portal id from config/brokers.json."),
    workspace: Optional[Path] = typer.Option(None, "--workspace", "-w", help="Workspace root."),
    headless: bool = typer.Option(False, "--headless", help="Run browser headlessly."),
) -> None:
    """Open a visible browser and wait for the user to complete login."""
    root = _root(workspace)
    broker = get_broker(root, portal_id)
    ok = login_portal(root, broker, headless=headless)
    if not ok:
        raise typer.Exit(1)
    typer.echo(f"login ok: {portal_id}")


@app.command()
def search(
    portal_id: str = typer.Argument(..., help="Portal id from config/brokers.json."),
    task_id: Optional[str] = typer.Option(None, "--task", help="Task id from config/tasks.json."),
    workspace: Optional[Path] = typer.Option(None, "--workspace", "-w", help="Workspace root."),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Write candidates JSON."),
    headless: bool = typer.Option(False, "--headless", help="Run browser headlessly."),
) -> None:
    """Discover candidate report/model/data links without downloading."""
    root = _root(workspace)
    broker = get_broker(root, portal_id)
    task = get_task(root, task_id) if task_id else None
    candidates = discover(root, broker, task, headless=headless)
    destination = output or root / "data" / "state" / "search_candidates" / f"{portal_id}.{task_id or 'manual'}.json"
    write_json(destination, {"portal_id": portal_id, "task_id": task_id, "candidates": candidates})
    for candidate in candidates[:25]:
        typer.echo(f"- {candidate['title']} | {candidate['url']}")
    typer.echo(f"candidates: {len(candidates)}")
    typer.echo(f"wrote: {destination}")


@app.command()
def fetch(
    portal_id: str = typer.Argument(..., help="Portal id from config/brokers.json."),
    task_id: Optional[str] = typer.Option(None, "--task", help="Task id from config/tasks.json."),
    workspace: Optional[Path] = typer.Option(None, "--workspace", "-w", help="Workspace root."),
    dry_run: bool = typer.Option(False, "--dry-run", help="Discover candidates but do not download."),
    max_downloads: Optional[int] = typer.Option(None, "--max-downloads", help="Download cap for this run."),
    headless: bool = typer.Option(False, "--headless", help="Run browser headlessly."),
) -> None:
    """Download candidate PDFs, models, financial data, and exports."""
    root = _root(workspace)
    broker = get_broker(root, portal_id)
    task = get_task(root, task_id) if task_id else None
    result = fetch_portal(root, broker, task, dry_run=dry_run, max_downloads=max_downloads, headless=headless)
    typer.echo(json.dumps(result.__dict__, indent=2))


@app.command()
def index(
    task_id: Optional[str] = typer.Option(None, "--task", help="Limit to one task id."),
    workspace: Optional[Path] = typer.Option(None, "--workspace", "-w", help="Workspace root."),
) -> None:
    """Index downloaded research files into JSONL metadata."""
    root = _root(workspace)
    path = index_downloads(root, task_id)
    typer.echo(f"wrote: {path}")


@app.command()
def status(
    task_id: Optional[str] = typer.Option(None, "--task", help="Limit to one task id."),
    workspace: Optional[Path] = typer.Option(None, "--workspace", "-w", help="Workspace root."),
    json_output: bool = typer.Option(False, "--json", help="Print JSON."),
) -> None:
    """Show download and index status."""
    root = _root(workspace)
    report = status_report(root, task_id)
    if json_output:
        typer.echo(json.dumps(report, indent=2))
        return
    typer.echo(f"downloaded_files: {report['downloaded_files']}")
    typer.echo(f"indexed_documents: {report['indexed_documents']}")
    typer.echo(f"manifest_path: {report['manifest_path']}")
    typer.echo(f"index_path: {report['index_path']}")
    for broker, count in report["by_broker"].items():
        typer.echo(f"{broker}: {count}")


@app.command("list-portals")
def list_portals(workspace: Optional[Path] = typer.Option(None, "--workspace", "-w", help="Workspace root.")) -> None:
    """List configured portals."""
    root = _root(workspace)
    config = load_brokers(root)
    for broker in config.get("brokers", []):
        enabled = "enabled" if broker.get("enabled") else "disabled"
        domains = ", ".join(broker.get("allowed_domains", [])) or "no domains"
        typer.echo(f"{broker.get('id')} | {enabled} | {domains}")


if __name__ == "__main__":
    app()

