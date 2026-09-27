# Cognitive Desktop Workspace — Project State

## Current status

**Milestone:** 1 — MVP
**Active phase:** None (ready to begin Phase 0 — Environment & Toolchain)
**Last completed phase:** None

## Phase completion log

| Phase | Name | Milestone | Status | Completed |
|---|---|---|---|---|
| 0 | Environment & Toolchain | 1 | `[ ] pending` | — |
| 1 | Plan (DESIGN.md) | 1 | `[ ] pending` | — |
| 2 | Tauri Shell + Hotkeys + OCR | 1 | `[ ] pending` | — |
| 3 | Python Sidecar + SymPy Solver | 1 | `[ ] pending` | — |
| 4 | BYOM Router + Session Context | 1 | `[ ] pending` | — |
| 5 | Socratic Faded-Example Engine | 1 | `[ ] pending` | — |
| 6 | SPICE Netlist Pipeline + Circuit SVG | 1 | `[ ] pending` | — |
| 7 | Voice Dictation (whisper.cpp) | 1 | `[ ] pending` | — |
| 8 | YouTube Transcript Ingestion | 1 | `[ ] pending` | — |
| 9 | Anki Export | 1 | `[ ] pending` | — |
| 10 | Error Taxonomy + Dynamic Cheatsheet | 2 | `[ ] pending` | — |
| 11 | "Spot the Flaw" Error Discrimination | 2 | `[ ] pending` | — |
| 12 | Bode / Phasor Diagram Artifacts | 2 | `[ ] pending` | — |

## Key decisions logged

| # | Decision | Rationale |
|---|---|---|
| 1 | Tauri v2 over Electron | <60 MB idle RAM; native Win32 API access without additional bridges |
| 2 | `Windows.Media.Ocr` over Tesseract | Zero-dependency, offline, already on every Windows 10+ machine |
| 3 | SymPy sidecar over LLM arithmetic | 100% deterministic; eliminates hallucination on circuit math |
| 4 | ngspice over pure Python SPICE | Industry standard; handles non-linear components future phases may need |
| 5 | Homework mode: no answer disclosure | Core pedagogical principle; enforced at IPC system prompt layer |
| 6 | OpenAI-compatible adapter layer | Allows zero-reconfiguration switching between Ollama, Groq, Gemini |
| 7 | YouTube CC via `timedtext` URL | No video download → no ToS violation, no maintenance breakage |
| 8 | genanki for Anki export | Pure-Python, no Anki install required for basic export |

## Open questions / blockers

- [ ] Choose an open-source JS circuit renderer for the SVG Canvas (candidates: `circuitjs1` port, `schemdraw.js`, custom SVG from netlist)
- [ ] Confirm ngspice can be bundled as a sidecar on Windows (no separate install)
- [ ] Validate whisper.cpp base.en achieves <2s on a representative mid-range laptop (i5/i7 8th gen)
- [ ] Decide whether to use Tauri's built-in sidecar mechanism or spawn the Python process manually

## Immediate action items (pre-Phase 1)

1. **Prompt-spike the faded-example engine** — benchmark a system prompt against 5 circuit and
   calculus problems; verify no final answers leak at Level 1 and Level 2.
2. **Build 1-day Windows Snip prototype** — minimal Tauri/Rust script: Alt+S → GDI capture → 
   `Windows.Media.Ocr` → floating HUD result. Proves the core interaction loop.
3. **Build one parametric artifact component** — isolated React component rendering an SVG
   circuit with an R slider that updates a Bode plot in real time (no backend required).
