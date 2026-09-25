# DevPilot — Requirements

## Functional Requirements

### FR-1: CLI — Scan
- `devpilot scan <repo> [-o .devpilot/]` writes `facts.json` and `findings.json`
- Must complete in < 30 s on a mid-sized repo (e.g. pallets/flask @ 3.1.0)
- All paths in output are repo-relative POSIX separators
- Must work offline with no API keys

### FR-2: Nine scanners (all pure functions `scan_x(repo: Path) -> list[Model]`)
- **languages** — LOC by file extension
- **deps** — pyproject.toml, requirements*.txt, package.json → manager, files, runtime, dev
- **entrypoints** — console_scripts, `__main__`, manage.py, Dockerfile CMD, package.json scripts
- **envvars** — `os.environ[...]`, `os.getenv(...)`, `process.env.*`, `.env.example`
- **ci** — `.github/workflows/*.yml` → `run:` steps (ground-truth setup commands)
- **git_history** — most-changed files in last 90 days (hotspots)
- **owners** — CODEOWNERS file, else top committers per directory
- **todos** — TODO/FIXME/HACK occurrences with `file:line`
- **docs_inventory** — README, CONTRIBUTING, `docs/**/*.md`, `*.pdf` (text via pypdf)

### FR-3: Doc-drift detection
Six rules, each producing findings with `id`, `severity`, `message`, `evidence: ["path:line", ...]`:
- **D1** (high) — Env var read in code but absent from all docs and `.env.example`
- **D2** (high) — Install command in docs differs from CI install step
- **D3** (medium) — Test command in docs differs from CI test step
- **D4** (medium) — Doc references a file path that does not exist
- **D5** (medium) — Python version in docs outside `requires-python` / CI matrix
- **D6** (low) — Entry point documented but not declared, or vice versa

### FR-4: CLI — Verify
- `devpilot verify <repo>` derives setup + test steps from `facts.ci_commands` (preferred) or docs (fallback)
- Runs each step in a fresh temp venv with a configurable per-step timeout (default 300 s)
- Captures exit code, duration, and last 40 lines of output
- Writes `.devpilot/verify.json`
- Deny-list blocks commands containing: `sudo`, `rm -rf /`, `curl|sh`, anything touching secrets

### FR-5: CLI — Ask
- `devpilot ask <repo> "question"` prints top 5 ranked chunks with `file:line`
- Chunks code by function/class (AST for Python) and docs by heading
- Ranking via self-written BM25; no external service, fully offline
- Must find the correct file in top-3 for at least 7/10 benchmark questions

### FR-6: CLI — Report
- `devpilot report <repo>` writes `report.html` (single self-contained file) and `ONBOARDING.md` skeleton
- HTML report includes:
  - Summary cards: languages, deps, setup status, drift count by severity
  - Mermaid architecture diagram of top-level modules and their imports
  - Setup guide built only from CI commands that passed in `verify.json`
  - Drift findings table with evidence links
  - Owners map
  - Top-5 ranked first tasks (score = small file + tests nearby + not a hotspot + has owner)
- Readable in light and dark mode

### FR-7: IBM Bob "Onboarding Guide" mode
- Custom mode slug `onboarding-guide`, name "🧭 Onboarding Guide"
- Role: senior engineer onboarding a new teammate to an unfamiliar repo
- Edit access restricted by `fileRegex` to `ONBOARDING\.md|\.devpilot/.*`
- Grounding rule: every command, path, env var, and owner must cite `facts.json` or a `file:line`

### FR-8: `onboard-repo` skill
- Step a: run `devpilot scan` + `devpilot verify`
- Step b: list top-level modules from `facts.json`
- Step c: spawn one `explore` subagent **per module**, in parallel
- Step d: merge results into `ONBOARDING.md` with sections: Overview, Architecture, Setup,
  Env vars, Drift warnings, Module guide, Who to ask, First 5 tasks, Glossary
- Step e: run `devpilot report` and link `report.html` from `ONBOARDING.md`

## Non-Functional Requirements

### NFR-1: Test coverage
- Every scanner has a test against `tests/fixtures/tiny_repo` asserting **exact** expected facts
- `tiny_repo` contains at least one instance of every drift rule D1–D6
- A `test_cli.py` smoke test verifies `devpilot --help` and each subcommand

### NFR-2: Code quality
- Python 3.11+, type hints on all public functions
- `ruff check .` passes with zero warnings
- No function exceeds ~40 lines

### NFR-3: Safety
- Code inside a repo is never executed except inside `verify.py`
- `verify.py` always uses a fresh temp venv with a timeout
- The deny-list in `verify.py` is tested against adversarial inputs

### NFR-4: Portability
- All repo paths in output use POSIX separators (Windows paths normalized)
- No runtime network calls, no API keys

### NFR-5: Performance
- `devpilot scan` < 30 s on pallets/flask @ 3.1.0

## Test Oracle — `tests/fixtures/tiny_repo`

The fixture is a hand-built minimal repo. It must contain **exactly one instance** of each
drift rule so tests can assert precise expected findings:

| Rule | How it's triggered in the fixture |
|---|---|
| D1 | `app.py` reads `os.environ["SECRET_KEY"]`; no `.env.example`, no doc mentions it |
| D2 | `README.md` says `pip install -r requirements.txt`; `.github/workflows/ci.yml` runs `pip install -e .[dev]` |
| D3 | `README.md` says `python -m pytest`; CI runs `pytest -v` |
| D4 | `README.md` references `docs/setup_guide.md` which does not exist |
| D5 | `README.md` says "Python 3.9+"; `pyproject.toml` has `requires-python = ">=3.11"` |
| D6 | `README.md` mentions `mytool` CLI; no `console_scripts` entry for it in `pyproject.toml` |

## Benchmark — `data/onboarding_questions.md`

Ten fixed questions for measuring `devpilot ask` retrieval accuracy and human answer speed:
1. How do I install and run the project locally?
2. What environment variables does the project require?
3. Where is the main application entry point?
4. What test framework is used and how do I run tests?
5. Which files change most frequently?
6. Who owns the core application module?
7. What third-party runtime dependencies does the project use?
8. Are there any open TODOs or known workarounds in the code?
9. What CI/CD pipeline runs on pull requests?
10. How does the project handle configuration (env vs files)?
