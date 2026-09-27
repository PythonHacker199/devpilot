"""Tests for devpilot.scan.deps.scan_deps."""
from pathlib import Path

from devpilot.scan.deps import scan_deps

TINY_REPO = Path(__file__).parent / "fixtures" / "tiny_repo"


def test_returns_dep_not_none():
    dep = scan_deps(TINY_REPO)
    assert dep is not None


def test_manager_is_pip():
    dep = scan_deps(TINY_REPO)
    assert dep.manager == "pip"


def test_runtime_is_empty():
    dep = scan_deps(TINY_REPO)
    assert dep.runtime == []


def test_dev_contains_pytest_and_ruff():
    dep = scan_deps(TINY_REPO)
    assert "pytest" in dep.dev
    assert "ruff" in dep.dev


def test_files_contains_pyproject_toml():
    dep = scan_deps(TINY_REPO)
    assert "pyproject.toml" in dep.files


def test_empty_dir_returns_none(tmp_path):
    assert scan_deps(tmp_path) is None
