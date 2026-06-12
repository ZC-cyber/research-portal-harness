from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from research_portal_harness.cli import app


runner = CliRunner()


def test_cli_init_and_list_portals(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"

    result = runner.invoke(app, ["init", str(workspace)])
    assert result.exit_code == 0
    assert (workspace / "config" / "brokers.json").exists()

    result = runner.invoke(app, ["list-portals", "--workspace", str(workspace)])
    assert result.exit_code == 0
    assert "bernstein_research" in result.stdout


def test_cli_add_portal(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    runner.invoke(app, ["init", str(workspace)])

    result = runner.invoke(
        app,
        [
            "add-portal",
            "example_portal",
            "--name",
            "Example Portal",
            "--login-url",
            "https://research.example.com/login",
            "--allowed-domain",
            "example.com",
            "--workspace",
            str(workspace),
        ],
    )

    assert result.exit_code == 0
    listed = runner.invoke(app, ["list-portals", "--workspace", str(workspace)])
    assert "example_portal" in listed.stdout


def test_cli_setup_safety_ack_and_doctor(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"

    result = runner.invoke(
        app,
        [
            "setup",
            "--workspace",
            str(workspace),
            "--portal-id",
            "example_portal",
            "--name",
            "Example Portal",
            "--login-url",
            "https://research.example.com/login",
            "--allowed-domain",
            "example.com",
            "--acknowledge-safety",
        ],
    )
    assert result.exit_code == 0
    assert (workspace / "data" / "state" / "safety_ack.json").exists()

    result = runner.invoke(app, ["doctor", "example_portal", "--workspace", str(workspace)])
    assert result.exit_code == 0
    assert "safety_ack" in result.stdout
    assert "allowed_domains" in result.stdout


def test_fetch_requires_safety_ack(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    runner.invoke(app, ["init", str(workspace)])
    runner.invoke(
        app,
        [
            "add-portal",
            "example_portal",
            "--name",
            "Example Portal",
            "--login-url",
            "https://research.example.com/login",
            "--allowed-domain",
            "example.com",
            "--workspace",
            str(workspace),
        ],
    )

    result = runner.invoke(app, ["fetch", "example_portal", "--workspace", str(workspace)])
    assert result.exit_code == 2
    assert "Safety acknowledgement missing" in result.output
