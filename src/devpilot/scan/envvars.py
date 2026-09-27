"""Scan a repository for environment variable usage and documentation."""
from __future__ import annotations

import re
from collections import defaultdict
from pathlib import Path

from devpilot.models import EnvVar

# --- code patterns ---
_PY_ENVIRON = re.compile(r"""os\.environ\[["'](\w+)["']\]""")
_PY_GETENV  = re.compile(r"""os\.getenv\(["'](\w+)["']""")
_JS_PROC    = re.compile(r'process\.env\.([A-Z_][A-Z0-9_]*)')

# --- doc patterns ---
_ENV_EXAMPLE_LINE = re.compile(r'^(\w+)=')
_DOC_CAPS         = re.compile(r'[A-Z][A-Z0-9_]{2,}')
_DOC_KEYWORDS     = re.compile(r'\b(env|variable|secret|key|config)\b', re.IGNORECASE)


def scan_envvars(repo: Path) -> list[EnvVar]:
    # name -> {"read_at": [...], "documented_in": [...]}
    data: dict[str, dict[str, list[str]]] = defaultdict(lambda: {"read_at": [], "documented_in": []})

    # --- scan Python files ---
    for path in repo.rglob("*.py"):
        rel = path.relative_to(repo).as_posix()
        for lineno, line in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
            for pattern in (_PY_ENVIRON, _PY_GETENV):
                for match in pattern.finditer(line):
                    data[match.group(1)]["read_at"].append(f"{rel}:{lineno}")

    # --- scan JS/TS files ---
    for ext in ("*.js", "*.ts"):
        for path in repo.rglob(ext):
            rel = path.relative_to(repo).as_posix()
            for lineno, line in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
                for match in _JS_PROC.finditer(line):
                    data[match.group(1)]["read_at"].append(f"{rel}:{lineno}")

    # --- scan .env.example ---
    env_example = repo / ".env.example"
    if env_example.exists():
        rel = env_example.relative_to(repo).as_posix()
        for lineno, line in enumerate(env_example.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
            m = _ENV_EXAMPLE_LINE.match(line)
            if m:
                data[m.group(1)]["documented_in"].append(f"{rel}:{lineno}")

    # --- scan .md / .rst doc files ---
    for ext in ("*.md", "*.rst"):
        for path in repo.rglob(ext):
            rel = path.relative_to(repo).as_posix()
            for lineno, line in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
                if _DOC_KEYWORDS.search(line):
                    for cap in _DOC_CAPS.findall(line):
                        data[cap]["documented_in"].append(f"{rel}:{lineno}")

    return sorted(
        [
            EnvVar(name=name, read_at=info["read_at"], documented_in=info["documented_in"])
            for name, info in data.items()
        ],
        key=lambda e: e.name,
    )
