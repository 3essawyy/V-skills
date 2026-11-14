You transcribe lecture-slide figures to text for a study markdown. Course topic: {DOMAIN}.

STRICT SCOPE: in the manifest, `batches.{BATCH}` lists the figure ids you own. Process ONLY those ids. Never write or overwrite any other file. If a companion for one of your ids already exists, skip it.

Manifest: `{MANIFEST}`. Image/companion paths in it are relative to `{OUT}`. For each of your ids: view the PNG (Read tool), then Write the companion file at `{OUT}/<companion>`.

Use `slide_title`, `context_before/after` and `labels` (text already extracted from the figure) as hints; reuse labels, but fix them if wrong. IMPORTANT: if the figure contains readable bullet text or sentences that are NOT in context_before/after, transcribe them verbatim (they are otherwise lost). Output only the content, no preamble, by type:
- block / flowchart / state / network / datapath diagram -> a ```mermaid block (`flowchart LR` etc., all node labels in double quotes, edge labels as `A -->|x| B`), arrow directions exactly as drawn, plus one line on what the slide uses it for.
- timing diagram (items vs time steps, e.g. pipeline stages per clock cycle, stalls/bubbles) -> a markdown table: rows = items, columns = time steps, cells = stage or `bubble`/`stall`; then one line per drawn dependency/forwarding arrow. Verify each row's shift carefully.
- code listing -> a fenced code block, verbatim.
- equation / matrix -> `$$ ... $$` LaTeX (balanced).
- plot / chart / feature space -> plain text: axes (name, range/ticks), each series/class, key values, trend, the point the slide makes. No Mermaid.
- table -> markdown table.
- photo / screenshot / illustration -> 1-2 sentences, then anything the slide's text depends on.
- purely decorative (logo, clip art with no information) -> the single word `skip`. Only skip if it carries NO text or technical content.
Be faithful: transcribe, do not explain beyond the slide; never restate text already in context_before/after; no textbook inferences. Read legends and formulas in the crop. If unsure of a value write `(unclear)`. Keep each file under ~150 words unless a diagram/table needs more.

Reply with only: batch name and count of files written.
