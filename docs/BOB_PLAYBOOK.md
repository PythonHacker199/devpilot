# Bob Playbook — building DevPilot with IBM Bob 2.0

Run each phase in Bob, in order. Each phase lists the **mode**, the **prompt to paste**, what
**Bob 2.0 feature** it demonstrates, and a **done check**. After every phase, export the
session into `bob_sessions/` (see "Evidence" at the bottom).

Bob features used, and where:

| Feature | Phases |
|---|---|
| Plan mode → Agent mode handoff | 1, 2 |
| Parallel `general` subagents (build work) | 3 |
| Parallel `explore` subagents (product runtime) | 8 |
| Document understanding (@-mentioned docs, PDFs) | 1, 4, 8 |
| Skills (`.bob/skills/`) | 8 |
| Custom mode + mode-specific rules | 8 |
| Command execution (tests, verify) | 2–10 |
| Bobalytics (Bobcoin and time evidence) | 9, 10 |

> Tips: subagents need your **approval** before they run, so watch for the prompt. Bob spawns
> them only for self-contained, multi-step tasks, which is why the prompts below split work
> into clearly independent units. If Bob does the work inline instead, reply:
> *"Please delegate each unit to a separate subagent so they run in parallel."*

---

## Phase 0 — Setup (you, ~10 min)

1. Open `C:\Users\supra\devpilot` as the workspace in Bob.
2. Create a venv: `python -m venv .venv`, then activate it.
3. Choose the sample repo. Recommended: **`pallets/flask` at tag `3.1.0`**. It's real, mid-sized,
   has GitHub Actions CI, a CONTRIBUTING guide and Sphinx docs, which is plenty of material for drift checks.
4. Screenshot Bob's empty workspace → `bob_sessions/screenshots/00-start.png`.

---

## Phase 1 — Plan (Plan mode)

**Feature:** Plan mode + document understanding.

```
Read @docs/PROBLEM.md and @docs/DESIGN.md carefully.
Produce an implementation plan for DevPilot as docs/PLAN.md:
- ordered milestones matching the package layout in DESIGN.md
- for each scanner: inputs, exact output model, edge cases, and the test that proves it
- design tests/fixtures/tiny_repo so that it contains AT LEAST one instance of every
  drift rule D1–D6, and list the exact expected findings (this is our test oracle)
- mark which milestones are independent and can be built in parallel by subagents
- risks and how we'll de-risk them in a 2-day hackathon
Do not write any code yet.
```

**Done check:** `docs/PLAN.md` exists, and its fixture section lists expected D1–D6 findings.

---

## Phase 2 — Scaffold + test oracle (Agent mode)

**Feature:** Plan→Agent handoff, command execution.

```
Implement Milestone 1 of @docs/PLAN.md:
- pyproject.toml (src layout, package "devpilot", console script `devpilot = devpilot.cli:app`,
  deps: typer, jinja2, pyyaml, pypdf; dev: pytest, ruff)
- src/devpilot/models.py with the dataclasses from DESIGN.md
- src/devpilot/cli.py with stub commands scan/verify/ask/report
- tests/fixtures/tiny_repo exactly as specified in PLAN.md (with its intentional drift)
- tests/test_cli.py smoke test
- scripts/fetch_sample.sh that shallow-clones pallets/flask at tag 3.1.0 into data/sample_repo
- data/onboarding_questions.md with the 10 benchmark questions from PLAN.md
Then run: pip install -e ".[dev]" && pytest -q && ruff check .
Fix until green.
```

**Done check:** `pytest -q` passes and `devpilot --help` works.

---

## Phase 3 — Scanners in parallel (Agent mode) ⭐

**Feature:** parallel `general` subagents. This is the headline demo of the build process.

