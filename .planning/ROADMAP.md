# DevPilot — Roadmap

## Milestone 1 (current) — Foundation

> Build the project skeleton, test oracle, and dependency contract.
> All later phases build on this foundation.

### Phase 1 — Plan
**Status:** `[ ] pending`
**Mode:** Plan
**Bob feature:** Plan mode + document understanding
**Deliverable:** `docs/PLAN.md` — ordered milestones, scanner specs, fixture spec with expected D1–D6 findings, parallelism map, risks

**UAT:**
- [ ] `docs/PLAN.md` exists
- [ ] Fixture section lists the exact expected D1–D6 findings
- [ ] Parallelism map identifies which milestones can run in parallel

---

### Phase 2 — Scaffold + Test Oracle
**Status:** `[ ] pending`
**Mode:** Agent
**Bob feature:** Plan→Agent handoff, command execution
**Deliverable:** Working package skeleton, `tiny_repo` fixture, CLI stubs, passing smoke test

**Tasks:**
- `pyproject.toml` with src layout, console script, runtime deps (typer, jinja2, pyyaml, pypdf), dev deps (pytest, ruff)
- `src/devpilot/models.py` — dataclasses for `Facts`, `Finding`, `VerifyStep`
- `src/devpilot/cli.py` — stub commands: scan / verify / ask / report
- `tests/fixtures/tiny_repo/` — hand-built with intentional D1–D6 drift per REQUIREMENTS.md
- `tests/test_cli.py` — smoke test: `devpilot --help`, each subcommand returns without error
- `scripts/fetch_sample.sh` — shallow-clones `pallets/flask @ 3.1.0` into `data/sample_repo`
- `data/onboarding_questions.md` — 10 benchmark questions from REQUIREMENTS.md

**UAT:**
- [ ] `pytest -q` passes (zero failures)
- [ ] `devpilot --help` lists scan, verify, ask, report
- [ ] `ruff check .` passes with zero warnings
- [ ] `tests/fixtures/tiny_repo/` contains one instance of each drift rule D1–D6

---

### Phase 3 — Scanners (parallel subagents ⭐)
**Status:** `[ ] pending`
**Mode:** Agent
**Bob feature:** Parallel `general` subagents
**Deliverable:** All 9 scanners implemented, tested, and wired into `devpilot scan`

**Scanners** (each dispatched to its own subagent):
1. `scan/languages.py`
2. `scan/deps.py`
3. `scan/entrypoints.py`
4. `scan/envvars.py`
5. `scan/ci.py`
6. `scan/git_history.py`
7. `scan/owners.py`
8. `scan/todos.py`
9. `scan/docs_inventory.py`

**Each subagent contract:**
- Implement `scan_<name>(repo: Path) -> list[Model]` as a pure function
- Write `tests/test_scan_<name>.py` asserting exact expected facts for `tiny_repo`
- Run its own test file until green
- Not edit any file outside its scanner module and its test

**UAT:**
- [ ] Subagent panel shows 9 completed
- [ ] `pytest -q` is green (all scanner tests pass)
- [ ] `devpilot scan tests/fixtures/tiny_repo` writes `.devpilot/facts.json`
- [ ] `ruff check .` passes
- [ ] 📸 Screenshot subagent panel → `bob_sessions/screenshots/03-subagents.png`

---

### Phase 4 — Doc-Drift Detection
**Status:** `[ ] pending`
**Mode:** Agent
**Bob feature:** Document understanding (reads real OSS docs to verify rules)
**Deliverable:** `src/devpilot/drift.py` (D1–D6), `docs/DRIFT_REVIEW.md`

**Tasks:**
- Implement D1–D6 in `drift.py`; each finding has `id`, `severity`, `message`, `evidence: ["path:line", ...]`
- Test against `tiny_repo` — findings must match oracle in `docs/PLAN.md` exactly
- Run `bash scripts/fetch_sample.sh` then `devpilot scan data/sample_repo`
- Hand-check every finding against real Flask docs; label TRUE POSITIVE / FALSE POSITIVE
- Write `docs/DRIFT_REVIEW.md` with labels and precision figure (TP / total)

**UAT:**
- [ ] `test_drift.py` passes with exact expected findings
- [ ] `docs/DRIFT_REVIEW.md` exists with a precision figure

---

### Phase 5 — Setup Verification
**Status:** `[ ] pending`
**Mode:** Agent
**Deliverable:** `src/devpilot/verify.py`, `devpilot verify` command, `verify.json`

**Tasks:**
- Derive steps from `facts.ci_commands` (preferred) or docs (fallback)
- Run in fresh temp venv, per-step timeout (default 300 s), capture exit code + duration + last 40 lines
- Deny-list: blocks `sudo`, `rm -rf /`, `curl|sh`, anything touching secrets
- Test with a fixture whose test step deliberately fails
- Run on `data/sample_repo` and report results

**UAT:**
- [ ] `test_verify.py` passes (including deny-list adversarial test)
- [ ] `devpilot verify tests/fixtures/tiny_repo` writes `verify.json`
- [ ] `ruff check .` passes

---

### Phase 6 — `devpilot ask`
**Status:** `[ ] pending`
**Mode:** Agent
**Deliverable:** `src/devpilot/search.py`, `devpilot ask` command, `docs/ASK_EVAL.md`

