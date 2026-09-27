# DevPilot — Drift Review

## Sample repo: pallets/flask @ 3.1.0

This file will be populated in Phase 4 after running `devpilot scan data/sample_repo`
and hand-checking each finding against the Flask source, README, and CONTRIBUTING docs.

## Review protocol

For each finding produced by `devpilot scan data/sample_repo`:
1. Read both sides of the evidence (`path:line` for each).
2. Open the cited files and verify the claim is accurate.
3. Label: **TRUE POSITIVE** (real drift) or **FALSE POSITIVE** (scanner error or overfitting).
4. If FALSE POSITIVE: note which rule fired incorrectly and what the fix should be.

## Findings table

| # | ID | Severity | Message | Evidence | Verdict | Notes |
|---|---|---|---|---|---|---|
| — | — | — | — | — | — | Run `devpilot scan data/sample_repo` to populate |

## Precision

```
Precision = TP / (TP + FP)
```

**Precision: _TBD_ (run scan + review to fill in)**

> Note: do not overfit rule fixes to Flask specifically. The fix should generalize
> to any mid-sized Python project.