```
Implement the nine scanners from @docs/DESIGN.md. Each one is independent and self-contained,
so delegate each to its own general subagent and run them in parallel:

  1. scan/languages.py        2. scan/deps.py           3. scan/entrypoints.py
  4. scan/envvars.py          5. scan/ci.py             6. scan/git_history.py
  7. scan/owners.py           8. scan/todos.py          9. scan/docs_inventory.py

Each subagent must:
- implement `scan_<name>(repo: Path) -> list[Model]` as a pure function, per DESIGN.md conventions
- write tests/test_scan_<name>.py asserting the EXACT expected facts for tests/fixtures/tiny_repo
  (from docs/PLAN.md)
- run its own test file until green and report the result
- NOT edit any file outside its scanner module and its test

When all subagents finish, wire them into `devpilot scan` so it writes .devpilot/facts.json,
then run the full test suite and ruff.
```

**Done check:** subagent panel shows 9 completed; `pytest -q` is green;
`devpilot scan tests/fixtures/tiny_repo` writes `facts.json`.
📸 Screenshot the subagent panel (count, tokens, elapsed time) → `bob_sessions/screenshots/03-subagents.png`.

---

## Phase 4 — Doc-drift detection (Agent mode)

**Feature:** document understanding. Bob reasons over real docs to tune the rules.

```
Implement src/devpilot/drift.py with rules D1–D6 from @docs/DESIGN.md. Each finding needs
id, severity, message, and evidence ["path:line", ...] for BOTH sides of the contradiction.
Test against tests/fixtures/tiny_repo: the findings must match the oracle in docs/PLAN.md exactly.

Then run `bash scripts/fetch_sample.sh` and `devpilot scan data/sample_repo`.
Read @data/sample_repo/README.md, @data/sample_repo/CONTRIBUTING.rst and the CI workflows,
and hand-check every finding. For each one, label it TRUE POSITIVE or FALSE POSITIVE in
docs/DRIFT_REVIEW.md. Fix the rules to remove false positives, but don't overfit to Flask.
```

**Done check:** `docs/DRIFT_REVIEW.md` exists with a precision figure (TP / total).

---

## Phase 5 — Setup verification (Agent mode)

```
Implement src/devpilot/verify.py and `devpilot verify <repo>`:
- derive setup + test steps from facts.ci_commands (preferred) or docs (fallback)
- run them in a fresh temp venv with a per-step timeout (default 300s), capturing
  exit code, duration, and the last 40 lines of output
- never run commands containing: sudo, rm -rf /, curl|sh, or anything touching secrets
  (keep a deny-list and test it)
- write .devpilot/verify.json
Test with a tiny fixture whose test step deliberately fails. Then run it on data/sample_repo
and report the results.
```

---

## Phase 6 — `devpilot ask` (Agent mode)

```
Implement src/devpilot/search.py: chunk code by function/class (ast for Python) and docs by
heading, then rank with a small self-written BM25. `devpilot ask <repo> "question"` prints the
top 5 chunks with file:line. Test on the fixture with 3 known Q→file answers. Then run all
10 questions in @data/onboarding_questions.md against data/sample_repo and record, for each,
whether the top-3 contains the right file in docs/ASK_EVAL.md.
```

---

## Phase 7 — HTML report (Agent mode)

```
Implement src/devpilot/report/ with a Jinja2 template that renders report.html from
facts.json + findings.json + verify.json:
- summary cards (languages, deps, setup status, drift count by severity)
- a Mermaid architecture diagram of top-level modules and their imports
- setup guide built ONLY from CI commands that passed in verify.json
- drift findings table with evidence links
- owners map and top-5 ranked first tasks (ranking per DESIGN.md)
It must be a single self-contained HTML file, readable in light and dark mode.
Generate it for data/sample_repo and open it.
```

📸 Screenshot the report → `bob_sessions/screenshots/07-report.png`.

---

## Phase 8 — The Bob-native onboarding workflow (Agent mode → Onboarding Guide mode) ⭐

**Feature:** custom mode, mode rules, skills, and parallel `explore` subagents **as part of the product**.

**8a. Have Bob create the kit (Agent mode):**

