# DevPilot — Implementation Plan

## Overview

DevPilot is implemented as an ordered sequence of independent-then-converging milestones.
The deterministic Python CLI is built first; the Bob layer is assembled last.

```
Phase 2 (scaffold)
  └── Phase 3 (scanners, 9 parallel subagents)
        ├── Phase 4 (drift)
        ├── Phase 5 (verify)       ← 4 + 5 can run in parallel
        └── Phase 6 (ask / BM25)   ← 6 can run in parallel with 4 + 5
              └── Phase 7 (report) ← depends on 4 + 5; 6 optional
                    └── Phase 8 (Bob kit) ← depends on 4 + 5 + 7
                          └── Phase 9 (impact)
                                └── Phase 10 (package)
```

---

## Milestone 1 — Foundation (Phases 2–3)

### Phase 2 — Scaffold + Test Oracle

**Purpose:** Establish the package shape, the dataclasses every later module shares, the CLI
stub that proves installation works, and the hand-crafted test fixture that is the single
ground truth for all scanner and drift tests.

#### Inputs
- `docs/DESIGN.md` — package layout, models, CLI commands
- `.planning/REQUIREMENTS.md` — test oracle spec (D1–D6 trigger conditions)

#### Deliverables
| File | Notes |
|---|---|
| `pyproject.toml` | src layout; `devpilot = devpilot.cli:app`; runtime: typer, jinja2, pyyaml, pypdf; dev: pytest, ruff |
| `src/devpilot/__init__.py` | empty |
| `src/devpilot/models.py` | dataclasses: `Language`, `Dep`, `Entrypoint`, `EnvVar`, `CiCommand`, `Hotspot`, `Owner`, `Todo`, `DocFile`, `Facts`, `Finding`, `VerifyStep` |
| `src/devpilot/cli.py` | Typer app: `scan`, `verify`, `ask`, `report` stubs (each prints "not implemented yet") |
| `src/devpilot/scan/__init__.py` | empty |
| `tests/__init__.py` | empty |
| `tests/test_cli.py` | smoke: `--help`, each subcommand exits 0 |
| `tests/fixtures/tiny_repo/` | hand-built repo (see oracle spec below) |
| `scripts/fetch_sample.sh` | `git clone --depth 1 --branch 3.1.0 https://github.com/pallets/flask data/sample_repo` |
| `data/onboarding_questions.md` | 10 benchmark questions |

#### `tests/fixtures/tiny_repo` — exact file list

```
tests/fixtures/tiny_repo/
  pyproject.toml               # requires-python = ">=3.11"
  README.md                    # triggers D2, D3, D4, D5, D6
  app.py                       # triggers D1
  .github/
    workflows/
      ci.yml                   # triggers D2, D3
```

**D1 trigger — `app.py`**
```python
import os
SECRET_KEY = os.environ["SECRET_KEY"]   # not in .env.example, not in docs
```
(No `.env.example` exists.)

**D2 + D3 trigger — `.github/workflows/ci.yml`**
```yaml
steps:
  - name: Install
    run: pip install -e .[dev]           # differs from README "pip install -r requirements.txt"
  - name: Test
    run: pytest -v                       # differs from README "python -m pytest"
```

**D4 trigger — `README.md` contains:**
```
See [setup_guide](docs/setup_guide.md)  # file does not exist
```

**D5 trigger — `README.md` contains:**
```
Requires Python 3.9+.
```
but `pyproject.toml` has `requires-python = ">=3.11"`.

**D6 trigger — `README.md` contains:**
```
Install the `mytool` CLI after setup.
```
but `pyproject.toml` has no `[project.scripts]` entry for `mytool`.

#### Expected exact findings from `tiny_repo`

| id | severity | evidence (both sides) |
|---|---|---|
| D1 | high | `app.py:2` ↔ (no doc) |
| D2 | high | `README.md:N` (`pip install -r requirements.txt`) ↔ `.github/workflows/ci.yml:4` (`pip install -e .[dev]`) |
| D3 | medium | `README.md:N` (`python -m pytest`) ↔ `.github/workflows/ci.yml:7` (`pytest -v`) |
| D4 | medium | `README.md:N` ↔ `docs/setup_guide.md` (missing) |
| D5 | medium | `README.md:N` ("3.9+") ↔ `pyproject.toml:N` (`>=3.11`) |
| D6 | low | `README.md:N` (`mytool`) ↔ `pyproject.toml` (no console_scripts) |

