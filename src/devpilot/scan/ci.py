"""Scan GitHub Actions workflow files for shell run steps."""
from __future__ import annotations

from pathlib import Path

import yaml

from devpilot.models import CiCommand


def _find_run_line(text: str, run_value: str) -> int:
    """Return the 1-based line number of the `run:` key whose value matches run_value."""
    stripped = run_value.strip()
    lines = text.splitlines()
    for i, line in enumerate(lines, start=1):
        # Match lines that start with optional whitespace then "run:"
        stripped_line = line.lstrip()
        if not stripped_line.startswith("run:"):
            continue
        # Extract the inline value (if any) after "run:"
        inline = stripped_line[len("run:"):].strip()
        if inline and inline == stripped:
            return i
        # Multiline block scalar — the run: line itself is what we record
        if not inline or inline in ("|", ">", "|-", ">-"):
            return i
    return 0


def scan_ci(repo: Path) -> list[CiCommand]:
    """Scan .github/workflows/ for shell run steps and return CiCommand records."""
    workflows_dir = repo / ".github" / "workflows"
    if not workflows_dir.is_dir():
        return []

    results: list[CiCommand] = []

    for wf_path in sorted(
        list(workflows_dir.glob("*.yml")) + list(workflows_dir.glob("*.yaml"))
    ):
        raw_text = wf_path.read_text(encoding="utf-8")
        data = yaml.safe_load(raw_text)
        if not isinstance(data, dict):
            continue

        workflow_rel = wf_path.relative_to(repo).as_posix()
        jobs = data.get("jobs") or {}

        for _job_name, job in jobs.items():
            if not isinstance(job, dict):
                continue
            steps = job.get("steps") or []
            for step in steps:
                if not isinstance(step, dict) or "run" not in step:
                    continue
                run_value = str(step["run"]).strip()
                step_name = step.get("name", "(unnamed)")
                line = _find_run_line(raw_text, run_value)
                results.append(
                    CiCommand(
                        workflow=workflow_rel,
                        step=step_name,
                        run=run_value,
                        line=line,
                    )
                )

    return results
