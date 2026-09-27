"""Tests for scan_docs_inventory."""
from __future__ import annotations

from pathlib import Path

from devpilot.scan.docs_inventory import scan_docs_inventory

TINY_REPO = Path(__file__).parent / "fixtures" / "tiny_repo"


def test_returns_at_least_one_item():
    results = scan_docs_inventory(TINY_REPO)
    assert len(results) >= 1


def test_readme_kind_and_path():
    results = scan_docs_inventory(TINY_REPO)
    readme = next((d for d in results if d.path == "README.md"), None)
    assert readme is not None, "README.md not found in results"
    assert readme.kind == "readme"


def test_readme_commands_contain_pip_install():
    results = scan_docs_inventory(TINY_REPO)
    readme = next(d for d in results if d.path == "README.md")
    assert any(
        "pip install" in cmd for cmd in readme.commands
    ), f"No pip install command found; commands={readme.commands}"


def test_readme_file_refs_contain_setup_guide():
    results = scan_docs_inventory(TINY_REPO)
    readme = next(d for d in results if d.path == "README.md")
    assert "docs/setup_guide.md" in readme.file_refs, (
        f"docs/setup_guide.md not in file_refs: {readme.file_refs}"
    )


def test_empty_repo_returns_empty_list(tmp_path):
    results = scan_docs_inventory(tmp_path)
    assert results == []
