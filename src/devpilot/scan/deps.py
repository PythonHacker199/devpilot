"""Dependency scanner: detects pip (pyproject.toml / requirements*.txt) and npm."""
from __future__ import annotations

import json
import re
import tomllib
from pathlib import Path

from devpilot.models import Dep

_VERSION_RE = re.compile(r"[>=<!\s].*$")


def _strip_version(spec: str) -> str:
    """Return just the package name from a PEP 508 specifier."""
    return _VERSION_RE.sub("", spec).strip()


def scan_deps(repo: Path) -> Dep | None:
    # ── pyproject.toml ────────────────────────────────────────────────────────
    pyproject = repo / "pyproject.toml"
    if pyproject.is_file():
        data = tomllib.loads(pyproject.read_text(encoding="utf-8"))
        project = data.get("project", {})
        runtime = [_strip_version(s) for s in project.get("dependencies", [])]
        dev = [
            _strip_version(s)
            for s in project.get("optional-dependencies", {}).get("dev", [])
        ]
        return Dep(manager="pip", files=["pyproject.toml"], runtime=runtime, dev=dev)

    # ── requirements*.txt ────────────────────────────────────────────────────
    req_files = sorted(repo.glob("requirements*.txt"))
    if req_files:
        runtime: list[str] = []
        dev: list[str] = []
        files: list[str] = []
        for idx, req_path in enumerate(req_files):
            rel = req_path.relative_to(repo).as_posix()
            files.append(rel)
            names = [
                _strip_version(line.strip())
                for line in req_path.read_text(encoding="utf-8").splitlines()
                if line.strip() and not line.strip().startswith("#")
            ]
            if idx == 0:
                runtime.extend(names)
            else:
                dev.extend(names)
        return Dep(manager="pip", files=files, runtime=runtime, dev=dev)

    # ── package.json ─────────────────────────────────────────────────────────
    pkg_json = repo / "package.json"
    if pkg_json.is_file():
        data = json.loads(pkg_json.read_text(encoding="utf-8"))
        runtime = list(data.get("dependencies", {}).keys())
        dev = list(data.get("devDependencies", {}).keys())
        return Dep(manager="npm", files=["package.json"], runtime=runtime, dev=dev)

    return None
