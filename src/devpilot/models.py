"""Data models shared across all DevPilot modules."""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Language:
    name: str
    files: int
    loc: int


@dataclass
class Dep:
    manager: str
    files: list[str]
    runtime: list[str]
    dev: list[str]


@dataclass
class Entrypoint:
    kind: str   # console_script | main_block | manage_py | dockerfile_cmd | npm_script
    name: str
    target: str
    source: str  # path:line


@dataclass
class EnvVar:
    name: str
    read_at: list[str]       # path:line references
    documented_in: list[str] # path:line references


@dataclass
class CiCommand:
    workflow: str
    step: str
    run: str
    line: int


@dataclass
class Hotspot:
    path: str
    commits_90d: int


@dataclass
class Owner:
    path: str
    owners: list[str]
    source: str  # "codeowners" | "git-authors"


@dataclass
class Todo:
    file: str
    line: int
    text: str
    kind: str  # TODO | FIXME | HACK | XXX


@dataclass
class DocFile:
    path: str
    kind: str          # readme | contributing | doc | pdf
    commands: list[str]
    file_refs: list[str]


@dataclass
class Facts:
    repo: str
    scanned_at: str
    languages: list[Language] = field(default_factory=list)
    deps: Dep | None = None
    entrypoints: list[Entrypoint] = field(default_factory=list)
    env_vars: list[EnvVar] = field(default_factory=list)
    ci_commands: list[CiCommand] = field(default_factory=list)
    hotspots: list[Hotspot] = field(default_factory=list)
    owners: list[Owner] = field(default_factory=list)
    todos: list[Todo] = field(default_factory=list)
    docs: list[DocFile] = field(default_factory=list)


@dataclass
class Finding:
    id: str        # "D1" – "D6"
    severity: str  # "high" | "medium" | "low"
    message: str
    evidence: list[str]  # path:line references for both sides


@dataclass
class VerifyStep:
    command: str
    exit_code: int
    duration_s: float
    output_tail: str  # last 40 lines joined
    passed: bool
