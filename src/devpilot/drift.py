"""Drift detection rules for DevPilot."""
from __future__ import annotations

import re
import tomllib
from pathlib import Path

from devpilot.models import Facts, Finding

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_INSTALL_KEYWORDS = ("pip install", "npm install", "yarn install", "poetry install")
_TEST_KEYWORDS = ("pytest", "python -m pytest", "npm test", "jest", "go test")


def _is_install(cmd: str) -> bool:
    lower = cmd.lower()
    return any(kw in lower for kw in _INSTALL_KEYWORDS)


def _is_test(cmd: str) -> bool:
    lower = cmd.lower()
    return any(kw in lower for kw in _TEST_KEYWORDS)


def _norm(s: str) -> str:
    """Strip, lowercase, collapse whitespace."""
    return " ".join(s.strip().lower().split())


def _substring_match(needle: str, haystack: str) -> bool:
    """Return True if normalized needle is a substring of normalized haystack."""
    return _norm(needle) in _norm(haystack)


# ---------------------------------------------------------------------------
# Rule D1 — env var read in code but not documented
# ---------------------------------------------------------------------------

def _d1(facts: Facts) -> list[Finding]:
    findings: list[Finding] = []
    for env_var in facts.env_vars:
        if not env_var.documented_in:
            findings.append(Finding(
                id="D1",
                severity="high",
                message=f"{env_var.name} read in code but not documented",
                evidence=list(env_var.read_at),
            ))
    return findings


# ---------------------------------------------------------------------------
# Rule D2 — install command mismatch
# ---------------------------------------------------------------------------

def _d2(facts: Facts) -> list[Finding]:
    findings: list[Finding] = []

    # Collect doc install commands: (path, command_string)
    doc_installs: list[tuple[str, str]] = []
    for doc in facts.docs:
        for cmd in doc.commands:
            if _is_install(cmd):
                doc_installs.append((doc.path, cmd))

    # Collect CI install commands: (workflow:line, run_string)
    ci_installs: list[tuple[str, str]] = []
    for ci in facts.ci_commands:
        if _is_install(ci.run):
            ci_installs.append((f"{ci.workflow}:{ci.line}", ci.run))

    ci_source = ci_installs[0][0] if ci_installs else "(no CI install step)"

    for doc_path, doc_cmd in doc_installs:
        # Check if the doc command is a substring-normalized match in any CI command
        matched = any(_substring_match(doc_cmd, ci_cmd) for _, ci_cmd in ci_installs)
        if not matched:
            findings.append(Finding(
                id="D2",
                severity="high",
                message="Install command mismatch",
                evidence=[doc_path, ci_source],
            ))

    return findings


# ---------------------------------------------------------------------------
# Rule D3 — test command mismatch
# ---------------------------------------------------------------------------

def _d3(facts: Facts) -> list[Finding]:
    findings: list[Finding] = []

    doc_tests: list[tuple[str, str]] = []
    for doc in facts.docs:
        for cmd in doc.commands:
            if _is_test(cmd):
                doc_tests.append((doc.path, cmd))

    ci_tests: list[tuple[str, str]] = []
    for ci in facts.ci_commands:
        if _is_test(ci.run):
            ci_tests.append((f"{ci.workflow}:{ci.line}", ci.run))

    ci_source = ci_tests[0][0] if ci_tests else "(no CI test step)"

    for doc_path, doc_cmd in doc_tests:
        matched = any(_substring_match(doc_cmd, ci_cmd) for _, ci_cmd in ci_tests)
        if not matched:
            findings.append(Finding(
                id="D3",
                severity="medium",
                message="Test command mismatch",
                evidence=[doc_path, ci_source],
            ))

    return findings


# ---------------------------------------------------------------------------
# Rule D4 — doc references a missing file path
# ---------------------------------------------------------------------------

