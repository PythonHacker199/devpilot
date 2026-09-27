"""Tests for devpilot.scan.entrypoints."""
from __future__ import annotations

import sys
from pathlib import Path

# Ensure the src layout is importable when the package is not installed.
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


from devpilot.scan.entrypoints import scan_entrypoints  # noqa: E402

# ---------------------------------------------------------------------------
# Shared fixture path
# ---------------------------------------------------------------------------
TINY_REPO = Path(__file__).parent / "fixtures" / "tiny_repo"


# ---------------------------------------------------------------------------
# Test 1 – tiny_repo returns no entrypoints
# ---------------------------------------------------------------------------
def test_empty_on_tiny_repo() -> None:
    results = scan_entrypoints(TINY_REPO)
    assert results == []


# ---------------------------------------------------------------------------
# Test 2 – pyproject.toml [project.scripts] → console_script
# ---------------------------------------------------------------------------
def test_console_script(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text(
        "[project.scripts]\nmytool = \"mypkg.cli:main\"\n",
        encoding="utf-8",
    )
    results = scan_entrypoints(tmp_path)
    assert len(results) == 1
    ep = results[0]
    assert ep.kind == "console_script"
    assert ep.name == "mytool"
    assert ep.target == "mypkg.cli:main"
    assert ep.source.startswith("pyproject.toml:")


# ---------------------------------------------------------------------------
# Test 3 – .py file with if __name__ == "__main__": → main_block
# ---------------------------------------------------------------------------
def test_main_block(tmp_path: Path) -> None:
    script = tmp_path / "run.py"
    script.write_text(
        'def main():\n    pass\n\nif __name__ == "__main__":\n    main()\n',
        encoding="utf-8",
    )
    results = scan_entrypoints(tmp_path)
    kinds = [ep.kind for ep in results]
    assert "main_block" in kinds
    ep = next(ep for ep in results if ep.kind == "main_block")
    assert ep.name == "run.py"
    assert ep.target == "__main__"
    assert ep.source == "run.py:4"