---

### Phase 3 — Nine Scanners (parallel)

Each scanner is a single pure function `scan_X(repo: Path) -> list[Model]` with no global state,
no network calls, and no side effects. All nine can be implemented simultaneously.

#### Scanner specs

##### 1. `scan/languages.py` — `scan_languages(repo)`
- Walk every non-hidden, non-gitignored file
- Map extension → language name (`.py` → Python, `.ts`/`.tsx` → TypeScript, `.js`/`.jsx` → JavaScript, `.go` → Go, `.rb` → Ruby, `.rs` → Rust, `.java` → Java, `.md` → Markdown, `.yml`/`.yaml` → YAML, `.json` → JSON — unknown extension → "Other")
- Return `list[Language]` sorted by LOC descending
- Edge cases: binary files (skip), symlinks (follow once), empty files (count as 0 LOC)
- Model: `Language(name: str, files: int, loc: int)`
- **Test oracle:** `tiny_repo` → `[Language("Python", 1, 2), Language("YAML", 1, 7), Language("Markdown", 1, 10), Language("TOML", 1, 5)]` (line counts match actual fixture content)

##### 2. `scan/deps.py` — `scan_deps(repo)`
- Detect `pyproject.toml` (parse `[project].dependencies` + `[project.optional-dependencies].dev`), `requirements*.txt` (one entry per non-comment line), `package.json` (`dependencies` + `devDependencies`)
- Return single `Dep` dataclass (manager, files, runtime, dev)
- Edge cases: multiple requirements files, both pyproject and requirements present, no dep file (return empty)
- Model: `Dep(manager: str, files: list[str], runtime: list[str], dev: list[str])`
- **Test oracle:** `tiny_repo` → `Dep(manager="pip", files=["pyproject.toml"], runtime=[], dev=["pytest", "ruff"])`

##### 3. `scan/entrypoints.py` — `scan_entrypoints(repo)`
- Parse `[project.scripts]` in `pyproject.toml` → kind `console_script`
- Detect `if __name__ == "__main__":` in `.py` files → kind `main_block`
- Detect `manage.py` at repo root → kind `manage_py`
- Detect `CMD` instruction in `Dockerfile` → kind `dockerfile_cmd`
- Detect `scripts` section in `package.json` → kind `npm_script`
- Model: `Entrypoint(kind: str, name: str, target: str, source: str)`
  - `source` is `path:line`
- **Test oracle:** `tiny_repo` → `[]` (no console_scripts, no `__main__`, no Dockerfile)

##### 4. `scan/envvars.py` — `scan_envvars(repo)`
- Regex scan `.py` files for `os.environ\[["'](\w+)["']\]` and `os.getenv\(["'](\w+)["']`
- Regex scan `.js`/`.ts` files for `process\.env\.(\w+)`
- Collect vars from `.env.example` if present (lines matching `KEY=`)
- Collect documented var names from all doc files (naive: words in ALL_CAPS adjacent to "env", "variable", "set")
- Model: `EnvVar(name: str, read_at: list[str], documented_in: list[str])`
  - `read_at` and `documented_in` are `path:line` references
- **Test oracle:** `tiny_repo` → `[EnvVar(name="SECRET_KEY", read_at=["app.py:2"], documented_in=[])]`

##### 5. `scan/ci.py` — `scan_ci(repo)`
- Walk `.github/workflows/*.yml`
- Parse YAML; extract every `run:` string from `steps`
- Store workflow filename, step name, run string, line number
- Model: `CiCommand(workflow: str, step: str, run: str, line: int)`
- Edge cases: multi-line `run:` blocks (join lines), matrix strategy (ignore; treat as one)
- **Test oracle:** `tiny_repo` → `[CiCommand(workflow=".github/workflows/ci.yml", step="Install", run="pip install -e .[dev]", line=4), CiCommand(workflow=".github/workflows/ci.yml", step="Test", run="pytest -v", line=7)]`

