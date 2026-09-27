# Problem Statement — Developer Onboarding

## The workflow

A developer joins a team (or picks up an unfamiliar service) and has to get from
"I have repo access" to "I merged my first meaningful change." Along the way they must:

1. Get the project running locally (install toolchain, deps, env vars, services).
2. Build a mental model of the architecture (modules, entry points, data flow).
3. Find out who owns what and where to ask.
4. Pick a first task that is small, safe, and useful.
5. Answer dozens of "where is X / how does Y work" questions.

## Where time, effort, and errors are too high

| Pain | Why it happens | Cost |
|---|---|---|
| **Setup fails on first try** | README steps are stale; the *real* commands live in CI config nobody reads | Hours of trial and error, plus interrupting senior devs |
| **Undocumented env vars / services** | Code reads `os.environ[...]` that no doc mentions | Cryptic runtime errors, rework |
| **No architecture map** | Knowledge lives in people's heads | Days of reading code linearly |
| **"Who owns this?"** | CODEOWNERS missing or stale | Wrong reviewers, stalled PRs |
| **Bad first task** | Picked by guesswork | Rework, slow first PR, lost confidence |
| **Senior-dev interruption tax** | Every question above becomes a Slack ping | Hidden cost on the whole team |

Core insight: **most of the answers already exist in the repo**, spread across code,
CI workflows, git history, and docs that contradict each other. Onboarding is slow because
a human has to find, reconcile, and verify that information by hand.

## Solution: DevPilot

DevPilot turns a repository into a **verified onboarding kit** in minutes:

- A **deterministic scanner** (Python CLI) extracts facts: languages, deps, entry points,
  env vars, CI commands, git hotspots, owners, TODOs, and a docs inventory.
- **Doc-drift detection** cross-checks docs against reality, e.g. "the README says
  `pip install -r requirements.txt` but CI runs `pip install -e .[dev]`" or "`DATABASE_URL`
  is read in `app/db.py:12` but documented nowhere."
- **Setup verification** actually runs the detected setup and test commands in an isolated
  environment and reports what breaks, *before* the new hire hits it.
- **IBM Bob layer**: an "Onboarding Guide" custom mode plus an `onboard-repo` skill.
  Bob fans out `explore` subagents **in parallel, one per module**, to write module
  summaries grounded in the scanner's facts. It then merges them into `ONBOARDING.md`
  and an HTML report with an architecture diagram, setup guide, glossary, owner map,
  and ranked first tasks.
- **`devpilot ask`** answers onboarding questions offline with `file:line` citations.

## How we will prove impact

Measured on a real open-source project (see `docs/IMPACT.md`, filled in during Phase 9):

| Metric | Baseline (manual) | With DevPilot | How measured |
|---|---|---|---|
| Time to first successful local test run | _stopwatch_ | _stopwatch_ | Fresh clone, clean venv |
| Time to answer 10 standard onboarding questions | _stopwatch_ | _stopwatch_ | Fixed question list in `data/onboarding_questions.md` |
| Setup errors encountered | _count_ | _count_ | Log every failed command |
| Doc-drift issues found | 0 (unknown) | _count_ | `devpilot scan` drift findings, hand-verified |
| Accuracy of answers | _n/10_ | _n/10_ | Checked against the source code |

> Numbers are **measured, not estimated**. Leave a cell blank rather than guess.

## Out of scope for the prototype

- Private-repo auth, multi-repo monorepo federation, and chat integrations (Slack etc.).
- Languages other than Python and JS/TS for deep scanning. Others get a shallow scan.
