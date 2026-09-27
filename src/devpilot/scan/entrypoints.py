"""Scan a repository for entrypoints."""
from __future__ import annotations

import json
import re
import tomllib
from pathlib import Path

from devpilot.models import Entrypoint


def scan_entrypoints(repo: Path) -> list[Entrypoint]:
    results: list[Entrypoint] = []

    # --- pyproject.toml [project.scripts] ---
    pyproject = repo / "pyproject.toml"
    if pyproject.is_file():
        raw = pyproject.read_text(encoding="utf-8")
        data = tomllib.loads(raw)
        scripts: dict[str, str] = (
            data.get("project", {}).get("scripts", {})
        )
        raw_lines = raw.splitlines()
        for key, value in scripts.items():
            # Find the line number of the key in the raw text (1-based).
            line_no = 1
            for i, line in enumerate(raw_lines, start=1):
                if re.search(rf'^\s*{re.escape(key)}\s*=', line):
                    line_no = i
                    break
            results.append(
                Entrypoint(
                    kind="console_script",
                    name=key,
                    target=value,
                    source=f"pyproject.toml:{line_no}",
                )
            )

    # --- if __name__ == "__main__": blocks ---
    main_pattern = re.compile(r'if\s+__name__\s*==\s*["\']__main__["\']')
    for py_file in sorted(repo.rglob("*.py")):
        lines = py_file.read_text(encoding="utf-8", errors="replace").splitlines()
        for i, line in enumerate(lines, start=1):
            if main_pattern.search(line):
                rel = py_file.relative_to(repo).as_posix()
                results.append(
                    Entrypoint(
                        kind="main_block",
                        name=rel,
                        target="__main__",
                        source=f"{rel}:{i}",
                    )
                )
                break  # one entrypoint per file

    # --- manage.py at repo root ---
    if (repo / "manage.py").is_file():
        results.append(
            Entrypoint(
                kind="manage_py",
                name="manage.py",
                target="manage.py",
                source="manage.py:1",
            )
        )

    # --- Dockerfile CMD ---
    dockerfile = repo / "Dockerfile"
    if dockerfile.is_file():
        cmd_pattern = re.compile(r'^\s*CMD\s+(.+)', re.IGNORECASE)
        for i, line in enumerate(dockerfile.read_text(encoding="utf-8").splitlines(), start=1):
            m = cmd_pattern.match(line)
            if m:
                results.append(
                    Entrypoint(
                        kind="dockerfile_cmd",
                        name="CMD",
                        target=m.group(1).strip(),
                        source=f"Dockerfile:{i}",
                    )
                )

    # --- package.json scripts ---
    pkg_json = repo / "package.json"
    if pkg_json.is_file():
        data_js = json.loads(pkg_json.read_text(encoding="utf-8"))
        for key, value in data_js.get("scripts", {}).items():
            results.append(
                Entrypoint(
                    kind="npm_script",
                    name=key,
                    target=value,
                    source="package.json:1",
                )
            )

    return results