##### 6. `scan/git_history.py` — `scan_git_history(repo)`
- Run `git log --since=90.days.ago --name-only --format=` via `subprocess`
- Count commit touches per file path
- Return top-20 by commit count, repo-relative POSIX paths
- Model: `Hotspot(path: str, commits_90d: int)`
- Edge cases: not a git repo (return `[]`), no commits in 90 days (return `[]`)
- **Test oracle:** `tiny_repo` (not a git repo) → `[]`

##### 7. `scan/owners.py` — `scan_owners(repo)`
- If `CODEOWNERS` or `.github/CODEOWNERS` exists: parse each pattern-owner line
- Else: for each top-level directory, run `git log --follow --format="%ae"` and tally top committer
- Model: `Owner(path: str, owners: list[str], source: str)` where `source` is `"codeowners"` or `"git-authors"`
- Edge cases: not a git repo and no CODEOWNERS (return `[]`)
- **Test oracle:** `tiny_repo` → `[]` (no CODEOWNERS, not a git repo)

##### 8. `scan/todos.py` — `scan_todos(repo)`
- Regex scan all text files for `TODO`, `FIXME`, `HACK`, `XXX` (case-insensitive, at word boundary)
- Skip binary files, `.git/`, `node_modules/`, `.venv/`, `__pycache__/`
- Model: `Todo(file: str, line: int, text: str, kind: str)` where `kind` ∈ {TODO, FIXME, HACK, XXX}
- **Test oracle:** `tiny_repo` → `[]` (no TODOs in fixture files)

##### 9. `scan/docs_inventory.py` — `scan_docs_inventory(repo)`
- Collect: `README.md`, `README.rst`, `CONTRIBUTING.md`, `CONTRIBUTING.rst`, `docs/**/*.md`, `docs/**/*.rst`, `*.pdf` (text via `pypdf`)
- For each file: extract inline code blocks (backtick-fenced), shell commands (`$ ` prefix or `pip`/`python`/`npm` prefixes), file path references (words matching `\w+/\w+\.\w+`)
- Model: `DocFile(path: str, kind: str, commands: list[str], file_refs: list[str])`
  - `kind` ∈ {readme, contributing, doc, pdf}
- **Test oracle:** `tiny_repo` → one `DocFile` for `README.md` with `commands` containing the install and test strings, `file_refs` containing `docs/setup_guide.md`

---

## Milestone 2 — Intelligence (Phases 4–7)

### Phase 4 — Doc-Drift Detection

#### Input models consumed
`EnvVar`, `CiCommand`, `DocFile`, `Entrypoint`, `Dep` from `facts.json`

#### Rule implementations

| Rule | Logic | Evidence fields |
|---|---|---|
| D1 | `env_var.documented_in == [] and env_var.name not in dot_env_keys` | `[read_at[0], "(undocumented)"]` |
| D2 | `doc.commands` contains install-like string ≠ `ci_command.run` for install step | `[doc.path:line, ci.workflow:line]` |
| D3 | `doc.commands` contains test-like string ≠ `ci_command.run` for test step | `[doc.path:line, ci.workflow:line]` |
| D4 | `doc.file_refs` contains a path that `(repo / ref).exists()` is False | `[doc.path:line, ref + " (missing)"]` |
| D5 | doc text matches `Python \d+\.\d+` and that version < `requires-python` lower bound | `[doc.path:line, "pyproject.toml:line"]` |
| D6 | doc text contains entry point name not in `entrypoints`, or vice versa | `[doc.path:line, "pyproject.toml:line"]` |

**Install heuristic:** command string contains `pip install`, `npm install`, `yarn install`, or `poetry install`.
**Test heuristic:** command string contains `pytest`, `python -m pytest`, `npm test`, `jest`.

#### Finding model
```python
@dataclass
class Finding:
    id: str          # "D1" – "D6"
    severity: str    # "high" | "medium" | "low"
    message: str
    evidence: list[str]   # ["path:line", ...] — both sides
```

