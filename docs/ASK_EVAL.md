# DevPilot — Ask Evaluation

## Benchmark: `data/onboarding_questions.md` × `data/sample_repo`

This file is populated in Phase 6 after running all 10 benchmark questions against
`data/sample_repo` (pallets/flask @ 3.1.0).

## Evaluation protocol

For each question:
1. Run: `devpilot ask data/sample_repo "<question>"`
2. Record the top-3 file paths returned.
3. Identify the "correct" file (the file that actually contains the primary answer).
4. Mark HIT if the correct file appears in the top-3, MISS otherwise.

## Results table

| # | Question | Correct file | Top-3 files | Hit? |
|---|---|---|---|---|
| 1 | How do I install and run the project locally? | CONTRIBUTING.rst / README.md | — | — |
| 2 | What environment variables does the project require? | src/flask/cli.py | — | — |
| 3 | Where is the main application entry point? | src/flask/app.py | — | — |
| 4 | What test framework is used and how do I run tests? | CONTRIBUTING.rst | — | — |
| 5 | Which files change most frequently? | (hotspots from facts.json) | — | — |
| 6 | Who owns the core application module? | CODEOWNERS / git log | — | — |
| 7 | What third-party runtime dependencies does the project use? | pyproject.toml | — | — |
| 8 | Are there any open TODOs or known workarounds in the code? | (todos from facts.json) | — | — |
| 9 | What CI/CD pipeline runs on pull requests? | .github/workflows/*.yml | — | — |
| 10 | How does the project handle configuration (env vs files)? | src/flask/cli.py | — | — |

## Hit rate

```
Hit rate = hits / 10
```

**Hit rate: _TBD_ (run Phase 6 evaluation to fill in)**

**Target: ≥ 7/10**
