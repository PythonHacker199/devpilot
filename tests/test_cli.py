"""Smoke tests for the DevPilot CLI."""
from __future__ import annotations

from typer.testing import CliRunner

from devpilot.cli import app

runner = CliRunner()


def test_help() -> None:
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "scan" in result.output
    assert "verify" in result.output
    assert "ask" in result.output
    assert "report" in result.output


def test_scan_help() -> None:
    result = runner.invoke(app, ["scan", "--help"])
    assert result.exit_code == 0


def test_verify_help() -> None:
    result = runner.invoke(app, ["verify", "--help"])
    assert result.exit_code == 0


def test_ask_help() -> None:
    result = runner.invoke(app, ["ask", "--help"])
    assert result.exit_code == 0


def test_report_help() -> None:
    result = runner.invoke(app, ["report", "--help"])
    assert result.exit_code == 0
