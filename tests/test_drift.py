"""Tests for drift detection rules against the tiny_repo fixture."""
from __future__ import annotations

from pathlib import Path

import pytest

from devpilot._scan import run_scan

TINY_REPO = Path("tests/fixtures/tiny_repo")


@pytest.fixture(scope="module")
def scan_results():
    facts, findings = run_scan(TINY_REPO)
    return facts, findings


def test_finding_count(scan_results):
    _, findings = scan_results
    assert len(findings) == 6, f"Expected 6 findings, got {len(findings)}: {[f.id for f in findings]}"


def test_all_ids_present(scan_results):
    _, findings = scan_results
    ids = {f.id for f in findings}
    assert ids == {"D1", "D2", "D3", "D4", "D5", "D6"}, f"Finding IDs: {ids}"


def test_d1_severity_and_message(scan_results):
    _, findings = scan_results
    d1 = next(f for f in findings if f.id == "D1")
    assert d1.severity == "high"
    assert "SECRET_KEY" in d1.message


def test_d2_severity(scan_results):
    _, findings = scan_results
    d2 = next(f for f in findings if f.id == "D2")
    assert d2.severity == "high"


def test_d5_severity(scan_results):
    _, findings = scan_results
    d5 = next(f for f in findings if f.id == "D5")
    assert d5.severity == "medium"


def test_d6_severity(scan_results):
    _, findings = scan_results
    d6 = next(f for f in findings if f.id == "D6")
    assert d6.severity == "low"
