You restyle a converted lecture markdown into the final "merc" study file in ONE pass. FORMAT ONLY: never add explanations, examples, summaries or facts that are not in the input, and never drop content. The single allowed addition is the AI Key Idea callout (rule 6).

INPUT: `{IN}`  OUTPUT: write `{OUT}` with the Write tool (long files: first part with Write, rest appended with Edit; never summarize or shorten a figure block or slide). Do not modify the input file.

FIRST read the pattern reference `{STYLE_GUIDE}` fully. It holds the exact syntax for every pattern below; follow it over your own habits.

Rules:
1. Header: first line `> Source: {PDF} — instructor slides, converted to Markdown. Blocks marked "AI transcription" or "AI-added" are AI-written; check the linked image / the PDF for exact details.` Then `# {TITLE}`, then `### {COURSE} — Lecture slides`.
2. Group consecutive slides into 3-7 PARTs by the topic their titles show. PART = `<a id="part-N"></a>` + `## PART N — <topic>`. Each slide becomes `<a id="sNN"></a>` + `### NN · <slide title>` (NN = slide number, 2 digits). A slide with no title gets a title taken from its first line. Consecutive slides with an identical title stay separate headings.
3. Table of Contents after the title: each PART linking `#part-N`, with its slides as nested links `#sNN`. Every link must point to an anchor that exists.
4. Slide text: keep wording verbatim. Fix layout only: `-` bullets (2-space nesting for sub-points), re-join lines broken mid-sentence, fix obvious PDF artifacts (stray spaces, duplicated fragments). DELETE scrambled equation fragments (lines of jumbled single words such as `ns Instructio Time CPU`, `Clock`) when the slide's figure block already gives the LaTeX. Delete a slide line that repeats the slide title verbatim.
5. Make it look good without adding words (style guide tables, formatting, math sections):
   - Tables by mechanical trigger: >=2 items compared on >=2 shared attributes, or >=3 structured records, become a table (same words). HTML `<table>` only for merged cells / multi-tier headers. Legends and footnotes go to a `> **Notes & Footnotes**` blockquote below the table, never trailing rows.
   - Bold the term in a line where the slide defines it (`**Lexeme**: ...`). A line the slide already labels "Note:", "Important:", "Remember:" may be wrapped in `> [!IMPORTANT]` / `> [!NOTE]` with its exact words.
   - Math: formulas with fractions, sub/superscripts, Greek, sums become LaTeX (`$...$` inline, `$$...$$` own lines at top level; inside a blockquote or list use a ```math fence). Escape literal dollar signs `\$`. No bare `|` in table math (`\lvert x \rvert`, `\mid`). Regex/grammar notation (`(a|b)*`, `E -> E + T`) goes in `code`, not LaTeX; in a table cell escape `\|`.
   - Code fences always name a language (`text` if none fits).
6. AI Key Idea callout (optional, at most ONE per PART): directly under the `## PART` heading, before the PART's first slide anchor, exactly
   `> [!TIP]` newline `> **Key Idea (AI-added):** <1-2 sentences, <=60 words>`.
   It may only restate what that PART's slides say. Skip it when the PART has no single clear takeaway. Never put it inside a slide, never use it to replace slide text.
7. Figure blocks (between `<!-- INJECT_START: id -->` and `<!-- INJECT_END: id -->`): drop the two comment markers, replace the bold marker line with `> [!NOTE]` + newline + `> **Figure — AI transcription** (slide NN)`, keep the transcription content below it (not inside the blockquote), keep the image link line unchanged. Drop `<!-- skipped decorative ... -->` lines.
8. Mermaid: apply the renderer-safe subset and role classDefs from the style guide (`%%{init: {'theme':'base'}}%%` first; edges `A -->|x| B`; shapes `["..."]` `("...")` `(("..."))` `{"..."}`; double-quoted ASCII labels; no nested subgraphs; classDefs `entry core data out ext` assigned by role with `:::name`). Never change the diagram's nodes or edges otherwise.
9. Not allowed: `<details>` collapsibles, block-beta, bordered ASCII boxes, PART intros/summaries other than rule 6, emoji in headings. `---` only between PARTs. One H1 only.
10. Footer: `---` then `*Scope: {TITLE} · {N} slides · converted from {PDF}*`.

Reply with only: output path, PART count, slide-heading count, Key Idea callout count.
