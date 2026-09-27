# DevPilot — Impact Measurement

> All numbers in this file are **measured, not estimated**.
> Leave a cell blank rather than guess.
> Populate this file in Phase 9 after running both the baseline and DevPilot flows.

## Measurement conditions

- **Sample repo:** pallets/flask @ tag 3.1.0 (shallow clone, ~12k LOC Python)
- **Machine:** _(record CPU, RAM, OS)_
- **Baseline:** Fresh clone, clean venv, no DevPilot, no AI assistance
- **With DevPilot:** Fresh clone, run Phase 8b flow (Bob Onboarding Guide + onboard-repo skill)

## Results

| Metric | Baseline (manual) | With DevPilot | How measured |
|---|---|---|---|
| Time to first passing local test run | _stopwatch_ | _stopwatch_ | Start: clone completes. Stop: first green `pytest` output |
| Time to answer 10 benchmark questions | _stopwatch_ | _stopwatch_ | Questions from `data/onboarding_questions.md`; stop when all 10 have a written answer |
| Setup errors encountered | _count_ | _count_ | Log every failed command |
| Doc-drift issues found | 0 (unknown without tool) | _count from `devpilot scan`_ | `devpilot scan` findings, hand-verified (see `docs/DRIFT_REVIEW.md`) |
| Answer accuracy (correct file in top-3) | _n/10_ | _n/10_ | Checked against source; see `docs/ASK_EVAL.md` |

## Supporting metrics

| Metric | Value | Source |
|---|---|---|
| Drift detection precision | _TP / total_ | `docs/DRIFT_REVIEW.md` |
| Ask retrieval hit rate | _n/10_ | `docs/ASK_EVAL.md` |
| Phase 3 subagent wall-clock | _s_ | Bob subagent panel screenshot (`bob_sessions/screenshots/03-subagents.png`) |
| Phase 8 explore subagent wall-clock | _s_ | Bob subagent panel screenshot (`bob_sessions/screenshots/08-explore-subagents.png`) |
| ONBOARDING.md citation accuracy | _n/10 verified_ | Phase 8c spot-check |

## Notes

_(Add any observations about failures, edge cases, or surprising results here.)_
