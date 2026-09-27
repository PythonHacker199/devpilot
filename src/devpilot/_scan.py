"""Wire all scanners together into a single scan pipeline."""
from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from devpilot.models import Facts, Finding
from devpilot.scan.ci import scan_ci
from devpilot.scan.deps import scan_deps
from devpilot.scan.docs_inventory import scan_docs_inventory
from devpilot.scan.entrypoints import scan_entrypoints
from devpilot.scan.envvars import scan_envvars
from devpilot.scan.git_history import scan_git_history
from devpilot.scan.languages import scan_languages
from devpilot.scan.owners import scan_owners
from devpilot.scan.todos import scan_todos


def run_scan(repo: Path) -> tuple[Facts, list[Finding]]:
    """Run all scanners and drift detection on *repo*."""
    repo = repo.resolve()
    facts = Facts(
        repo=repo.name,
        scanned_at=datetime.now(UTC).isoformat(),
        languages=scan_languages(repo),
        deps=scan_deps(repo),
        entrypoints=scan_entrypoints(repo),
        env_vars=scan_envvars(repo),
        ci_commands=scan_ci(repo),
        hotspots=scan_git_history(repo),
        owners=scan_owners(repo),
        todos=scan_todos(repo),
        docs=scan_docs_inventory(repo),
    )

    from devpilot.drift import detect_drift

    findings = detect_drift(facts, repo)
    return facts, findings
