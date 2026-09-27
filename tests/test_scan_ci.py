"""Tests for devpilot.scan.ci.scan_ci."""
from __future__ import annotations

from pathlib import Path

from devpilot.scan.ci import scan_ci

TINY_REPO = Path(__file__).parent / "fixtures" / "tiny_repo"


def test_returns_two_commands():
    commands = scan_ci(TINY_REPO)
    assert len(commands) == 2


def test_first_step_name_and_run():
    commands = scan_ci(TINY_REPO)
    assert commands[0].step == "Install"
    assert commands[0].run == "pip install -e .[dev]"


def test_second_step_name_and_run():
    commands = scan_ci(TINY_REPO)
    assert commands[1].step == "Test"
    assert commands[1].run == "pytest -v"


def test_workflow_path():
    commands = scan_ci(TINY_REPO)
    assert commands[0].workflow == ".github/workflows/ci.yml"
    assert commands[1].workflow == ".github/workflows/ci.yml"


def test_lines_are_positive_integers():
    commands = scan_ci(TINY_REPO)
    for cmd in commands:
        assert isinstance(cmd.line, int)
        assert cmd.line > 0


def test_empty_repo_returns_empty_list(tmp_path: Path):
    result = scan_ci(tmp_path)
    assert result == []
