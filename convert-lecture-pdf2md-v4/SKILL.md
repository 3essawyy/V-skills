---
name: convert-lecture-pdf2md-v4
description: Convert lecture-slide PDFs into final, merc-styled study Markdown in one pipeline, with no separate styling sweep, without losing meaning in figures, diagrams, timing tables or equations. Script extraction + PDF text-coverage check, cheap-vision figure transcription, strong-model QA and diagram redo, a single built-in merc styling pass (tables, callouts, renderer-safe Mermaid, LaTeX), machine validation with per-PART repair, then finalize into a per-lecture folder. Use when asked to convert lecture/slide PDFs to md, make slides readable for later sessions, or build styled study notes from slide decks.
---

# convert-lecture-pdf2md-v4

Goal: **A) few tokens, B) nothing lost (not in pictures, not in text boxes, not in wiring), C) the output is the final styled study file: topic subsections, not a slide dump.**
v4 = v3's pipeline + the merc styling built in, so no `/doc-merc-v4` sweep is needed afterwards. The styling rules are a **copied, lecture-specific subset** of doc-merc-v4 (`references/style_guide.md`), maintained independently: changing doc-merc-v4 does not change this skill. The validator now also checks math, tables, Mermaid safe subset and AI callouts, and reports **failing PARTs** so only those get repaired.
v4.1 (CMPS450-style output): slides grouped into **topic subsections** `### N.M Title (slides a–b)` with hidden per-slide anchors `<a id="sNN">`; empty slides (title, outline, section divider, thank-you) **dropped and listed in the footer**; repeated build lines de-duplicated; rich header; PART+subsection ToC with slide ranges; one `Roadmap (AI-added)` diagram; leaner figure blocks; more tables.

`<skill_dir>` = folder of this SKILL.md. Scripts: `<skill_dir>/scripts/`, prompts: `<skill_dir>/prompts/`, style reference: `<skill_dir>/references/style_guide.md`. Needs `pymupdf pillow` (project/user venv, not global); `mmdc` (`@mermaid-js/mermaid-cli`) for Mermaid validation. On Windows run Python with `PYTHONIOENCODING=utf-8` when printing PDF text.

## Roles
- **Orchestrator = main session (Opus)**: runs scripts, launches agents, reads only their short replies and validator output. Images and full markdown never enter the main context.
- **Cheap (Haiku)**: vision batches, the styling pass.
- **Strong (Sonnet)**: hard figures, QA, diagram redo, repair of failing PARTs. Also the styling pass when the pilot shows Haiku output is flat (see step 7).

