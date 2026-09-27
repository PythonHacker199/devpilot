# Cognitive Desktop Workspace — Roadmap

## Milestone 1 — MVP

> Deliver a working Windows app that a student can install, run with Alt+S, capture a
> circuit or math problem, and get Socratic scaffolding with a circuit SVG artifact.
> Every number in the response comes from the deterministic solver.

---

### Phase 0 — Environment & Toolchain (manual, ~2 hrs)

**Status:** `[ ] pending`

Tasks (done by developer, not automated):
1. Install Rust stable + `cargo` (rustup)
2. Install Node.js LTS + pnpm
3. Install Tauri v2 CLI: `cargo install tauri-cli --version "^2"`
4. Install Python 3.11+ and create `.venv`; install SymPy + genanki
5. Download whisper.cpp and build for CPU (AVX2): `make base.en`
6. Confirm `Windows.Media.Ocr` is available (Windows 10 1803+; should be present)
7. Create repo with `pnpm create tauri-app` using React + TypeScript template

**UAT:**
- [ ] `cargo tauri dev` starts the app shell with no errors
- [ ] `python -m pytest tests/ -q` passes (empty test suite — placeholder)
- [ ] whisper.cpp binary can transcribe a 5-second WAV clip from CLI

---

### Phase 1 — Plan

**Status:** `[ ] pending`
**Mode:** Plan

Produce `docs/DESIGN.md`:
- IPC surface (Tauri commands exposed to React)
- Sidecar process lifecycle and IPC protocol (stdin/stdout JSON)
- Data model for SQLite tables (sessions, attempts, error_taxonomy, netlists, cheatsheets)
- System prompt architecture (base prompt + mode overlays: homework vs exam)
- Artifact rendering pipeline (netlist → SVG → slider → re-simulate loop)
- State machine for Faded Example levels (1 → 2 → 3 transitions)
- Risk register (hallucination containment, sidecar crash recovery, OCR failure fallback)

**UAT:**
- [ ] `docs/DESIGN.md` exists with all sections above
- [ ] IPC command table lists every `tauri::command` with input/output types
- [ ] SQLite schema is fully specified (CREATE TABLE statements or equivalent)

---

### Phase 2 — Tauri Shell + Global Hotkeys + OCR

**Status:** `[ ] pending`
**Mode:** Agent

Tasks:
- `src-tauri/src/main.rs` — app lifecycle, system tray, window management
- `src-tauri/src/capture.rs` — screen rect capture using Win32 GDI (BitBlt)
- `src-tauri/src/ocr.rs` — `Windows.Media.Ocr` WinRT bindings via `windows` crate
- `src-tauri/src/ipc.rs` — Tauri commands: `snip_and_ocr()`, `get_window_state()`
- `src-tauri/Cargo.toml` — dependencies: `tauri`, `windows` (WinRT), `screenshot-rs` or `scrap`
- System tray with "Snip (Alt+S)", "Dictate (Alt+D)", "Settings", "Quit"
- Floating HUD window (always-on-top, 400 px wide, right-anchored) that shows OCR result

**UAT:**
- [ ] Alt+S opens a crosshair selector; drag produces a screenshot
- [ ] OCR text from a screenshot of a printed equation appears in the HUD within 500 ms
- [ ] App idles at < 60 MB RAM (Task Manager)
- [ ] `cargo test` passes

---

### Phase 3 — Python Sidecar + SymPy Solver

**Status:** `[ ] pending`
**Mode:** Agent

Tasks:
- `sidecar/solver.py` — SymPy symbolic solver; JSON-in / JSON-out over stdin/stdout
  - Input: `{ "expr": "...", "solve_for": "x", "subs": {"R": 4000} }`
  - Output: `{ "symbolic": "...", "numeric": "..." }`
  - Uses SymPy's safe parser; does **not** call `eval()`
- `sidecar/sidecar_main.py` — dispatcher (solver + future spice); launched by Tauri as sidecar
- Tauri IPC command `solve_expr(payload)` that sends to sidecar and returns result
- `tests/test_solver.py` — 10 test cases covering: Ohm's law, KVL simple loop, RC time constant,
  voltage divider, Thevenin equivalent, quadratic roots, matrix 2×2 inversion,
  Laplace s-domain expression, partial fraction, sinusoidal steady-state amplitude

**UAT:**
- [ ] All 10 solver test cases pass with exact expected results
- [ ] Tauri IPC round-trip (frontend → sidecar → result) completes < 200 ms for simple expressions
- [ ] Invalid expressions return a structured error, not a crash

---

### Phase 4 — BYOM Router + Session Context

**Status:** `[ ] pending`
**Mode:** Agent

Tasks:
- `src/lib/modelRouter.ts` — OpenAI-compatible adapter; config: provider URL, model, API key
  - Providers: Ollama (`http://localhost:11434`), Groq, Gemini, OpenRouter
  - Automatic fallback chain on rate-limit (429) or timeout
  - Response streaming to HUD
