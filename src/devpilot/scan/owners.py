"""Scan repository ownership from CODEOWNERS or git commit history."""
from __future__ import annotations

import subprocess
from collections import Counter
from pathlib import Path

from devpilot.models import Owner


def scan_owners(repo: Path) -> list[Owner]:
    # 1. Try CODEOWNERS in root or .github/
    for candidate in (repo / "CODEOWNERS", repo / ".github" / "CODEOWNERS"):
        if candidate.is_file():
            return _parse_codeowners(candidate)

    # 2. Fall back to git-authors per top-level directory
    return _owners_from_git(repo)


def _parse_codeowners(path: Path) -> list[Owner]:
    owners: list[Owner] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        parts = stripped.split()
        pattern = parts[0]
        owner_handles = parts[1:]
        owners.append(Owner(path=pattern, owners=owner_handles, source="codeowners"))
    return owners


def _owners_from_git(repo: Path) -> list[Owner]:
    owners: list[Owner] = []
    try:
        top_dirs = [p.name for p in repo.iterdir() if p.is_dir() and not p.name.startswith(".")]
    except OSError:
        return []

    for dir_name in top_dirs:
        try:
            result = subprocess.run(
                ["git", "-C", str(repo), "log", "--format=%ae", "--", dir_name],
                capture_output=True,
                text=True,
                timeout=10,
            )
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return []

        if result.returncode != 0:
            return []

        emails = [e.strip() for e in result.stdout.splitlines() if e.strip()]
        if not emails:
            continue

        most_common_email, _ = Counter(emails).most_common(1)[0]
        owners.append(Owner(path=dir_name, owners=[most_common_email], source="git-authors"))

    return owners
