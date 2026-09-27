# DevPilot — Demo Script (3 minutes)

> Read this aloud at a comfortable pace (~130 wpm). Total runtime: ~3 minutes.
> Timestamps are guides; adjust for live typing speed.

---

## [0:00 – 0:20] The Problem

**[Screen: a fresh clone of a mid-sized repo. Terminal open. No README changes.]**

> "You've just joined a new team. You have repo access. The README says
> `pip install -r requirements.txt` — but when you run it, you get an error.
> The real install command is buried in the GitHub Actions workflow nobody reads.
> This costs hours on day one. DevPilot fixes it before you even start."

---

## [0:20 – 0:55] The Scan

**[Screen: terminal in the sample repo directory]**

> "One command. `devpilot scan` walks the entire repo — code, CI workflows, git history,
> docs — and extracts verifiable facts."

```bash
devpilot scan data/sample_repo
```

**[Screen: JSON output scrolling, then: `✓ Wrote facts.json and findings.json`]**

> "And immediately — six doc-drift findings. The README install command doesn't match CI.
> An env var is read in code but documented nowhere. A referenced file doesn't exist.
> These are the exact things that would have wasted the new hire's first day."

**[Screen: open findings.json briefly, highlight D1 and D2]**

---

## [0:55 – 1:20] Verify

**[Screen: terminal]**

> "Now let's actually run the setup commands. `devpilot verify` spins up an isolated
> virtual environment, runs each detected command with a timeout, and records what breaks."

```bash
devpilot verify data/sample_repo
```

**[Screen: steps running, duration displayed, final: `3/3 steps passed`]**

> "Three steps passed. Now we have ground truth — not docs that might be wrong, but commands
> that actually work on this machine, right now."

---

## [1:20 – 1:45] Ask

**[Screen: terminal]**

> "A new developer has questions. `devpilot ask` uses BM25 search over the code and docs —
> no API, no network — and returns ranked answers with file and line citations."

```bash
devpilot ask data/sample_repo "What environment variables are required?"
```

**[Screen: ranked results showing SECRET_KEY from app.py with file:line citation]**

> "The answer comes from the source, not from memory. Every result has a `file:line` so you
> can click straight to the evidence."

---

## [1:45 – 2:10] The Report

**[Screen: terminal → browser]**

> "And the full picture: one HTML report. Architecture, setup guide from verified commands only,
> drift warnings table, owners, and a ranked list of five safe first tasks."

```bash
devpilot report data/sample_repo
```

**[Screen: report.html opens — scroll through all six sections]**

> "Light and dark mode. Everything linkable. A new hire can read this in five minutes and
> know exactly what to do."

---

## [2:10 – 2:50] Bob — The AI Layer

**[Screen: Bob in Onboarding Guide mode, new chat]**

> "The real power: switch Bob to Onboarding Guide mode and run the `onboard-repo` skill."

```
I'm new to the repo at data/sample_repo. Onboard me.
```

**[Screen: Bob spawns multiple explore subagents — show subagent panel]**

> "Bob fans out one explore subagent per Flask module — all in parallel. Each one reads
> the source and returns a grounded summary: purpose, key files, connections, gotchas.
> Bob then merges them into ONBOARDING.md."

**[Screen: ONBOARDING.md opens — scroll through sections]**

> "Every command comes from verify.json. Every env var cites a file:line. If Bob can't
> verify something, it writes 'UNVERIFIED' — it never guesses."

---

## [2:50 – 3:00] The Punchline

**[Screen: side-by-side: stopwatch for manual vs DevPilot]**

> "Manual onboarding: hours. With DevPilot: under 60 seconds to a verified, cited,
> module-level onboarding guide. The repo's knowledge was always there — DevPilot just
> makes it findable."

---

*End of demo. See `docs/IMPACT.md` for measured before/after numbers.*
