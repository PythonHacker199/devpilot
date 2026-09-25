# DevPilot — Project Context

## What we are building

DevPilot turns an unfamiliar repository into a **verified onboarding kit** in minutes.
It solves the problem that most onboarding knowledge already exists in the repo (code, CI,
git history, docs) but a new developer has to find, reconcile, and verify it by hand.

## Core value proposition

- A **deterministic Python CLI** (`devpilot`) extracts facts: languages, deps, entry points,
  env vars, CI commands, git hotspots, owners, TODOs, and a docs inventory.
- **Doc-drift detection** cross-checks docs against reality (e.g. README install command
  vs CI install command; env vars read in code but documented nowhere).
- **Setup verification** runs detected setup and test commands in an isolated temp venv
  and reports what breaks before a new hire hits it.
- **IBM Bob layer** — an "Onboarding Guide" custom mode + `onboard-repo` skill that fans
  out parallel `explore` subagents (one per module) to write grounded module summaries,
  then merges them into `ONBOARDING.md` + `report.html`.
- **`devpilot ask`** answers onboarding questions offline with `file:line` citations (BM25).

## Guiding principles

- **Facts are computed, prose is generated.** Bob never invents a command, path, or env var.
  Every claim in `ONBOARDING.md` traces back to `facts.json` or a `file:line`.
- Scanners are **pure functions** — no global state, no network calls, no side effects.
- Code never executes inside a repo except in `verify.py`, and only inside a temp venv.
- Python 3.11+, type hints everywhere, `ruff`-clean, no function over ~40 lines.

## Target users

New developers (and returning contributors) joining an unfamiliar Python/JS/TS project.
Secondary user: the senior developer who wants drift warnings without reading every CI diff.

## Tech stack

- **Language:** Python 3.11+
- **CLI framework:** Typer
- **Templating:** Jinja2
- **Config/data:** PyYAML, dataclasses
- **PDF reading:** pypdf
- **Search:** self-written BM25 (no external service)
- **Testing:** pytest
- **Linting:** ruff
- **Bob:** custom mode (`onboarding-guide`), mode rules, skill (`onboard-repo`)
- **No** network calls at runtime, no API keys required

## Repository layout

```
src/devpilot/           Python package
  cli.py                Typer app (scan/verify/ask/report)
  models.py             Dataclasses: Facts, Finding, VerifyStep
  scan/                 Nine pure-function scanners
  drift.py              D1–D6 cross-check rules → findings
  verify.py             Isolated temp-venv execution
  search.py             BM25 chunker + ranker
  report/               Jinja2 HTML renderer
tests/
  fixtures/tiny_repo/   Hand-built repo with known D1–D6 drift (test oracle)
  test_scan_*.py, test_drift.py, test_verify.py, test_search.py, test_cli.py
data/
  onboarding_questions.md   Fixed 10-question benchmark
  sample_repo/              OSS repo fetched by script (git-ignored)
scripts/fetch_sample.sh     Shallow-clones pallets/flask @ 3.1.0
.bob/
  custom_modes.yaml         "Onboarding Guide" mode
  rules-onboarding-guide/   Grounding rules
  skills/onboard-repo/      SKILL.md + ONBOARDING.md template
docs/
  PLAN.md, DRIFT_REVIEW.md, ASK_EVAL.md, IMPACT.md, DEMO_SCRIPT.md
bob_sessions/               Exported Bob session transcripts (evidence)
```

## Impact metrics (to be measured in Phase 9)

| Metric | Baseline | With DevPilot |
|---|---|---|
| Time to first passing local test run | stopwatch | stopwatch |
| Time to answer 10 standard onboarding questions | stopwatch | stopwatch |
| Setup errors encountered | count | count |
| Doc-drift issues found | 0 (unknown) | devpilot scan count |
| Answer accuracy (Q→right file in top-3) | n/10 | n/10 |

## Out of scope (prototype)

- Private-repo auth, multi-repo monorepo federation, Slack integrations
- Deep scanning of languages other than Python and JS/TS (others get shallow scan)

## Key documents

- `docs/PROBLEM.md` — full problem statement and solution description
- `docs/DESIGN.md` — architecture, CLI spec, package layout, drift rules, data models
- `docs/BOB_PLAYBOOK.md` — 10-phase build playbook with Bob prompts and done checks
