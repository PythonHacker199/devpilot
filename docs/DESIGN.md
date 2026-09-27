# DevPilot — Design

## Architecture

```
            ┌──────────────────────── deterministic (Python CLI) ────────────────────────┐
 repo ──►   scan ──► facts.json ──► drift ──► findings.json ──► verify ──► verify.json   │
            └────────────────────────────────────────────────────────────────────────────┘
                                         │
            ┌───────────────── AI reasoning (IBM Bob, "Onboarding Guide" mode) ──────────┐
            │  onboard-repo skill:                                                        │
            │   1. run `devpilot scan` + `devpilot verify`                                │
            │   2. spawn explore subagents IN PARALLEL, one per top-level module ────────►│ module summaries
            │   3. merge summaries + facts → ONBOARDING.md                                │
            │   4. `devpilot report` → report.html                                        │
            └─────────────────────────────────────────────────────────────────────────────┘
```

Principle: **facts are computed, prose is generated.** Bob never invents a command, path, or
env var. Every claim in `ONBOARDING.md` must trace back to `facts.json` or a `file:line`.
This is what makes the output trustworthy enough to hand to a new hire.

## CLI

| Command | Output | Notes |
|---|---|---|
| `devpilot scan <repo> [-o .devpilot/]` | `facts.json`, `findings.json` | Pure, offline, < 30 s on a mid-sized repo |
| `devpilot verify <repo>` | `verify.json` | Runs setup and test commands in a temp venv, with a timeout per step |
| `devpilot ask <repo> "question"` | Ranked snippets with `file:line` | BM25 over code and doc chunks; offline |
| `devpilot report <repo>` | `report.html`, `ONBOARDING.md` skeleton | Jinja2 template; Mermaid diagram |

## Package layout

```
src/devpilot/
  cli.py                 # Typer app
  models.py              # dataclasses for Facts, Finding, VerifyStep
  scan/
    languages.py         # LOC by extension
    deps.py              # pyproject / requirements*.txt / package.json
    entrypoints.py       # console_scripts, __main__, manage.py, Dockerfile CMD, package.json scripts
    envvars.py           # os.environ / getenv / process.env + .env.example
    ci.py                # .github/workflows/*.yml → `run:` steps (the ground-truth setup)
    git_history.py       # hotspots: most-changed files, last 90 days
    owners.py            # CODEOWNERS, else top committers per directory
    todos.py             # TODO/FIXME/HACK with file:line
    docs_inventory.py    # README, CONTRIBUTING, docs/**/*.md, *.pdf (text via pypdf)
  drift.py               # cross-checks → findings
  verify.py              # isolated execution of setup/test commands
  search.py              # chunker + BM25 (no external service)
  report/
    render.py
    templates/report.html.j2
tests/
  fixtures/tiny_repo/    # hand-built repo with KNOWN drift, used as the test oracle
  test_scan_*.py, test_drift.py, test_verify.py, test_search.py, test_cli.py
data/
  onboarding_questions.md   # fixed 10-question benchmark
  sample_repo/              # real OSS repo, fetched by script, git-ignored
scripts/fetch_sample.sh     # clones the pinned sample repo
.bob/
  custom_modes.yaml         # "Onboarding Guide" mode
  rules-onboarding-guide/   # grounding rules for that mode
  skills/onboard-repo/SKILL.md
```

Dependencies: `typer`, `jinja2`, `pyyaml`, `pypdf`, plus `pytest` for dev. No network calls
at runtime, no API keys.

## `facts.json` shape (synthetic example)

```json
{
  "repo": "sample_repo",
  "scanned_at": "2026-09-25T14:03:00Z",
  "languages": [{"name": "Python", "files": 84, "loc": 12450}],
  "deps": {"manager": "pip", "files": ["pyproject.toml"], "runtime": ["click>=8.1"], "dev": ["pytest"]},
  "entrypoints": [{"kind": "console_script", "name": "flask", "target": "flask.cli:main", "source": "pyproject.toml:45"}],
  "env_vars": [{"name": "FLASK_APP", "read_at": ["src/flask/cli.py:320"], "documented_in": ["docs/cli.rst:14"]}],
  "ci_commands": [{"workflow": ".github/workflows/tests.yaml", "step": "Run tests", "run": "pytest -v", "line": 41}],
  "hotspots": [{"path": "src/flask/app.py", "commits_90d": 17}],
  "owners": [{"path": "src/flask/", "owners": ["@maintainer-a"], "source": "git-authors"}],
  "todos": [{"file": "src/flask/helpers.py", "line": 210, "text": "TODO: deprecate in 4.0"}],
  "docs": [{"path": "README.md", "kind": "readme", "commands": ["pip install -U Flask"]}]
}
```

## Drift rules (v1)

| ID | Rule | Severity |
|---|---|---|
| D1 | Env var read in code but not in any doc or `.env.example` | high |
| D2 | Install command in docs differs from the CI install step | high |
| D3 | Test command in docs differs from the CI test step | medium |
| D4 | Doc references a file path that doesn't exist | medium |
| D5 | Python version in docs is outside `requires-python` / CI matrix | medium |
| D6 | Entry point documented but not declared (or vice versa) | low |

Every finding carries `evidence: ["path:line", ...]` for both sides of the contradiction.

## First-task ranking

Candidate = TODO/FIXME or a hotspot-adjacent small file. Score = small file size
+ has tests nearby + not in a hotspot (low merge-conflict risk) + has an owner. The top 5 go into
`ONBOARDING.md` with a reason for each.

## Conventions (Bob: follow these)

- Python 3.11+, type hints everywhere, `ruff`-clean, and no function over ~40 lines.
- Scanners are **pure functions** `scan_x(repo: Path) -> list[Model]`, with no global state.
- Every scanner has a test against `tests/fixtures/tiny_repo` that asserts **exact** expected facts.
- Never execute repo code except in `verify.py`, and only inside a temp venv with timeouts.
- Paths in output are repo-relative and use POSIX separators, so Windows paths are normalized.