## Faithfulness contract
Formatting only. Slide text stays verbatim; figure transcriptions are marked `> [!NOTE]` + `**Figure — AI transcription**`. AI additions allowed: **at most one** `> [!TIP]` + `**Key Idea (AI-added):**` callout per PART (directly under the PART heading, 1–2 sentences restating only that PART's slides), and one `### Roadmap (AI-added)` Mermaid flow of the PARTs after the ToC. Neither sits inside slide content. Dropping a slide is allowed only when it teaches nothing; the validator flags a dropped slide with >40 words of content.

## Before starting: settle with the user (ask in one round)
Output layout (per-lecture folder `LecNN - Title/` with the PDF moved in), final file name, Key Idea callouts on/off (default on), QA depth, assets folder name, and any project rules (e.g. a syllabus table to update). Pilot one deck end-to-end first, report cost and look, then run the rest.

## Prompt placeholders
`{DOMAIN}` course topic in a few words (sharpens figure types, e.g. "lexical analysis, DFAs, grammars"), `{COURSE}` course name, `{SCRATCH}` session temp dir, `{BATCH} {MANIFEST} {OUT}` vision, `{DIR} {PDF} {STEM} {SLIDES} {EXTRA}` QA/redo, `{IN} {OUT} {PDF} {TITLE} {N} {STYLE_GUIDE}` style, plus `{STYLE_PROMPT} {PARTS} {PROBLEMS}` repair. Give agents the prompt file path + values; don't paste the prompt (saves main-context tokens). If callouts are off, add "Rule 6 is disabled: write no Key Idea callouts." to the style agent's values.

## Pipeline
| # | Step | Command / prompt | Model |
|---|---|---|---|
| 1 | Extract | `python scripts/convert_pdf.py <pdf> --out-dir <dir>` → `<stem>.md`, `media/<stem>/`, manifest. Check slides == sections. | script |
| 2 | **Text coverage** | `python scripts/coverage.py <pdf> <stem>.md 0.85`. Real slide sentences listed as missing = text inside a figure box that was eaten as labels. Back up `<stem>.md`, then `python scripts/fix_text.py <pdf> <stem>.md 1,5,9` for those slides; re-run coverage. Missing footers / single diagram labels are fine. | script |
| 3 | Vision | One agent per `batches.batch_N` with `prompts/vision.md`, all in parallel. Hard figures (`"hard": true`) → strong. | Haiku |
| 4 | Inject | `convert_pdf.py <pdf> --out-dir <dir> --inject` (re-run after every companion edit; resumable). | script |
| 5 | QA + fix | One agent per deck with `prompts/qa.md`: the slides vision agents flagged `(unclear)`/approximate + 2–4 densest. It fixes companions in place; re-inject. Note the reported *systematic* type. | Sonnet |
| 6 | **Diagram redo** | If QA reports wiring errors (expected for datapaths/circuits/automata/networks): list every unchecked companion with a ```mermaid block of that kind, split ~5–8 per agent, `prompts/redo_diagrams.md`; re-inject. | Sonnet |
| 7 | **Style (merc, one pass)** | `prompts/style.md` with `{STYLE_GUIDE}` = `<skill_dir>/references/style_guide.md` → final md, one agent per deck, in parallel. Pilot: open the result and judge the look; if it's flat/inconsistent despite passing validation, use Sonnet for style for the rest of the run and note it. | Haiku (→ Sonnet) |
| 8 | Validate | `python scripts/validate_style.py <stem>.md <final.md> <N>` (kept anchors + dropped-slides footer cover 1..N, dropped-slide content guard, subsection ranges, per-slide word coverage within its subsection, every figure image linked, AI callout/Roadmap form and placement, one H1, ToC anchors, math, pipe tables, `<details>` ban, Mermaid safe subset + `mmdc`) and `coverage.py <pdf> <final.md>`. Exit 1 → it prints `FAILING_PARTS: part-2,...`. | script |
| 8b | **Repair** | If parts fail: one Sonnet agent with `prompts/restyle_parts.md` (`{PARTS}` = the failing list, `{PROBLEMS}` = those lines of validator output). Re-validate; max 2 rounds, then report what remains. Whole-file failures (`[doc]`: H1, anchors/dropped list, header) → re-run step 7. | Sonnet |
| 9 | Finalize | `python scripts/finalize.py <dir> <stem> <final.md> [--assets-dir assets] --delete-raw` → moves figures + manifest to `assets/`, rewrites links (no spaces in paths), verifies every link, deletes raw md only if all links resolve. | script |

## Rules & lessons
- **Strict batch scope**: vision agents touch only their own ids (one agent once rewrote 10 files of other batches).
- Don't "correct" slide typos in transcriptions; quote the slide (e.g. `VAX-11/780 (slide reads "AX-11/780")`).
- Coverage < threshold with only footer/labels missing is normal for picture-only slides; after inject, coverage drops because labels are re-worded inside transcriptions. Judge by the *missing lines* list, not the %.
- Scrambled equation text layers (`ns Instructio Time CPU`) are kept by extraction and dropped by the style prompt only when the figure gives the LaTeX.
- Progressive builds (same diagram on consecutive slides, a new part highlighted or added) are faithful: keep every build's figure; only identical repeated *text lines* within a subsection are written once.
- Formal notation that isn't arithmetic (grammars, regexes, code, shell commands) is `code`, not LaTeX; `|` in table cells must be escaped. The validator catches bare pipes that break tables.
- Keep the AI-provenance marker on every figure block and every Key Idea callout; never blend AI text into slide text.
- No final doc-merc sweep: if the look needs changing, fix `references/style_guide.md` / `prompts/style.md` here (doc-merc-v4 is a separate, general skill).
- Never edit instructor PDFs; moving them into the lecture folder is fine when the user agreed.
- **Coverage after inject (step 4) too**: a slide's text can be in the raw md before inject (as figure labels) and vanish after, when the vision companion doesn't repeat it. Run `coverage.py` on the injected raw md as well and `fix_text.py` those slides *before* styling (Lec04 pilot: 8 slides lost their instructions this way).
- `fix_text.py`'s `FOOTER` regex is course-specific; set it to the deck's repeated footer (date, instructor name) before running, or strip those lines afterwards. Footer lines are noise; the style prompt deletes them.
- Diagram direction follows the slide (LR or TD as drawn); no prompt may force one direction for all diagrams (the v4 pilot's redo prompt turned hierarchies sideways).
- The per-slide word coverage ignores LaTeX macros, so notation moved from `$$\begin{aligned}` to `text` fences (correct per the style guide) doesn't false-fail.
- Keep rules course-neutral: write prompt/guide changes for slide decks in general, not for the deck that exposed the problem.
- Shell edits of scripts containing Unicode/private-use chars (`•`, `–`, ``) via `sed` can strip escapes: use `chr(0x2022)` etc. in code.

## Cost seen (Claude, 2026-11)
Haiku vision ≈ 65–95k subagent tokens per 8-figure batch; Sonnet QA ≈ 65–80k per deck; Sonnet diagram redo ≈ 75–95k per 5–8 figures; Haiku style ≈ 90–140k per 35–50-slide deck (v3 prompt; v4 adds reading the ~200-line style guide). Scripts cost nothing. Update after the v4 pilot.

## Knobs (top of `convert_pdf.py`, unchanged from v2)
`MIN_FIG_AREA_FRAC`, `REPEAT_FRAC`, `MAX_PX`, `BATCH_SIZE`, `LOWTEXT_CHARS`, `ANNOT_MAX_CHARS` (text blocks up to this length inside a figure become labels; the cause of step-2 losses).
