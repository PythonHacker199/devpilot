# Cognitive Desktop Workspace — Requirements

## Functional Requirements

---

### FR-1: Global Hotkey Screen Snip (Alt+S)
- Pressing Alt+S freezes the screen and lets the user drag a bounding rectangle
- The captured region is sent through the local OCR pipeline
- Extracted text + image thumbnail are injected as context into the active session
- Must work over any foreground window (browser, IDE, PDF viewer, video player)
- Latency: snip → OCR text available < 500 ms

### FR-2: Local OCR Pipeline
- Uses `Windows.Media.Ocr` WinRT API — offline, zero-cost, no API key
- Preserves mathematical notation as closely as possible (subscripts, Greek letters)
- Falls back to raw image passing (base64 to VLM) when OCR confidence is low

### FR-3: Local Voice Dictation (Alt+D)
- Pressing Alt+D starts recording from the system default microphone
- Releasing Alt+D (or a configurable max duration) stops recording and transcribes
- Transcription via whisper.cpp (base.en model default; small.en option)
- Runs fully on CPU via AVX2/SIMD — no GPU required
- Latency: 5-second clip transcribed < 2 s on a modern laptop CPU
- Transcript is appended to the current session context

### FR-4: BYOM (Bring Your Own Model) Router
- Single OpenAI-compatible adapter layer supporting:
  - **Local:** Ollama, LM Studio (any model the user has pulled)
  - **Cloud:** Google Gemini API, Groq API, OpenRouter (user-supplied API key)
- Zero-config fallback chain: Groq → Gemini → Local Ollama (configurable order)
- Completions cached locally in SQLite to reduce repeat API calls and survive rate limits
- Provider rate-limit detection triggers automatic fallback without user intervention

### FR-5: Socratic Faded-Example Engine
The engine presents the same problem at three scaffold levels. Level is selected automatically
based on the student's error history, or manually via toggle.

| Level | App provides | Student must produce |
|---|---|---|
| 1 (guided) | Problem setup + governing equation + intermediate result | Final numerical answer |
| 2 (partial) | Problem setup only | Equation + full solution |
| 3 (exam sim) | Problem statement only | Everything: equation, method, answer |

Rules:
- The engine **never reveals the full solution** while in Homework mode
- Moving from Level 1 → 2 → 3 requires the student to succeed at the current level
- Each attempt is logged to the Error Taxonomy (FR-10)

### FR-6: "Spot the Flaw" Error Discrimination Mode
- On demand, the engine generates a multi-step derivation with **one deliberate error** injected
- Error types drawn from the Error Taxonomy: reversed KVL polarity, missing initial condition,
  sign convention violation, off-by-one index, wrong formula variant
- Student must identify the step containing the error and explain the correct form
- If the student is wrong, the engine gives a Socratic hint (not the answer)
- Correct identification is logged as a "discrimination success" in the Error Taxonomy

### FR-7: Socratic Diagnostic Probing ("I'm stuck" path)
- When the student clicks "I'm stuck", the engine does **not** provide the answer
- Instead it probes backward through the solution path:
  1. "What governing law or formula applies to this problem type?"
  2. "What are the boundary/initial conditions at t=0 (or the DC steady state)?"
  3. "What is the unknown variable you are trying to isolate?"
  4. "What does the equation look like if you substitute the known values?"
- Each probe is revealed only after the student answers (or skips) the previous one
- System prompt strictly enforces this; it is **not** overridable by the student in the chat box

### FR-8: SPICE Netlist Intermediate Representation
- When the snipped image is detected as a circuit diagram (by VLM classification):
  1. A multimodal VLM translates the image to a valid SPICE netlist
  2. The netlist is stored in the local SQLite DB with a thumbnail of the source image
  3. The deterministic solver (FR-9) runs the netlist; LLM output is limited to topology
     explanation, loop definitions, and physical intuition — **no raw numbers**
- Netlist format follows standard SPICE syntax; must be parseable by ngspice

### FR-9: Deterministic Hybrid Solver
Two components, both run locally as Python sidecar processes:

**SymPy solver** (`sidecar/solver.py`):
- Accepts symbolic math expressions (LaTeX or plain-text) + known variables
- Returns exact symbolic result + numerical evaluation with full precision
- Used for: algebraic manipulation, matrix inversion, Laplace transforms, partial fractions

**ngspice runner** (`sidecar/spice.py`):
- Accepts a SPICE netlist
- Returns: nodal voltages, branch currents, operating-point table, optional AC/transient data
- Used for: circuit problem solving, replacing LLM arithmetic entirely

Neither sidecar ever executes arbitrary user-provided shell commands. Input is parsed and
validated before being passed to SymPy or ngspice.

### FR-10: Diagnostic Error Taxonomy Log
Every student attempt (correct or incorrect) is logged to local SQLite with:
- `session_id`, `timestamp`
- `problem_type` (circuit / calculus / linear-algebra / signals / other)
- `scaffold_level` (1 / 2 / 3)
- `outcome` (correct / hint-needed / wrong / skipped)
- `failure_mode` (one of):
  - `formula_retrieval` — forgot the applicable theorem or formula
  - `boundary_sign` — boundary condition or sign convention error
  - `algebraic_slip` — arithmetic or algebraic execution error
  - `topology_error` — wrong node/loop assignment in a circuit
  - `discrimination_miss` — failed to spot an injected error
- `evidence` — the student's verbatim incorrect answer (for review)

### FR-11: Dynamic Living Cheatsheet
- A contextual reference card generated on-the-fly from a curated cheatsheet database
- Card sections are **ranked by Error Taxonomy frequency**: sections matching the student's
  most frequent `failure_mode` appear first
- Student can pin or dismiss individual sections
- Cheatsheet state (pins, dismissals, custom notes) persists in SQLite

