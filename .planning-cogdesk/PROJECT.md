# Cognitive Desktop Workspace — Project Context

## What we are building

A native Windows desktop application that inverts the passive "input mode" trap of STEM
education. Students spend ~80% of study time consuming content (watching lectures, reading
slides, skimming AI summaries) which produces recognition memory without generative recall —
the root cause of "I understood the lecture, but I freeze on the exam problem."

The app acts as an **Active Retrieval & Diagnostic Workspace** running entirely on the
student's machine, hooking into their screen and microphone to capture context on demand,
then scaffolding problem-solving through Socratic dialogue instead of answer-dumping.

## Core value proposition

- **Alt+S screen snip** → local OCR → immediate contextual explainer without leaving the IDE
  or browser
- **Alt+D voice dictation** → local whisper.cpp transcription → hands-free question capture
  during lectures
- **Socratic faded-example engine** — three scaffold levels that progressively remove solution
  steps, forcing the student to generate rather than recognize
- **"Spot the Flaw" error discrimination** — deliberately injects subtle errors in derivations
  for the student to catch, building critical debugging instincts
- **Diagnostic Error Taxonomy Log** — structured local ledger categorizing every mistake by
  failure mode (retrieval failure vs. sign convention miss vs. algebraic slip)
- **Interactive artifacts** — live SVG circuit sandboxes, parametric Bode/phasor plots, and
  dynamic cheatsheets that re-prioritize based on the student's error log
- **SPICE Netlist intermediary** — circuit diagrams are translated to SPICE netlists before
  solving; a deterministic SymPy/ngspice solver handles all arithmetic, preventing LLM
  hallucination on circuit math
- **1-click Anki export** — missed problem steps automatically become `.apkg` flashcards

## Active Learning Ratio principle

Target: **30% concept intake : 70% active generation and retrieval practice**
(1:2 principle grounded in Dunlosky et al., 2013 / testing effect research)

## Target users

STEM students (undergraduate, graduate) in courses that require procedural problem solving:
circuits and electronics, differential equations, signals & systems, linear algebra, physics.
Primary persona: laptop-only student in a shared library/dorm, no special hardware.

## Tech stack

| Layer | Technology | Rationale |
|---|---|---|
| Desktop shell | Tauri v2 (Rust) | <60 MB idle RAM vs 350 MB+ Electron; native Win32 hooks |
| UI | React + TypeScript | Component model suits artifact canvas isolation |
| Global hotkeys | Win32 `RegisterHotKey` (via Tauri plugin) | Alt+S, Alt+D |
| Screen capture | Windows GDI/DXGl rect capture | Zero-dependency, no external screen recorder |
| OCR | `Windows.Media.Ocr` WinRT API | Instant, offline, free |
| Voice → text | whisper.cpp (base.en / small.en) | Local CPU (AVX2/SIMD), no API key |
| Symbolic solver | Python SymPy via sidecar process | 100% deterministic arithmetic |
| Circuit solver | ngspice (WASM build or sidecar) | Industry-standard SPICE, no hallucination |
| Artifact rendering | HTML5 Canvas + SVG in sandboxed WebView | Circuit sandbox, Bode/phasor plots |
| Graphing | Plotly.js or Chart.js (bundled) | Interactive sliders, no CDN |
| AI router | OpenAI-compatible adapter | Zero-config switch: Ollama / LM Studio / Groq / Gemini |
| Storage | SQLite (embedded via Tauri plugin) | Error logs, netlists, cheatsheet state — local only |
| Anki export | genanki (Python sidecar) | `.apkg` generation, optionally AnkiConnect sync |

## Repository layout (target)

```
src-tauri/          Rust Tauri shell
  src/
    main.rs         Hotkey registration, OCR, tray icon
    ocr.rs          Windows.Media.Ocr bindings
    capture.rs      Screen rect capture
    ipc.rs          Tauri commands exposed to frontend
src/                React + TypeScript frontend
  components/
    HUD/            Floating overlay UI
    Artifacts/
      CircuitCanvas.tsx     Sandboxed SVG circuit + sliders
      BodePlot.tsx          Parametric Bode diagram
      PhasorDiagram.tsx     Phasor / polar plot
    SocraticEngine/
      FadedExample.tsx      3-level scaffold controller
      SpotTheFlaw.tsx       Error injection UI
    ErrorDashboard/         Taxonomy log + cheatsheet generator
  lib/
    bm25.ts                 BM25 retrieval for cheatsheet ranking
    anki.ts                 .apkg export bridge
    modelRouter.ts          AI provider adapter
sidecar/                    Python helper process (packaged with app)
  solver.py                 SymPy math solver
  spice.py                  ngspice wrapper / SPICE netlist runner
  anki_export.py            genanki card builder
data/
  system_prompts/
    socratic_scaffold.md    Faded-example system prompt
    spot_the_flaw.md        Error injection system prompt
    circuit_explainer.md    Netlist + topology explainer prompt
  error_taxonomy.json       Failure mode category definitions
tests/
  fixtures/                 Sample circuit images, OCR ground truth
  test_solver.py            SymPy solver correctness
  test_spice.py             Netlist parsing + simulation
  test_ocr_pipeline.py      Snip → OCR → context round-trip
  test_faded_engine.py      Scaffold level progression
docs/
  DESIGN.md                 Architecture deep-dive
  PROMPT_ENGINEERING.md     System prompt benchmarks
  IMPACT.md                 Before/after learning metrics (to be filled)
```

## Performance targets

- Idle RAM: < 60 MB (Tauri shell + React WebView)
- Snip-to-OCR latency: < 500 ms
- Voice transcription latency (5-second clip): < 2 s on CPU (whisper base.en)
- First paint of artifact canvas: < 200 ms

## Hard scope limits (anti-features)

- **No video downloader** — no `.mp4` capture; YouTube CC/transcript ingestion via URL only
- **No full thesis/essay writer** — academic integrity risk and feature bloat
- **No presentation builder** — redundant with dedicated tools
- **No cloud storage** — all student data stays on device; no telemetry

## Key design decisions

1. **Socratic-first, answer-never**: Homework mode strictly forbids disclosing the final answer;
   Exam Simulator mode allows it only after the student has attempted all scaffold steps.
2. **Deterministic solver for all numbers**: LLM output is restricted to conceptual narrative
   and netlist generation. Every equation result, matrix inverse, and nodal voltage comes from
   SymPy or ngspice.
3. **Progressive disclosure**: Only the captured snip is shown initially; hints, artifacts, and
   cheatsheets are revealed step-by-step to prevent cognitive overload.
4. **Error taxonomy drives cheatsheet ordering**: If the student repeatedly misses passive sign
   convention, that section floats to the top of the active cheatsheet automatically.
