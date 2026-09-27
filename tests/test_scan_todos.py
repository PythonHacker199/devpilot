"""Tests for devpilot.scan.todos.scan_todos."""
from __future__ import annotations

from pathlib import Path

from devpilot.scan.todos import scan_todos

TINY_REPO = Path(__file__).parent / "fixtures" / "tiny_repo"


def test_empty_repo_returns_no_todos():
    """tiny_repo has no TODO comments."""
    assert scan_todos(TINY_REPO) == []


def test_finds_todo_fixme_hack(tmp_path: Path):
    """Three known markers are detected with correct kinds, file, and lines."""
    src = tmp_path / "sample.py"
    src.write_text(
        "# TODO: fix this\n"
        "x = 1  # FIXME: wrong value\n"
        "# hack: workaround\n",
        encoding="utf-8",
    )

    todos = scan_todos(tmp_path)

    assert len(todos) == 3
    assert [t.kind for t in todos] == ["TODO", "FIXME", "HACK"]
    assert all(t.file == "sample.py" for t in todos)
    assert [t.line for t in todos] == [1, 2, 3]


def test_case_insensitive_match(tmp_path: Path):
    """Lowercase 'todo' is matched because the regex is case-insensitive."""
    src = tmp_path / "notes.txt"
    src.write_text("todo: remember this\n", encoding="utf-8")

    todos = scan_todos(tmp_path)

    assert len(todos) == 1
    assert todos[0].kind == "TODO"


def test_git_directory_excluded(tmp_path: Path):
    """Files inside .git/ must never be scanned."""
    git_dir = tmp_path / ".git"
    git_dir.mkdir()
    (git_dir / "COMMIT_EDITMSG").write_text("TODO: not this one\n", encoding="utf-8")

    # Also add a real TODO outside .git so we know the scanner works
    (tmp_path / "real.py").write_text("# TODO: real one\n", encoding="utf-8")

    todos = scan_todos(tmp_path)

    files = [t.file for t in todos]
    assert all(".git" not in f for f in files)
    assert len(todos) == 1
    assert todos[0].file == "real.py"