- `src/lib/sessionStore.ts` — in-memory + SQLite session: messages, snipped context, OCR text
- Settings panel: provider selector, API key entry (saved to Windows Credential Manager via Tauri)
- System prompt loader from `data/system_prompts/` directory
- Homework mode enforcer: post-process LLM stream to detect and block answer patterns

**UAT:**
- [ ] Sending a question via HUD produces a streamed Socratic response (tested with Ollama llama3)
- [ ] Switching provider in settings takes effect on the next request without restart
- [ ] A direct "give me the answer" request in Homework mode is deflected back to a probe

---

### Phase 5 — Socratic Faded-Example Engine

**Status:** `[ ] pending`
**Mode:** Agent

Tasks:
- `src/components/SocraticEngine/FadedExample.tsx` — 3-level scaffold UI
  - Level 1: shows setup + equation + intermediate; student types final answer
  - Level 2: shows setup only; student types equation + solution
  - Level 3: shows problem statement; exam simulator
- State machine: attempt → evaluate → log to Error Taxonomy → advance or retry
- Evaluation: send student's answer to SymPy solver for symbolic comparison (not string match)
- "I'm stuck" button triggers FR-7 probe sequence; each probe revealed after student input
- `data/system_prompts/socratic_scaffold.md` — base system prompt (no-answer, probe-first rules)
- `tests/test_faded_engine.ts` — unit tests for state machine transitions

**UAT:**
- [ ] Completing Level 1 correctly unlocks Level 2 for the same problem
- [ ] "I'm stuck" triggers probe question 1; answering it reveals probe question 2; and so on
- [ ] Final answer in Level 1 is evaluated symbolically (e.g., `V = 8` matches `V = 12*6/9`)
- [ ] Skipping all probes does not reveal the answer

---

### Phase 6 — SPICE Netlist Pipeline + Circuit SVG Artifact

**Status:** `[ ] pending`
**Mode:** Agent

Tasks:
- `sidecar/spice.py` — ngspice wrapper; accepts netlist string; returns operating-point JSON
  - Allowlist validation of element types before exec
  - Runs ngspice in subprocess with 30 s timeout and no network access
- VLM circuit-detection prompt: sends snipped image; classifies as circuit / math / text
- If circuit: sends image to VLM → SPICE netlist extraction → store in SQLite
- `data/system_prompts/circuit_explainer.md` — topology-only system prompt (no numbers)
- `src/components/Artifacts/CircuitCanvas.tsx` — SVG circuit renderer from netlist
  - Node coloring (distinct color per independent node)
  - KVL mesh arrows overlay
  - Parameter sliders (R/L/C values) with live re-simulation
- `tests/test_spice.py` — 5 reference circuits: voltage divider, Wheatstone bridge, RC filter,
  simple op-amp, two-mesh KVL; results within 1% of hand-calculated reference

**UAT:**
- [ ] Snipping a voltage divider circuit produces a valid SPICE netlist within 3 s
- [ ] ngspice returns V_node2 within 1% of hand-calculated value
- [ ] Circuit SVG renders correctly; moving R1 slider updates displayed current in real time
- [ ] LLM response for circuit contains no raw numerical values (contains "see solver result")

---

### Phase 7 — Voice Dictation (whisper.cpp)

**Status:** `[ ] pending`
**Mode:** Agent

Tasks:
- `src-tauri/src/audio.rs` — WASAPI microphone capture; writes to temp WAV file
- Tauri command `start_dictation()` / `stop_dictation()` → triggers whisper.cpp binary
- `src/lib/whisper.ts` — IPC wrapper + transcript append to session context
- Model download on first launch with progress bar (base.en ~150 MB)
- `tests/test_ocr_pipeline.py` — round-trip: WAV file → transcript text check (5 fixture clips)

**UAT:**
- [ ] Alt+D starts microphone capture; releasing captures and transcribes
- [ ] 5-second spoken sentence transcribed correctly within 2 s on CPU
- [ ] Transcript appended to session context visible in HUD

---

### Phase 8 — YouTube Transcript Ingestion

**Status:** `[ ] pending`
**Mode:** Agent

Tasks:
- `src/lib/youtubeCC.ts` — fetch CC/auto-captions via YouTube's `timedtext` API (URL only, no download)
- Chunk transcript by paragraph / timestamp
- Index chunks into in-memory BM25 corpus for the session
- `devpilot ask`-style: student can query `"what did he say about node voltage at 12:30"`
  and get top-3 ranked transcript chunks with `transcript:HH:MM:SS` citation

**UAT:**
- [ ] Pasting a YouTube URL fetches captions and stores them in session context
- [ ] Querying a known phrase returns the correct timestamp chunk in top-3
- [ ] Fails gracefully (user-visible message) if no captions are available

---

### Phase 9 — Anki Export

**Status:** `[ ] pending`
**Mode:** Agent