### FR-12: Interactive Artifact Rendering
All artifacts are rendered in an isolated sandboxed WebView panel:

**Circuit Sandbox:**
- SVG circuit rendered from SPICE netlist via a lightweight open-source JS engine
- Parameter sliders: adjust any R/L/C/V component value in real time
- Live re-simulation on slider change (ngspice sidecar call or in-browser WASM)
- Node coloring: each independent electrical node gets a distinct color
- KVL loop overlays: directional arrows showing mesh current direction and voltage drops

**Parametric Graph Artifacts:**
- Second-order RLC: sliders for R, L, C → real-time damping category display
  (ζ > 1 overdamped / ζ = 1 critically damped / ζ < 1 underdamped)
- Live pole-zero plot and Bode magnitude/phase plot
- Phasor diagram for AC steady-state circuits

**Dual-Coded Analogy Cards:**
- Rendered alongside math when the topic has a known physical analogy
  (e.g., capacitive reactance ↔ open/short circuit at DC/∞ Hz)

### FR-13: YouTube Transcript Ingestion
- Accepts a YouTube video URL (no video download, no `.mp4`)
- Fetches closed captions / auto-generated transcript via YouTube's public CC endpoint
- Chunks transcript by heading/paragraph; indexes into the session BM25 corpus
- Student can ask questions against the transcript with `file:line`-style `transcript:timestamp` citations

### FR-14: Anki Card Export
- 1-click export of any missed problem step to Anki `.apkg` format
- Card front: the specific step the student failed (the "I'm stuck" trigger point)
- Card back: the Socratic hint sequence (not the final answer)
- Optional: 2-way sync via AnkiConnect API if Anki is running locally
- Export uses `genanki` Python library (bundled in sidecar)

---

## Non-Functional Requirements

### NFR-1: Performance / Resource envelope
- Idle RAM (shell + WebView, no model loaded): < 60 MB
- Peak RAM during local whisper transcription (base.en): < 350 MB
- Peak RAM with Ollama model active: Ollama manages its own process; shell stays < 100 MB
- Snip → OCR result: < 500 ms
- Whisper transcription (5 s clip, base.en, CPU): < 2 s
- Artifact first paint: < 200 ms

### NFR-2: Privacy / data residency
- No telemetry, analytics, or crash reporting to any server
- All student error logs, netlists, and cheatsheet state stored in local SQLite only
- API keys stored in OS credential store (Windows Credential Manager), never in plain files
- YouTube transcript fetch is the only outbound network call; it sends no student data

### NFR-3: Offline-first
- Core flows (snip, OCR, voice, Socratic scaffold with local model) work with no internet
- Cloud AI providers are opt-in; the app degrades gracefully to local Ollama if offline

### NFR-4: Solver correctness
- SymPy solver must return exact results for all test cases in `tests/test_solver.py`
- ngspice results must match hand-calculated reference values within floating-point tolerance
- LLM is **prohibited** from producing any numerical result for a circuit problem when a
  valid netlist is available; the system prompt enforces this at the Tauri IPC layer

### NFR-5: Security / sandboxing
- The sidecar Python processes run in a restricted subprocess (no shell=True, no network access)
- The artifact WebView panel is sandboxed (no Node.js integration, no file system access)
- SymPy expressions are parsed via SymPy's safe parser, not `eval()`
- ngspice inputs are validated against an allowlist of SPICE element types before execution

### NFR-6: Installability
- Ships as a single `.msi` installer or portable `.exe` bundle
- No admin rights required for installation to user profile directory
- No Docker, no WSL, no Python pre-installed by user (Python sidecar bundled)
- Whisper model (base.en, ~150 MB) downloaded on first launch with progress indicator

### NFR-7: Accessibility
- Keyboard-navigable UI (tab order, focus rings)
- High-contrast mode support (respects Windows system high-contrast setting)
- Font size adjustable in settings (12–20 px range)

---

## Scope tiers

### MVP (build first)
- FR-1 Global hotkey snip + FR-2 OCR
- FR-3 Voice dictation (whisper.cpp)
- FR-4 BYOM router (Ollama + one cloud provider)
- FR-5 Socratic faded-example engine (3 levels)
- FR-8 SPICE netlist intermediary + FR-9 deterministic solver (SymPy only; ngspice Phase 2)
- FR-12 Basic circuit SVG artifact with parameter sliders
- FR-13 YouTube CC transcript ingestion
- FR-14 Anki `.apkg` export (no AnkiConnect sync yet)

### Phase 2 (post-MVP)
- FR-6 "Spot the Flaw" error discrimination
- FR-10 Error Taxonomy Log + FR-11 Dynamic cheatsheet
- FR-9 ngspice full circuit simulation
- FR-12 Bode / phasor diagram artifacts
- AnkiConnect 2-way sync (FR-14 enhancement)

### Excluded (anti-features)
- Video `.mp4` downloader (YouTube ToS violation; high maintenance risk)
- Full thesis / dissertation writer (academic integrity risk)
- Presentation slide builder (feature bloat; redundant)
- Any server-side component or cloud storage

---

## System prompt constraints (enforced at IPC layer)

These constraints are woven into every system prompt and cannot be overridden by student input:

1. **No answer disclosure in Homework mode.** The model must not produce the final numerical
   or symbolic answer before the student has attempted the current scaffold level.
2. **No raw numbers for circuit problems with a valid netlist.** All nodal voltages and branch
   currents must be attributed to the solver output, not generated by the model.
3. **Probe before explaining.** On "I'm stuck", the model must ask the diagnostic probe sequence
   (FR-7) before providing any content.
4. **Citation required.** Every formula, theorem, or reference to a source file or transcript
   timestamp must include a citation in the format `[source:location]`.
