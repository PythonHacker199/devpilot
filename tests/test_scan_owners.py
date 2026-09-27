"""Tests for devpilot.scan.owners."""
from __future__ import annotations

from pathlib import Path

from devpilot.models import Owner
from devpilot.scan.owners import scan_owners

TINY_REPO = Path(__file__).parent / "fixtures" / "tiny_repo"


def test_no_codeowners_not_git_repo_returns_empty():
    """tiny_repo has no CODEOWNERS and is not a git repo → []."""
    result = scan_owners(TINY_REPO)
    assert result == []


def test_codeowners_parsed_correctly(tmp_path):
    """A CODEOWNERS file is parsed into Owner entries."""
    codeowners = tmp_path / "CODEOWNERS"
    codeowners.write_text(
        "# comment\n"
        "src/ @alice @bob\n"
        "*.py @charlie\n",
        encoding="utf-8",
    )

    result = scan_owners(tmp_path)

    assert len(result) == 2
    assert result[0].path == "src/"
    assert result[0].owners == ["@alice", "@bob"]
    assert result[0].source == "codeowners"


def test_result_is_always_list_of_owner(tmp_path):
    """Return type is always list[Owner] regardless of code path."""
    # No CODEOWNERS, non-git dir → []
    result_empty = scan_owners(tmp_path)
    assert isinstance(result_empty, list)
    for item in result_empty:
        assert isinstance(item, Owner)

    # With CODEOWNERS
    (tmp_path / "CODEOWNERS").write_text("docs/ @team\n", encoding="utf-8")
    result_owners = scan_owners(tmp_path)
    assert isinstance(result_owners, list)
    for item in result_owners:
        assert isinstance(item, Owner)