#### Test oracle for `tiny_repo`
Exact expected `findings.json` (used verbatim in `test_drift.py`):
```json
[
  {"id": "D1", "severity": "high",   "message": "SECRET_KEY read in code but not documented", "evidence": ["app.py:2"]},
  {"id": "D2", "severity": "high",   "message": "Install command mismatch", "evidence": ["README.md:3", ".github/workflows/ci.yml:4"]},
  {"id": "D3", "severity": "medium", "message": "Test command mismatch",    "evidence": ["README.md:4", ".github/workflows/ci.yml:7"]},
  {"id": "D4", "severity": "medium", "message": "Referenced file missing",  "evidence": ["README.md:6", "docs/setup_guide.md (missing)"]},
  {"id": "D5", "severity": "medium", "message": "Python version mismatch",  "evidence": ["README.md:1", "pyproject.toml:2"]},
  {"id": "D6", "severity": "low",    "message": "Entry point mytool documented but not declared", "evidence": ["README.md:8", "pyproject.toml (no console_scripts)"]}
]
```

---

### Phase 5 — Setup Verification

#### Design
```
facts.ci_commands (install steps)
  └─► filter: deny-list check
        └─► create temp venv (tempfile.mkdtemp)
              └─► subprocess.run each command, timeout=300s
                    └─► capture returncode, duration, last 40 lines of stdout+stderr
                          └─► write verify.json
```

#### Deny-list (case-insensitive substring match)
`["sudo", "rm -rf /", "curl | sh", "curl|sh", "wget|sh", "bash <(", "eval $(", ":(){", "mkfs", "/dev/", "shutdown", "reboot"]`

#### VerifyStep model
```python
@dataclass
class VerifyStep:
    command: str
    exit_code: int
    duration_s: float
    output_tail: str   # last 40 lines, joined
    passed: bool       # exit_code == 0
```

#### Test strategy
- `tests/fixtures/failing_repo/` — a minimal repo whose only CI step is `exit 1`
- `test_verify.py` asserts that running `devpilot verify` on it produces `passed=False`
- A second test checks every deny-list string is rejected before subprocess

---

### Phase 6 — `devpilot ask` (BM25 search)

#### Chunking strategy
- **Python files:** parse with `ast`; each function/class body is one chunk. Header = `path:line — def/class name`
- **Other code files:** split by blank lines into paragraphs ≥ 3 lines
- **Markdown/RST docs:** split by `##`/`===` headings; each section is one chunk

#### BM25 implementation (no external library)
Standard Okapi BM25 with k1=1.5, b=0.75. Self-contained in `search.py` (~60 lines).

```python
score(q, d) = Σ_t IDF(t) * (f(t,d) * (k1+1)) / (f(t,d) + k1*(1 - b + b*|d|/avgdl))
```

#### CLI output format
```
[1] src/app.py:12 — def configure():
    SECRET_KEY = os.environ["SECRET_KEY"]  ...

[2] README.md:1 — Installation
    pip install -r requirements.txt ...
```

#### Test oracle (3 Q→file assertions for `tiny_repo`)
| Question | Expected top-1 file |
|---|---|
| "What environment variables are required?" | `app.py` |
| "How do I install the project?" | `README.md` |
| "What Python version is required?" | `README.md` or `pyproject.toml` |

---

### Phase 7 — HTML Report

#### Template sections (Jinja2)
1. **Summary cards** — language breakdown, dep count, drift findings by severity (high/medium/low), verify pass/fail ratio
2. **Architecture diagram** — Mermaid `graph LR` of top-level Python modules + their imports (static import analysis, not runtime)
3. **Setup guide** — only `VerifyStep` entries with `passed=True`, rendered as numbered shell code blocks
4. **Drift findings** — table: ID | Severity | Message | Evidence (each evidence item is a `<code>` span)
5. **Owners map** — table: Path | Owners | Source
6. **First 5 tasks** — ranked candidates from `todos` + small-file analysis; score formula:
   `score = (1 / max(loc, 1)) * (1 + has_test_nearby) * (1 + has_owner) * (1 - is_hotspot)`

