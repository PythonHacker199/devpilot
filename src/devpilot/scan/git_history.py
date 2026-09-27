"""Scan git history to identify the most frequently changed files (hotspots)."""
from __future__ import annotations

import subprocess
from collections import Counter
from pathlib import Path

from devpilot.models import Hotspot

_TOP_N = 20


def scan_git_history(repo: Path) -> list[Hotspot]:
    """Return the top-20 files by commit count over the last 90 days."""
    # Treat the path as a git repo only when it contains a .git entry directly
    # (file or directory).  This prevents git from walking up to a parent repo
    # when the given path is a plain subdirectory.
    if not (repo / ".git").exists():
        return []

    try:
        result = subprocess.run(
            [
                "git",
                "-C",
                str(repo),
                "log",
                "--since=90.days.ago",
                "--name-only",
                "--format=",
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )
    except Exception:
        return []

    if result.returncode != 0:
        return []

    counts: Counter[str] = Counter()
    for line in result.stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        # Skip lines that look like commit hashes (40-char hex) — belt-and-braces
        # guard; with --format= git emits only blank separator lines and paths.
        if len(line) == 40 and all(c in "0123456789abcdefABCDEF" for c in line):
            continue
        counts[line.replace("\\", "/")] += 1

    if not counts:
        return []

    top = counts.most_common(_TOP_N)
    return [Hotspot(path=path, commits_90d=n) for path, n in top]