**Tasks:**
- Chunk code by function/class (AST for Python) and docs by heading
- Self-written BM25 ranker; no external service, fully offline
- `devpilot ask <repo> "question"` prints top 5 chunks with `file:line`
- Test with 3 known Q→file pairs against `tiny_repo`
- Run all 10 benchmark questions against `data/sample_repo`; record hit rate in `docs/ASK_EVAL.md`

**UAT:**
- [ ] `test_search.py` passes (3 known Q→file assertions)
- [ ] `docs/ASK_EVAL.md` shows ≥ 7/10 questions where correct file is in top-3
- [ ] `ruff check .` passes

---

### Phase 7 — HTML Report
**Status:** `[ ] pending`
**Mode:** Agent
**Deliverable:** `src/devpilot/report/`, `report.html` for `data/sample_repo`

**Tasks:**
- Jinja2 template rendering `facts.json` + `findings.json` + `verify.json` into a single self-contained HTML
- Summary cards, Mermaid architecture diagram, setup guide (passed steps only), drift table, owner map, top-5 first tasks
- Light and dark mode
- Generate report for `data/sample_repo` and open it

**UAT:**
- [ ] `devpilot report data/sample_repo` produces `report.html` with no template errors
- [ ] All six sections present in the HTML
- [ ] 📸 Screenshot the report → `bob_sessions/screenshots/07-report.png`
- [ ] `ruff check .` passes

---

### Phase 8 — IBM Bob Onboarding Kit ⭐
**Status:** `[ ] pending`
**Mode:** Agent (kit creation) → Onboarding Guide mode (product run)
**Bob feature:** Custom mode, mode rules, skills, parallel `explore` subagents
**Deliverable:** `.bob/` kit, `data/sample_repo/ONBOARDING.md`

**Tasks (8a — create the kit):**
- `.bob/custom_modes.yaml` with `onboarding-guide` mode (see REQUIREMENTS FR-7)
- `.bob/rules-onboarding-guide/01-grounding.md` — grounding rules
- `.bob/skills/onboard-repo/SKILL.md` + `ONBOARDING.md` template

**Tasks (8b — run the product):**
- Switch to 🧭 Onboarding Guide mode; prompt: "I'm new to the repo at data/sample_repo. Onboard me."
- Approve N parallel `explore` subagents (one per Flask module)
- `data/sample_repo/ONBOARDING.md` produced

**Tasks (8c — spot-check):**
- Verify 10 random citations in `ONBOARDING.md` against source; report any wrong/unsupported claims

**UAT:**
- [ ] `.bob/` kit files exist
- [ ] `data/sample_repo/ONBOARDING.md` generated with all required sections
- [ ] All citations in `ONBOARDING.md` verified — no uncited commands
- [ ] 📸 Screenshot parallel explore subagents → `bob_sessions/screenshots/08-explore-subagents.png`

---

### Phase 9 — Measure Impact
**Status:** `[ ] pending`
**Mode:** Agent (doc generation) + manual measurement
**Deliverable:** `docs/IMPACT.md` with measured (not estimated) numbers

**Tasks:**
- Manual baseline: fresh clone, stopwatch, get tests passing, answer 10 questions
- With DevPilot: repeat with Phase 8b flow
- Ask Bob to create `docs/IMPACT.md` from measured numbers only
- Include precision from `DRIFT_REVIEW.md`, hit-rate from `ASK_EVAL.md`, subagent wall-clock from Phase 3/8

**UAT:**
- [ ] `docs/IMPACT.md` exists with all table cells filled (no blanks or estimates)
- [ ] 📸 Screenshot Bobalytics → `bob_sessions/screenshots/09-bobalytics.png`

---

### Phase 10 — Package the Submission
**Status:** `[ ] pending`
**Mode:** Agent
**Deliverable:** Final `README.md`, `docs/DEMO_SCRIPT.md`, security scan

**Tasks:**
- Replace placeholder `README.md` with: problem (2 lines), solution, 60-second quickstart,
  architecture diagram, Bob 2.0 features used, headline impact numbers from `IMPACT.md`, limitations
- Write `docs/DEMO_SCRIPT.md` — 3-minute video script showing before/after
- Scan repo + `bob_sessions/` for secrets or API keys

**UAT:**
- [ ] `README.md` has all required sections
- [ ] `docs/DEMO_SCRIPT.md` exists and is ≤ 3 minutes when read aloud at a comfortable pace
- [ ] Security scan returns no secrets or API keys

---

## Parallelism map

Phases 3 (scanners) and later are the most parallelizable:
- **Phase 3:** 9 subagents in parallel, one per scanner
- **Phase 8:** N subagents in parallel, one per Flask top-level module

Phases with dependencies:
- Phase 3 depends on Phase 2 (models + fixture)
- Phase 4 depends on Phase 3 (scan must run first)
- Phase 5 depends on Phase 3 (ci_commands from facts)
- Phase 7 depends on Phases 4 + 5 (reads findings + verify JSON)
- Phase 8 depends on Phases 4 + 5 + 7 (all three commands must work)
- Phase 9 depends on Phase 8 (needs the full product)
- Phase 10 depends on Phase 9 (needs impact numbers)

## 2-day schedule

| Block | Phases |
|---|---|
| Day 1 AM | 0 (manual setup), 1 (plan) |
| Day 1 PM | 2 (scaffold), 3 (scanners) |
| Day 2 AM | 4 (drift), 5 (verify), 6 (ask) |
| Day 2 PM | 7 (report), 8 (Bob kit), 9 (impact), 10 (package) |

**If time is short:** cut Phase 6 first, then Phase 5. Phases 3, 4, 8, 9 carry the story.
