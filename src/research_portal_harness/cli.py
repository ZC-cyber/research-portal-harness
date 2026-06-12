from __future__ import annotations

import json
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

import typer

from .common import url_allowed, write_json
from .doctor import diagnose_workspace
from .indexer import index_downloads, status as status_report
from .mock_portal import run_mock_portal
from .portal import discover, fetch as fetch_portal, login as login_portal
from .safety import has_safety_ack, write_safety_ack
from .workspace import get_broker, get_task, init_workspace, load_brokers, save_brokers, upsert_broker

app = typer.Typer(help="Research Portal Harness execution CLI.")


def _root(workspace: Optional[Path]) -> Path:
    return (workspace or Path.cwd()).expanduser().resolve()


@app.command()
def init(workspace: Path = typer.Argument(..., help="Workspace directory to create or update.")) -> None:
    """Initialize a local acquisition workspace."""
    created = init_workspace(workspace)
    for path in created:
        typer.echo(f"created: {path}")


@app.command("safety-ack")
def safety_ack(
    workspace: Optional[Path] = typer.Option(None, "--workspace", "-w", help="Workspace root."),
    yes: bool = typer.Option(False, "--yes", "-y", help="Acknowledge without prompting."),
) -> None:
    """Record the first-run safety acknowledgement."""
    root = _root(workspace)
    typer.echo("Safety acknowledgement:")
    typer.echo("- I will only acquire research materials I am entitled to access.")
    typer.echo("- I will not paste passwords, one-time codes, cookies, or session tokens into chat.")
    typer.echo("- I will not bypass access controls, CAPTCHA, paywalls, entitlement checks, or rate limits.")
    typer.echo("- I am responsible for following my portal licenses and compliance rules.")
    if not yes and not typer.confirm("Acknowledge these terms?"):
        raise typer.Exit(1)
    path = write_safety_ack(root)
    typer.echo(f"wrote: {path}")


@app.command()
def setup(
    workspace: Path = typer.Option(..., "--workspace", "-w", help="Workspace root."),
    portal_id: str = typer.Option(..., "--portal-id", help="Stable lowercase portal id."),
    name: str = typer.Option(..., "--name", help="Human-readable portal name."),
    login_url: str = typer.Option(..., "--login-url", help="Official login or portal URL."),
    allowed_domain: list[str] = typer.Option(None, "--allowed-domain", help="Allowed domain. May be repeated."),
    acknowledge_safety: bool = typer.Option(False, "--acknowledge-safety", help="Record safety acknowledgement."),
) -> None:
    """Initialize workspace and add the first portal in one command."""
    init_workspace(workspace)
    root = _root(workspace)
    if acknowledge_safety and not has_safety_ack(root):
        write_safety_ack(root)
    add_portal(portal_id, name=name, login_url=login_url, allowed_domain=allowed_domain, workspace=root)
    typer.echo("")
    typer.echo("Next:")
    typer.echo(f"  rph doctor {portal_id} --workspace {root}")
    typer.echo(f"  rph login {portal_id} --workspace {root}")
    typer.echo(f"  rph search {portal_id} --task example_research_task --workspace {root}")


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
    if not dry_run and not has_safety_ack(root):
        typer.echo("Safety acknowledgement missing. Run `rph safety-ack --workspace <workspace>` first.", err=True)
        raise typer.Exit(2)
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


@app.command()
def doctor(
    portal_id: Optional[str] = typer.Argument(None, help="Optional portal id to diagnose."),
    workspace: Optional[Path] = typer.Option(None, "--workspace", "-w", help="Workspace root."),
    json_output: bool = typer.Option(False, "--json", help="Print JSON."),
) -> None:
    """Diagnose workspace and portal recipe readiness."""
    root = _root(workspace)
    report = diagnose_workspace(root, portal_id)
    if json_output:
        typer.echo(json.dumps(report, indent=2))
        return
    for pid, checks in report["portals"].items():
        typer.echo(f"{pid}:")
        for check in checks:
            typer.echo(f"  {check['status'].upper():4} {check['check']}: {check['detail']}")


@app.command("smoke-test")
def smoke_test(workspace: Optional[Path] = typer.Option(None, "--workspace", "-w", help="Workspace root.")) -> None:
    """Run an end-to-end local mock portal test."""
    root = _root(workspace or Path("/tmp/rph-smoke-workspace"))
    init_workspace(root)
    write_safety_ack(root)
    with run_mock_portal() as base_url:
        portal_id = "mock_research"
        add_portal(
            portal_id,
            name="Mock Research Portal",
            login_url=f"{base_url}/research",
            allowed_domain=["127.0.0.1"],
            workspace=root,
        )
        config = load_brokers(root)
        for broker in config["brokers"]:
            if broker.get("id") == portal_id:
                broker["manual_login"] = False
                broker["auth_success_url_patterns"] = ["research"]
        save_brokers(root, config)
        result = fetch_portal(root, get_broker(root, portal_id), get_task(root, "example_research_task"), max_downloads=10, headless=True)
        index_path = index_downloads(root, "example_research_task")
        report = status_report(root, "example_research_task")
    typer.echo(json.dumps({"fetch": result.__dict__, "index_path": str(index_path), "status": report}, indent=2))
    if result.downloaded < 3 or report["indexed_documents"] < 3:
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
