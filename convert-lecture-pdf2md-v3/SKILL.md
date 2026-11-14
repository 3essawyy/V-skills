---
name: convert-lecture-pdf2md-v3
description: Convert lecture-slide PDFs to token-lean, verified Markdown (optionally merc-styled) without losing meaning in figures, diagrams, timing tables or equations. Script extraction + PDF text-coverage check, cheap-vision figure transcription, strong-model QA and diagram redo, then style, validate and finalize into a per-lecture folder. Use when asked to convert lecture/slide PDFs to md, make slides readable for later sessions, or build study notes from slide decks.
---

# convert-lecture-pdf2md-v3

Goal: **A) few tokens, B) nothing lost: not in pictures, not in text boxes, not in wiring.**
v3 = v2's extractor + the fixes found converting 4 computer-architecture decks (166 slides, 114 figures):
text hidden inside figure boxes was dropped (→ coverage check + `fix_text.py`), parallel vision agents overwrote each other (→ strict batch scope), cheap-model datapath wiring was wrong in ~2/3 of checked diagrams (→ strong-model redo of every dense diagram), and the styled output needed machine validation (→ `validate_style.py`, `finalize.py`).

`<skill_dir>` = folder of this SKILL.md. Scripts: `<skill_dir>/scripts/`, prompts: `<skill_dir>/prompts/`. Needs `pymupdf pillow` (project/user venv, not global); `mmdc` (`@mermaid-js/mermaid-cli`) for Mermaid validation. On Windows run Python with `PYTHONIOENCODING=utf-8` when printing PDF text.

## Before starting: settle with the user (ask in one round)
Output layout (per-lecture folder `LecNN - Title/` with the PDF moved in, or v2's `original/`→`converted/`), final file name, style (merc in place / faithful only / both), QA depth, assets folder name, and any project rules (e.g. a syllabus table to update). Pilot one deck end-to-end first, report cost, then run the rest.

## Prompt placeholders
`{DOMAIN}` course topic in a few words (sharpens figure types, e.g. "MIPS pipelining, hazards"), `{COURSE}` course name, `{SCRATCH}` session temp dir, `{BATCH} {MANIFEST} {OUT}` vision, `{DIR} {PDF} {STEM} {SLIDES} {EXTRA}` QA/redo, `{IN} {OUT} {PDF} {TITLE} {N}` style. Give agents the prompt file path + values; don't paste the prompt (saves main-context tokens).

## Pipeline
| # | Step | Command / prompt | Model |
|---|---|---|---|
| 1 | Extract | `python scripts/convert_pdf.py <pdf> --out-dir <dir>` → `<stem>.md`, `media/<stem>/`, manifest. Check slides == sections. | script |
| 2 | **Text coverage** | `python scripts/coverage.py <pdf> <stem>.md 0.85`. Real slide sentences listed as missing = text inside a figure box that was eaten as labels (whole slide lost if that figure is later `skip`). Back up `<stem>.md`, then `python scripts/fix_text.py <pdf> <stem>.md 1,5,9` for those slides; re-run coverage. Missing footers / single diagram labels are fine. | script |
| 3 | Vision | One agent per `batches.batch_N` with `prompts/vision.md`, all in parallel. Hard figures (`"hard": true`) → strong model. | cheap (Haiku/Flash) |
| 4 | Inject | `convert_pdf.py <pdf> --out-dir <dir> --inject` (re-run after every companion edit; resumable). | script |
| 5 | QA + fix | One agent per deck with `prompts/qa.md`: the slides vision agents flagged `(unclear)`/approximate + 2–4 densest. It fixes companions in place; re-inject. Note the reported *systematic* type. | strong (Sonnet/Pro) |
| 6 | **Diagram redo** | If QA reports wiring errors (expected for datapaths/circuits/networks): list every unchecked companion with a ```mermaid block of that kind, split ~5–8 per agent, `prompts/redo_diagrams.md`; re-inject. | strong |
| 7 | Style (optional) | `prompts/style.md` → final md, one agent per deck, in parallel. | cheap |
| 8 | Validate | `python scripts/validate_style.py <stem>.md <final.md> <N>` (slide headings, one H1, ToC anchors, per-slide word coverage vs raw, `mmdc` per block) and `coverage.py <pdf> <final.md>`. Re-style or patch on failure. | script |
| 9 | Finalize | `python scripts/finalize.py <dir> <stem> <final.md> [--assets-dir assets] --delete-raw` → moves figures + manifest to `assets/`, rewrites links (no spaces in paths), verifies every link, deletes raw md only if all links resolve. | script |

## Rules & lessons
- **Strict batch scope**: vision agents touch only their own ids (one agent once rewrote 10 files of other batches).
- Don't "correct" slide typos in transcriptions; quote the slide (e.g. `VAX-11/780 (slide reads "AX-11/780")`).
- Coverage < threshold with only footer/labels missing is normal for picture-only slides; after inject, coverage drops because labels are re-worded inside transcriptions. Judge by the *missing lines* list, not the %.
- Scrambled equation text layers (`ns Instructio Time CPU`) are kept by extraction and dropped by the style prompt only when the figure gives the LaTeX.
- Repeated full-datapath diagrams on consecutive slides (same circuit, different highlighted stage) are faithful, not duplication; keep them.
- Keep the AI-provenance marker on every figure block; never blend AI text into slide text. Faithful conversions only, no added explanations.
- Never edit instructor PDFs; moving them into the lecture folder is fine when the user agreed.
- Shell edits of scripts containing Unicode/private-use chars (`•`, `–`, ``) via `sed` can strip escapes: use `chr(0x2022)` etc. in code.

## Cost seen (Claude, 2026-11)
Haiku vision ≈ 65–95k subagent tokens per 8-figure batch; Sonnet QA ≈ 65–80k per deck; Sonnet diagram redo ≈ 75–95k per 5–8 figures; Haiku style ≈ 90–140k per 35–50-slide deck. Scripts cost nothing. Main-session context stays small because images never enter it.

## Knobs (top of `convert_pdf.py`, unchanged from v2)
`MIN_FIG_AREA_FRAC`, `REPEAT_FRAC`, `MAX_PX`, `BATCH_SIZE`, `LOWTEXT_CHARS`, `ANNOT_MAX_CHARS` (text blocks up to this length inside a figure become labels; the cause of step-2 losses).