def _d4(facts: Facts, repo: Path) -> list[Finding]:
    findings: list[Finding] = []
    for doc in facts.docs:
        for file_ref in doc.file_refs:
            if not (repo / file_ref).exists():
                findings.append(Finding(
                    id="D4",
                    severity="medium",
                    message=f"Referenced file missing: {file_ref}",
                    evidence=[doc.path, f"{file_ref} (missing)"],
                ))
    return findings


# ---------------------------------------------------------------------------
# Rule D5 — Python version in docs is outside requires-python
# ---------------------------------------------------------------------------

_PY_VER_RE = re.compile(r"python\s+(\d+)\.(\d+)\+?", re.IGNORECASE)


def _parse_requires_python_lower(repo: Path) -> tuple[int, int] | None:
    """Return the lower bound (major, minor) from requires-python in pyproject.toml."""
    pyproject = repo / "pyproject.toml"
    if not pyproject.is_file():
        return None
    try:
        data = tomllib.loads(pyproject.read_text(encoding="utf-8"))
    except Exception:
        return None
    req = data.get("project", {}).get("requires-python", "")
    if not req:
        return None
    # Parse >=X.Y style
    m = re.search(r">=\s*(\d+)\.(\d+)", req)
    if m:
        return int(m.group(1)), int(m.group(2))
    # Parse ==X.Y style (exact)
    m = re.search(r"==\s*(\d+)\.(\d+)", req)
    if m:
        return int(m.group(1)), int(m.group(2))
    return None


def _d5(facts: Facts, repo: Path) -> list[Finding]:
    findings: list[Finding] = []
    lower = _parse_requires_python_lower(repo)
    if lower is None:
        return findings

    lower_major, lower_minor = lower

    for doc in facts.docs:
        try:
            text = (repo / doc.path).read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for m in _PY_VER_RE.finditer(text):
            doc_major = int(m.group(1))
            doc_minor = int(m.group(2))
            if (doc_major, doc_minor) < (lower_major, lower_minor):
                findings.append(Finding(
                    id="D5",
                    severity="medium",
                    message="Python version mismatch",
                    evidence=[doc.path, "pyproject.toml"],
                ))
                break  # one finding per doc file is enough

    return findings


# ---------------------------------------------------------------------------
# Rule D6 — entry point documented but not declared
# ---------------------------------------------------------------------------

_BACKTICK_WORD_RE = re.compile(r"`([a-zA-Z][a-zA-Z0-9_-]*)`")
_CLI_CONTEXT_RE = re.compile(r"\b(CLI|command|tool|install)\b", re.IGNORECASE)


def _d6(facts: Facts, repo: Path) -> list[Finding]:
    findings: list[Finding] = []

    declared_names = {
        ep.name for ep in facts.entrypoints if ep.kind == "console_script"
    }

    for doc in facts.docs:
        try:
            text = (repo / doc.path).read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue

        # Split into paragraphs/sections for context check
        paragraphs = re.split(r"\n\s*\n", text)

        seen_in_doc: set[str] = set()
        for para in paragraphs:
            # Only consider paragraphs that mention CLI context
            if not _CLI_CONTEXT_RE.search(para):
                continue
            for m in _BACKTICK_WORD_RE.finditer(para):
                word = m.group(1)
                if word.isalpha() and word not in declared_names and word not in seen_in_doc:
                    seen_in_doc.add(word)
                    findings.append(Finding(
                        id="D6",
                        severity="low",
                        message=f"Entry point {word!r} documented but not declared",
                        evidence=[doc.path, "pyproject.toml (no console_scripts)"],
                    ))

    return findings


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def detect_drift(facts: Facts, repo: Path) -> list[Finding]:
    """Apply all drift rules and return findings."""
    findings: list[Finding] = []
    findings.extend(_d1(facts))
    findings.extend(_d2(facts))
    findings.extend(_d3(facts))
    findings.extend(_d4(facts, repo))
    findings.extend(_d5(facts, repo))
    findings.extend(_d6(facts, repo))
    return findings