```
Create the IBM Bob onboarding kit for this project:

1. .bob/custom_modes.yaml with a mode:
   slug: onboarding-guide
   name: 🧭 Onboarding Guide
   roleDefinition: a senior engineer onboarding a new teammate to an unfamiliar repo
   whenToUse: when someone needs to understand, set up, or start contributing to a repo
   groups: read, execute, skill, subagent, todo, and edit restricted by fileRegex to
     ONBOARDING\.md|\.devpilot/.*
2. .bob/rules-onboarding-guide/01-grounding.md:
   - every command, path, env var, and owner must come from .devpilot/facts.json or a cited file:line
   - if unsure, write "UNVERIFIED" instead of guessing
   - setup steps come only from verify.json steps that passed
3. .bob/skills/onboard-repo/SKILL.md (name + description frontmatter) with these steps:
   a. run `devpilot scan <repo>` and `devpilot verify <repo>`
   b. list the top-level modules from facts.json
   c. spawn one explore subagent PER MODULE, in parallel, each returning: purpose,
      key files, public entry points, how it connects to other modules, and gotchas,
      all with file:line citations
   d. merge the results into ONBOARDING.md (Overview, Architecture, Setup, Env vars, Drift
      warnings, Module guide, Who to ask, First 5 tasks, Glossary)
   e. run `devpilot report <repo>` and link report.html from ONBOARDING.md
   Put a template for ONBOARDING.md next to SKILL.md.
```

**8b. Run the product (switch to 🧭 Onboarding Guide mode, new chat):**

```
I'm new to the repo at data/sample_repo. Onboard me.
```

**Done check:** you approve N parallel explore subagents (one per Flask module), and
`data/sample_repo/ONBOARDING.md` has citations throughout with no uncited commands.
📸 Screenshot the parallel explore subagents → `bob_sessions/screenshots/08-explore-subagents.png`.

**8c. Spot-check (Ask mode):**

```
Check @data/sample_repo/ONBOARDING.md against the source. Pick 10 random claims with
citations and verify each one. Report any that are wrong or unsupported.
```

---

## Phase 9 — Measure impact (you + Bob, Agent mode)

1. **Baseline (manual, no DevPilot, no AI).** Clone Flask fresh. Start a stopwatch. Get tests
   passing, then answer the 10 questions in `data/onboarding_questions.md`. Log every failed
   command. *(Ideally a teammate who hasn't seen Flask does this.)*
2. **With DevPilot.** Fresh clone, run the Phase 8b flow, and repeat the same tasks.
3. Then ask Bob:

```
Create docs/IMPACT.md from my measurements below. Fill the table from @docs/PROBLEM.md
using ONLY these numbers. Include precision from docs/DRIFT_REVIEW.md, the retrieval hit-rate
from docs/ASK_EVAL.md, and the subagent wall-clock from Phase 3/8. Don't invent any figure.
<paste your stopwatch times, error counts, and answer accuracy here>
```

📸 Screenshot Bobalytics (Bobcoins, time) → `bob_sessions/screenshots/09-bobalytics.png`.

---

## Phase 10 — Package the submission (Agent mode)

```
Write README.md: the problem (2 lines), the solution, a 60-second quickstart
(install → scan → verify → onboard with Bob), an architecture diagram, how Bob 2.0 is used
(modes, subagents, skills, doc understanding), the headline impact numbers from
@docs/IMPACT.md, and limitations. Then write docs/DEMO_SCRIPT.md, a 3-minute video script
showing the before/after. Finally, scan the repo and bob_sessions/ for secrets or API keys
and report anything found.
```

---

## Evidence for judges (`bob_sessions/`)

After **each** phase: in Bob's chat, open **Views and More Actions → History**, confirm the
workspace is `devpilot`, and export the task. Save it as:

```
bob_sessions/
  01-plan.md
  02-scaffold.md
  03-parallel-scanners.md
  04-drift.md
  05-verify.md
  06-ask.md
  07-report.md
  08-onboarding-kit-and-run.md
  09-impact.md
  10-packaging.md
  screenshots/
```

Before pushing, **remove any credentials or API keys** from both the code and the exported sessions.

## Suggested 2-day schedule

| Block | Phases |
|---|---|
| Day 1 AM | 0, 1, 2 |
| Day 1 PM | 3, 4 |
| Day 2 AM | 5, 6, 7 |
| Day 2 PM | 8, 9, 10, then record the demo |

If time runs short, cut Phase 6 (`ask`) first, then Phase 5. Phases 3, 4, 8 and 9 carry the story.