#### Self-contained HTML
Single file: all CSS inline in `<style>`, Mermaid loaded from CDN for diagram rendering.
Light/dark mode via `@media (prefers-color-scheme: dark)` CSS block.

---

## Milestone 3 — Bob Layer (Phase 8)

### Phase 8 — IBM Bob Onboarding Kit

#### `.bob/custom_modes.yaml`
```yaml
customModes:
  - slug: onboarding-guide
    name: "🧭 Onboarding Guide"
    roleDefinition: >
      You are a senior engineer onboarding a new teammate to an unfamiliar repository.
      You have access to facts.json, findings.json, and verify.json produced by devpilot.
      Every command, path, env var, and owner you mention must come from those files or
      cite a file:line. If unsure, write UNVERIFIED rather than guessing.
    whenToUse: >
      When someone needs to understand, set up, or start contributing to a repository
      that has been processed by devpilot scan and devpilot verify.
    groups:
      - read
      - execute
      - skill
      - subagent
      - todo
      - - edit
        - fileRegex: "ONBOARDING\\.md|\\.devpilot/.*"
```

#### `.bob/rules-onboarding-guide/01-grounding.md`
Rules enforced in this mode:
- Every command must be sourced from `verify.json` (passed steps only) or `facts.json`
- Every file path must exist in `facts.json`
- Every env var must appear in `facts.json`
- Every owner must appear in `facts.json`
- Setup steps come only from `verify.json` steps where `passed: true`
- When a fact cannot be verified: write `UNVERIFIED: <claim>` rather than guessing

#### `.bob/skills/onboard-repo/SKILL.md`
```markdown
---
name: onboard-repo
description: >
  Run devpilot scan + verify on a repo, then spawn one explore subagent per
  top-level module in parallel to produce module summaries grounded in facts.json.
  Merge all summaries into ONBOARDING.md and link report.html.
---
```

Steps defined in the skill:
1. Run `devpilot scan <repo>` — produces `.devpilot/facts.json`
2. Run `devpilot verify <repo>` — produces `.devpilot/verify.json`
3. List top-level modules from `facts.json` (Python packages with `__init__.py` or top-level `.py` files)
4. Spawn one `explore` subagent **per module** in parallel; each returns:
   - Purpose (one paragraph)
   - Key files with `file:line` citations
   - Public entry points (functions/classes used by other modules)
   - How it connects to other modules
   - Known gotchas (from `todos` and `findings`)
5. Merge all subagent results into `ONBOARDING.md` with sections:
   - Overview, Architecture, Setup (from verify.json passed steps), Env vars,
     Drift warnings, Module guide, Who to ask, First 5 tasks, Glossary
6. Run `devpilot report <repo>` and add link to `report.html` at top of `ONBOARDING.md`

---

## Risk register

| Rank | Risk | Mitigation |
|---|---|---|
| 1 | `git log` subprocess fails on non-git repos | Catch `CalledProcessError`; return `[]`; tested in `test_scan_git_history.py` |
| 2 | `pypdf` fails on encrypted/malformed PDFs | Wrap in try/except; skip silently; log warning |
| 3 | `ast.parse` fails on Python 2 syntax in scanned repo | Catch `SyntaxError`; fall back to line-by-line regex |
| 4 | Drift D2/D3 produces false positives on repos with identical commands | Normalize whitespace and strip flags before comparison; validated against Flask sample |
| 5 | `devpilot verify` hangs if a setup step never exits | `subprocess.run(timeout=300)` raises `TimeoutExpired`; captured as `passed=False` |
| 6 | HTML report too large (> 5 MB) for big repos | Cap `output_tail` at 40 lines; truncate todos list to top-50; truncate hotspots to top-20 |
| 7 | 2-day hackathon time crunch | Cut Phase 6 (ask) first if needed; Phases 3, 4, 8 carry the core story |

---

## Parallelism map (for Bob subagent dispatch)

| Parallel group | Phases |
|---|---|
| Wave A | Phase 3 subagents: all 9 scanners simultaneously |
| Wave B | Phases 4 + 5 + 6 (after Phase 3) |
| Wave C | Phase 7 (after Phases 4 + 5) |
| Sequential | Phase 8 → 9 → 10 |
