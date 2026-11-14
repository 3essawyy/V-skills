You restyle a converted lecture markdown into the "merc" aesthetic. FORMAT ONLY: never add explanations, examples, summaries or facts that are not in the input. Never drop content.

INPUT: `{IN}`  OUTPUT: write `{OUT}` with the Write tool (long files: first part with Write, rest appended with Edit; never summarize or shorten a figure block or slide). Do not modify the input file.

Rules:
1. Header: first line `> Source: {PDF} — instructor slides, converted to Markdown. Figure blocks marked "AI transcription" are AI-written; check the linked image for exact details.` Then `# {TITLE}`, then `### {COURSE} — Lecture slides`.
2. Group consecutive slides into 3-7 PARTs by the topic their titles show. PART = `<a id="part-N"></a>` + `## PART N — <topic>`. Each slide becomes `<a id="sNN"></a>` + `### NN · <slide title>` (NN = slide number, 2 digits). A slide with no title gets a title taken from its first line. Consecutive slides with an identical title stay separate headings.
3. Table of Contents after the title: each PART linking `#part-N`, with its slides as nested links `#sNN`. Every link must point to an anchor that exists.
4. Slide text: keep wording verbatim. Only fix layout: turn `–`/`•`/`o` bullets into `-` (nested with 2-space indent for sub-points), re-join lines broken mid-sentence, fix obvious PDF artifacts (stray spaces, duplicated fragments). DELETE scrambled equation fragments, i.e. lines of jumbled single words such as `ns Instructio Time CPU`, `cycles Clock Program`, `cycle`, `Clock`: they are the broken text layer of an equation that the slide's figure block already gives as LaTeX. Delete a slide line that repeats the slide title verbatim. Content shaped as >=3 structured records or a comparison becomes a markdown table (same words). Formulas with fractions/sub/superscripts become LaTeX (`$...$` inline, `$$...$$` own lines).
5. Figure blocks (between `<!-- INJECT_START: id -->` and `<!-- INJECT_END: id -->`): drop the two comment markers, replace the bold marker line with `> [!NOTE]` + newline + `> **Figure — AI transcription** (slide NN)`, keep the transcription content below it (not inside the blockquote), keep the image link line unchanged. Drop `<!-- skipped decorative ... -->` lines.
6. Mermaid (renderer-safe subset): first line inside the block `%%{init: {'theme':'base'}}%%`; keep the diagram type line; edges with labels ONLY as `A -->|label| B` or `A -.->|label| B` (convert `A -- "x" --> B` and `A -- x --> B`); shapes only `["..."]`, `("...")`, `(("..."))`, `{"..."}`; all labels in double quotes, plain ASCII (no emoji, no `|` inside labels, write `->`, `>=`); no nested subgraphs. Add these classDefs and assign nodes by role with `:::name`:
   `classDef entry fill:#1a1a2e,stroke:#e94560,color:#fff` (inputs/start), `classDef core fill:#16213e,stroke:#0f3460,color:#fff` (processing/logic), `classDef data fill:#0f3460,stroke:#533483,color:#fff` (memory/registers/storage), `classDef out fill:#2d3436,stroke:#00b894,color:#fff` (results/outputs), `classDef ext fill:#2d3436,stroke:#6c5ce7,color:#fff` (control/external).
   Do not change the diagram's nodes or edges otherwise.
7. `---` only between PARTs. One H1 only. No emoji in headings.
8. Footer: `---` then `*Scope: {TITLE} · {N} slides · converted from {PDF}*`.

Reply with only: output path, PART count, slide-heading count.
