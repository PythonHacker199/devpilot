# DevPilot — Project State

## Current status

**Milestone:** 1 — Foundation
**Active phase:** None (ready to begin Phase 1 — Plan)
**Last completed phase:** None

## Phase completion log

| Phase | Name | Status | Completed |
|---|---|---|---|
| 0 | Manual setup (venv, sample repo choice) | `[ ] pending` | — |
| 1 | Plan | `[ ] pending` | — |
| 2 | Scaffold + Test Oracle | `[ ] pending` | — |
| 3 | Scanners (parallel subagents) | `[ ] pending` | — |
| 4 | Doc-Drift Detection | `[ ] pending` | — |
| 5 | Setup Verification | `[ ] pending` | — |
| 6 | `devpilot ask` | `[ ] pending` | — |
| 7 | HTML Report | `[ ] pending` | — |
| 8 | IBM Bob Onboarding Kit | `[ ] pending` | — |
| 9 | Measure Impact | `[ ] pending` | — |
| 10 | Package the Submission | `[ ] pending` | — |

## Key decisions

- **Sample repo:** `pallets/flask @ tag 3.1.0` (real, mid-sized, has GitHub Actions, CONTRIBUTING, Sphinx docs — enough material for drift checks)
- **No network at runtime:** all scanning and searching is offline; only `verify.py` runs code, in an isolated temp venv
- **Test oracle:** `tests/fixtures/tiny_repo` is the single ground truth for scanner and drift tests; it must trigger exactly D1–D6 with known expected facts
- **Bob grounding rule:** no command, path, or env var in `ONBOARDING.md` without a `file:line` citation

## Bob sessions evidence

Export each phase's Bob session to `bob_sessions/<NN>-<name>.md` immediately after completing it.
Screenshots go to `bob_sessions/screenshots/`.

Required screenshots:
- `00-start.png` — Bob's empty workspace (Phase 0)
- `03-subagents.png` — Subagent panel with 9 completed scanners (Phase 3)
- `07-report.png` — Generated HTML report (Phase 7)
- `08-explore-subagents.png` — Parallel explore subagents (Phase 8)
- `09-bobalytics.png` — Bobalytics showing Bobcoins and time (Phase 9)

## Blockers / open questions

None at project start.
