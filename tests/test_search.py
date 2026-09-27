"""Tests for devpilot.search (BM25 over tiny_repo fixture)."""
from __future__ import annotations

from pathlib import Path

from devpilot._search import Chunk, answer

TINY_REPO = Path("tests/fixtures/tiny_repo")


def _top3_paths(results: list[tuple[Chunk, float]]) -> list[str]:
    """Return POSIX paths from the top-3 results."""
    return [chunk.path for chunk, _ in results[:3]]


# ---------------------------------------------------------------------------
# Q → file assertions
# ---------------------------------------------------------------------------

def test_env_vars_in_app_py():
    """'What environment variables are required?' → app.py in top-3."""
    results = answer(TINY_REPO, "What environment variables are required?", top_k=5)
    paths = _top3_paths(results)
    assert any("app.py" in p for p in paths), (
        f"Expected app.py in top-3 paths, got: {paths}"
    )


def test_install_in_readme():
    """'How do I install the project?' → README.md in top-3."""
    results = answer(TINY_REPO, "How do I install the project?", top_k=5)
    paths = _top3_paths(results)
    assert any("README.md" in p for p in paths), (
        f"Expected README.md in top-3 paths, got: {paths}"
    )


def test_python_version_in_readme_or_pyproject():
    """'What Python version is required?' → README.md or pyproject.toml in top-3."""
    results = answer(TINY_REPO, "What Python version is required?", top_k=5)
    paths = _top3_paths(results)
    assert any("README.md" in p or "pyproject.toml" in p for p in paths), (
        f"Expected README.md or pyproject.toml in top-3 paths, got: {paths}"
    )


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------

def test_empty_question_returns_empty_list():
    assert answer(TINY_REPO, "", top_k=5) == []


def test_returns_list_of_tuples():
    results = answer(TINY_REPO, "install", top_k=5)
    assert isinstance(results, list)
    for item in results:
        assert isinstance(item, tuple) and len(item) == 2
        chunk, score = item
        assert isinstance(chunk, Chunk)
        assert isinstance(score, float)
