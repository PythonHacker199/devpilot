# DevPilot

> A developer joins a team. The README is stale, the env vars are undocumented, and the first
> `pytest` fails because CI uses a different install command. **DevPilot fixes this before the
> new hire even clones the repo.**

DevPilot turns an unfamiliar repository into a **verified onboarding kit** in under 60 seconds:
facts extracted from code, CI, and git history; doc-drift warnings; a tested setup guide; and
an IBM Bob–generated `ONBOARDING.md` with module summaries, owner map, and ranked first tasks.

---

## 60-second quickstart

```bash
# 1. Install
pip install devpilot

# 2. Scan any repo — extracts facts, detects doc drift
devpilot scan path/to/repo

# 3. Verify setup — runs CI commands in an isolated venv, records what breaks
devpilot verify path/to/repo

# 4. Ask onboarding questions offline
devpilot ask path/to/repo "What environment variables are required?"

# 5. Generate the HTML report + ONBOARDING.md skeleton
devpilot report path/to/repo
# → path/to/repo/.devpilot/report.html
# → path/to/repo/.devpilot/ONBOARDING.md

# 6. Switch Bob to 🧭 Onboarding Guide mode and run the skill
# "I'm new to the repo at path/to/repo. Onboard me."
# Bob fans out explore subagents (one per module) and produces ONBOARDING.md
```

---

## Architecture

```
         ┌──────────── deterministic (Python CLI) ────────────┐
repo ──►  scan ──► facts.json ──► drift ──► findings.json      │
         │         verify ──────────────► verify.json          │
         └────────────────────────────────────────────────────┘
                              │
         ┌────── AI reasoning (IBM Bob, Onboarding Guide mode) ─┐
         │  onboard-repo skill:                                  │
         │   1. devpilot scan + devpilot verify                  │
         │   2. explore subagents IN PARALLEL (1 per module) ───►│ module summaries
         │   3. merge → ONBOARDING.md                            │
         │   4. devpilot report → report.html                    │
         └───────────────────────────────────────────────────────┘
```

**Principle: facts are computed, prose is generated.**
Bob never invents a command, path, or env var. Every claim in `ONBOARDING.md` traces back
to `facts.json` or a `file:line`.

---

## How IBM Bob 2.0 is used

| Feature | Where |
|---|---|
| **Plan mode + document understanding** | Phase 1: Bob reads `DESIGN.md` + `PROBLEM.md` to produce `docs/PLAN.md` |
| **Parallel `general` subagents** | Phase 3: 9 scanners built simultaneously, one subagent each |
| **Custom mode** | `.bob/custom_modes.yaml` — "🧭 Onboarding Guide" with restricted edit access |
| **Mode rules** | `.bob/rules-onboarding-guide/01-grounding.md` — enforces citation discipline |
| **Skill** | `.bob/skills/onboard-repo/SKILL.md` — 5-step onboarding workflow |
| **Parallel `explore` subagents** | Step 3 of the skill: one subagent per module, all in parallel |
| **Command execution** | `devpilot scan`, `verify`, `report` all invoked by Bob during the skill run |

---

## What gets detected

### Doc-drift rules

| ID | Severity | Example |
|---|---|---|
| D1 | high | `SECRET_KEY` read in `app.py` but not in any doc or `.env.example` |
| D2 | high | README says `pip install -r requirements.txt`; CI runs `pip install -e .[dev]` |
| D3 | medium | README says `python -m pytest`; CI runs `pytest -v` |
| D4 | medium | README links to `docs/setup_guide.md` which does not exist |
| D5 | medium | README says "Python 3.9+"; `pyproject.toml` requires `>=3.11` |
| D6 | low | README mentions `mytool` CLI; no `console_scripts` entry in `pyproject.toml` |

### Nine scanners

Languages · Deps · Entry points · Env vars · CI commands · Git hotspots · Owners · TODOs · Docs inventory

---

## Impact (Phase 9 — to be measured)

| Metric | Baseline (manual) | With DevPilot |
|---|---|---|
| Time to first passing local test run | _stopwatch_ | _stopwatch_ |
| Time to answer 10 standard onboarding questions | _stopwatch_ | _stopwatch_ |
| Setup errors encountered | _count_ | _count_ |
| Doc-drift issues found | 0 (unknown) | `devpilot scan` count |
| Answer accuracy (correct file in top-3) | _n/10_ | _n/10_ |

> Numbers are measured, not estimated. See `docs/IMPACT.md` after Phase 9.

---

## Limitations

- Deep scanning covers Python and JS/TS; other languages get a language-LOC count only.
- `devpilot verify` runs real install/test commands — requires Python and the target toolchain present.
- `devpilot ask` uses BM25 (keyword match); semantic search is not implemented in this prototype.
- Private-repo auth, monorepo federation, and Slack integrations are out of scope.
- Phase 9 (impact measurement) requires manual stopwatch runs; those numbers are not auto-generated.

---

## Development

```bash
# Install with dev deps
pip install -e ".[dev]"

# Run tests
pytest -q

# Lint
ruff check .

# Fetch the sample repo (pallets/flask @ 3.1.0)
bash scripts/fetch_sample.sh
```

See [`docs/BOB_PLAYBOOK.md`](docs/BOB_PLAYBOOK.md) for the full 10-phase build walkthrough.
