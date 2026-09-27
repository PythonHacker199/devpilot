"""Tests for src/devpilot/_verify.py."""
from __future__ import annotations

import dataclasses
import json
from pathlib import Path

FAILING_REPO = Path(__file__).parent / "fixtures" / "failing_repo"


def _write_facts(path: Path, ci_commands: list[dict]) -> None:
    facts_data = {
        "repo": "test",
        "scanned_at": "2024-01-01T00:00:00",
        "languages": [],
        "deps": None,
        "entrypoints": [],
        "env_vars": [],
        "ci_commands": ci_commands,
        "hotspots": [],
        "owners": [],
        "todos": [],
        "docs": [],
    }
    path.write_text(json.dumps(facts_data), encoding="utf-8")


def test_deny_list_blocks_sudo(tmp_path: Path) -> None:
    """A step with 'sudo' must be blocked without executing anything."""
    from devpilot._verify import run_verify

    facts_path = tmp_path / "facts.json"
    _write_facts(
        facts_path,
        ci_commands=[
            {
                "workflow": "ci.yml",
                "step": "Bad",
                "run": "sudo rm -rf /",
                "line": 1,
            }
        ],
    )

    steps = run_verify(tmp_path, facts_path)

    # "sudo rm -rf /" is both relevant (contains no install/test keyword) so it
    # won't normally be in the relevant list — but the deny-list must fire on
    # any command that happens to pass relevance AND is denied.
    # Since "sudo rm -rf /" contains neither an install nor a test keyword it
    # won't be in `relevant`; add a compound command that is both relevant AND
    # denied so the deny-list path is exercised.
    facts_path2 = tmp_path / "facts2.json"
    _write_facts(
        facts_path2,
        ci_commands=[
            {
                "workflow": "ci.yml",
                "step": "Sneaky install",
                "run": "sudo pip install -e .[dev]",
                "line": 1,
            }
        ],
    )

    steps = run_verify(tmp_path, facts_path2)

    assert len(steps) == 1
    step = steps[0]
    assert step.passed is False
    assert "BLOCKED" in step.output_tail


def test_exit_code_captured(tmp_path: Path) -> None:
    """The failing_repo fixture should produce at least one failed step."""
    from devpilot._scan import run_scan
    from devpilot._verify import run_verify

    # Produce facts.json from the failing_repo fixture
    facts, _findings = run_scan(FAILING_REPO)
    out_dir = tmp_path / ".devpilot"
    out_dir.mkdir(exist_ok=True)
    facts_path = out_dir / "facts.json"
    facts_path.write_text(
        json.dumps(dataclasses.asdict(facts), indent=2, default=str),
        encoding="utf-8",
    )

    steps = run_verify(FAILING_REPO, facts_path)

    assert len(steps) >= 1, "Expected at least one verify step"
    assert any(not s.passed for s in steps), (
        f"Expected at least one failed step, got: {steps}"
    )
