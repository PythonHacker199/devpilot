"""Tests for devpilot.scan.git_history."""
from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from devpilot.models import Hotspot
from devpilot.scan.git_history import scan_git_history

TINY_REPO = Path(__file__).parent / "fixtures" / "tiny_repo"


def test_not_a_git_repo_returns_empty_list() -> None:
    """tiny_repo fixture is not a git repo; scanner must return [] gracefully."""
    result = scan_git_history(TINY_REPO)
    assert result == []


@pytest.mark.skipif(shutil.which("git") is None, reason="git not available")
def test_real_repo_returns_hotspots() -> None:
    """Running against the devpilot repo itself should yield valid Hotspot objects."""
    result = scan_git_history(Path("."))
    # May be empty if there are genuinely no commits in the window, but each
    # item must be a Hotspot with a positive commit count.
    assert isinstance(result, list)
    for item in result:
        assert isinstance(item, Hotspot)
        assert item.commits_90d >= 1


def test_return_type_is_always_list() -> None:
    """scan_git_history must always return list[Hotspot], never None or another type."""
    result = scan_git_history(TINY_REPO)
    assert isinstance(result, list)
    for item in result:
        assert isinstance(item, Hotspot)
