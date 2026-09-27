"""Tests for src/devpilot/_report.py."""
from __future__ import annotations

import dataclasses
import json
from pathlib import Path

from devpilot._report import render_report
from devpilot._scan import run_scan

TINY_REPO = Path("tests/fixtures/tiny_repo")


def test_render_produces_html_and_md(tmp_path: Path) -> None:
    """render_report writes report.html and ONBOARDING.md with all six sections."""
    facts, findings = run_scan(TINY_REPO)

    (tmp_path / "facts.json").write_text(
        json.dumps(dataclasses.asdict(facts), indent=2, default=str),
        encoding="utf-8",
    )
    (tmp_path / "findings.json").write_text(
        json.dumps([dataclasses.asdict(f) for f in findings], indent=2),
        encoding="utf-8",
    )

    html_path, md_path = render_report(TINY_REPO, tmp_path)

    assert html_path.exists(), "report.html should be created"
    assert md_path.exists(), "ONBOARDING.md should be created"

    html = html_path.read_text(encoding="utf-8")
    for marker in ("Summary", "Architecture", "Setup Guide", "Drift", "Owners", "First"):
        assert marker in html, f"Expected section marker {marker!r} in report.html"


def test_render_without_verify_json(tmp_path: Path) -> None:
    """render_report completes without error when verify.json is absent."""
    facts, _findings = run_scan(TINY_REPO)

    (tmp_path / "facts.json").write_text(
        json.dumps(dataclasses.asdict(facts), indent=2, default=str),
        encoding="utf-8",
    )
    # deliberately do NOT write verify.json

    html_path, md_path = render_report(TINY_REPO, tmp_path)

    assert html_path.exists(), "report.html should be created even without verify.json"
