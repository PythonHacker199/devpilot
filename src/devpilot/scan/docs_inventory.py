"""Scan documentation files in a repository."""
from __future__ import annotations

import re
from pathlib import Path

from devpilot.models import DocFile

# Shell-command heuristic patterns
_COMMAND_KEYWORDS = (
    "pip install",
    "npm install",
    "yarn install",
    "poetry install",
    "pytest",
    "python -m",
    "npm run",
    "make ",
)

# File-path word pattern
_FILE_REF_RE = re.compile(r"\b(\w[\w/-]*\.\w+)\b")


def _extract_commands(text: str) -> list[str]:
    commands: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        # Lines starting with $ (shell prompt)
        if stripped.startswith("$"):
            commands.append(stripped)
            continue
        # 4-space-indented lines (markdown code block) with executable text
        if line.startswith("    ") and any(kw in stripped for kw in _COMMAND_KEYWORDS):
            commands.append(stripped)
            continue
        # Lines containing any of the keyword patterns
        if any(kw in line for kw in _COMMAND_KEYWORDS):
            commands.append(stripped)
    return commands


def _extract_file_refs(text: str) -> list[str]:
    refs: list[str] = []
    seen: set[str] = set()
    for match in _FILE_REF_RE.finditer(text):
        word = match.group(1)
        # Skip URLs
        if "http" in word:
            continue
        # Skip e.g. / i.e. style abbreviations (single letter before dot)
        parts = word.split(".")
        if len(parts) == 2 and len(parts[0]) <= 2:  # noqa: PLR2004
            continue
        if word not in seen:
            seen.add(word)
            refs.append(word)
    return refs


def _kind(rel: str) -> str:
    name = Path(rel).name.lower()
    if name in ("readme.md", "readme.rst"):
        return "readme"
    if name in ("contributing.md", "contributing.rst"):
        return "contributing"
    if name.endswith(".pdf"):
        return "pdf"
    return "doc"


def scan_docs_inventory(repo: Path) -> list[DocFile]:
    results: list[DocFile] = []

    candidates: list[tuple[Path, str]] = []

    # Root-level named files
    for name in ("README.md", "README.rst", "CONTRIBUTING.md", "CONTRIBUTING.rst"):
        p = repo / name
        if p.is_file():
            candidates.append((p, name))

    # docs/**/*.md and docs/**/*.rst
    docs_dir = repo / "docs"
    if docs_dir.is_dir():
        for ext in ("*.md", "*.rst"):
            for p in sorted(docs_dir.rglob(ext)):
                rel = p.relative_to(repo).as_posix()
                candidates.append((p, rel))

    # Root *.pdf
    for p in sorted(repo.glob("*.pdf")):
        rel = p.relative_to(repo).as_posix()
        candidates.append((p, rel))

    for path, rel in candidates:
        if path.suffix.lower() == ".pdf":
            try:
                from pypdf import PdfReader  # noqa: PLC0415

                reader = PdfReader(str(path))
                text = "\n".join(
                    page.extract_text() or "" for page in reader.pages
                )
            except Exception:  # noqa: BLE001
                continue
        else:
            try:
                text = path.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue

        results.append(
            DocFile(
                path=rel,
                kind=_kind(rel),
                commands=_extract_commands(text),
                file_refs=_extract_file_refs(text),
            )
        )

    return results
