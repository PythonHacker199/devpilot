"""Scan a repository for TODO/FIXME/HACK/XXX comments."""
from __future__ import annotations

import re
from pathlib import Path

from devpilot.models import Todo

_PATTERN = re.compile(r"\b(TODO|FIXME|HACK|XXX)\b", re.IGNORECASE)

_SKIP_DIRS = {
    ".git",
    "node_modules",
    ".venv",
    "venv",
    "__pycache__",
    ".devpilot",
    "dist",
    "build",
}


def scan_todos(repo: Path) -> list[Todo]:
    todos: list[Todo] = []

    for path in sorted(repo.rglob("*")):
        # Skip entries whose any ancestor directory is in the skip list
        if any(part in _SKIP_DIRS for part in path.parts):
            continue
        if not path.is_file():
            continue

        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except UnicodeDecodeError:
            continue

        rel = path.relative_to(repo).as_posix()
        for lineno, raw in enumerate(lines, start=1):
            m = _PATTERN.search(raw)
            if m:
                todos.append(
                    Todo(
                        file=rel,
                        line=lineno,
                        text=raw.strip(),
                        kind=m.group(1).upper(),
                    )
                )

    todos.sort(key=lambda t: (t.file, t.line))
    return todos