Tasks:
- `sidecar/anki_export.py` — genanki card builder
  - Input: `{ "front": "...", "back": "..." }` + optional tags from Error Taxonomy
  - Output: `.apkg` file saved to user's Downloads folder
- 1-click "Add to Anki" button on any Faded Example step
- Card front: the problem step the student failed at
- Card back: the Socratic probe chain (no final answer)
- Optional AnkiConnect sync if `http://localhost:8765` is reachable

**UAT:**
- [ ] Clicking "Add to Anki" produces a valid `.apkg` file openable by Anki desktop
- [ ] Card front and back match the problem step and probe sequence
- [ ] When AnkiConnect is running, the card appears in the target deck within 2 s

---

## Milestone 2 — Enhanced Diagnostics

### Phase 10 — Error Taxonomy Log + Dynamic Cheatsheet

**Status:** `[ ] pending`
**Mode:** Agent

Tasks:
- SQLite schema: `error_taxonomy` table (FR-10 fields)
- Write to DB on every attempt in the Faded Example engine
- `src/components/ErrorDashboard/` — dashboard showing failure mode frequency chart
- `src/lib/bm25.ts` — BM25 ranker for cheatsheet section ordering
- `src/components/ErrorDashboard/CheatsheetPanel.tsx` — live-ranked reference card
- `data/cheatsheets/*.md` — curated section files per topic domain

**UAT:**
- [ ] After 3 boundary-sign errors, the Passive Sign Convention section is ranked #1 in cheatsheet
- [ ] Error dashboard shows correct counts by failure mode
- [ ] Student can pin/dismiss cheatsheet sections; state persists across app restarts

---

### Phase 11 — "Spot the Flaw" Error Discrimination

**Status:** `[ ] pending`
**Mode:** Agent

Tasks:
- `src/components/SocraticEngine/SpotTheFlaw.tsx` — UI: shows multi-step derivation, student clicks the wrong step
- System prompt: `data/system_prompts/spot_the_flaw.md` — error injection rules
- Error injector: picks a random step in the model's derivation and injects one error from taxonomy
- Evaluation: student identifies step + explains error; SymPy verifies the correction
- Logs outcome to Error Taxonomy as `discrimination_miss` or `discrimination_success`

**UAT:**
- [ ] A generated derivation contains exactly one injected error
- [ ] Clicking the correct step and providing the right correction is logged as success
- [ ] A wrong step click triggers a Socratic hint, not the answer

---

### Phase 12 — Full Bode / Phasor Diagram Artifacts

**Status:** `[ ] pending`
**Mode:** Agent

Tasks:
- `src/components/Artifacts/BodePlot.tsx` — Plotly.js Bode magnitude + phase, live R/L/C sliders
- `src/components/Artifacts/PhasorDiagram.tsx` — rotating phasor SVG, ω slider
- RLC damping classifier: real-time ζ calculation + label (overdamped / critical / underdamped)
- Pole-zero plot linked to Bode

**UAT:**
- [ ] Adjusting R from 100 Ω to 1 kΩ visually shifts damping category on chart in < 100 ms
- [ ] Pole-zero plot updates in sync with Bode on every slider change
- [ ] Phasor diagram rotates correctly for ω sweep from 1 to 10 kHz

---

## Dependency map

```
Phase 0 (env setup)
  └─► Phase 1 (design)
        └─► Phase 2 (shell + OCR)
              └─► Phase 3 (sidecar + solver)
                    ├─► Phase 4 (router + session)
                    │     └─► Phase 5 (Socratic engine)
                    │           ├─► Phase 8 (YouTube CC)
                    │           └─► Phase 9 (Anki export)
                    └─► Phase 6 (SPICE + circuit SVG)
Phase 7 (voice) is independent of Phase 4–6; can run in parallel with Phase 4
Phase 10–12 (Milestone 2) depend on all MVP phases being complete
```

## Risk register

| Rank | Category | Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|---|---|
| 1 | STEM integrity | LLM hallucinating circuit arithmetic | High | Critical | Route all numbers to deterministic solver; LLM produces topology prose only |
| 2 | Pedagogical | Students bypassing Socratic hints under exam pressure | High | High | Dual-mode toggle: Homework (guided) vs Exam Sim (strict no-answer) |
| 3 | API rate limits | Free cloud tier exhausted mid-session | High | Medium | SQLite completion cache + auto-fallback chain (Groq → Gemini → Ollama) |
| 4 | UX / cognitive overload | Too many simultaneous panels cluttering screen | Medium | Medium | Progressive disclosure: only snip shown initially; artifacts/hints revealed step-by-step |
| 5 | Packaging | whisper.cpp CPU build fails on user's hardware | Medium | Medium | Bundle pre-built binary for x86-64 AVX2; fall back to cloud ASR opt-in |
| 6 | Windows-only | WinRT OCR API unavailable on older OS builds | Low | High | Document minimum OS requirement (Windows 10 1803+); fallback to Tesseract via sidecar |
