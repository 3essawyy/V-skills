QA + fix a lecture PDF->markdown conversion. Course topic: {DOMAIN}.
Folder `{DIR}`, PDF `{PDF}`. AI figure transcriptions are the files `{DIR}/media/{STEM}/<id>.md` (id = slide_NN_fig_01); they are injected into `{STEM}.md` between INJECT markers.

Check these slides: {SLIDES}, plus {EXTRA} more figure slides of your choice that are NOT `skip` and carry the most technical content (diagrams, timing tables, plots, dense equations).
For each: render the full PDF page to PNG (`python -c "import fitz,sys; d=fitz.open(sys.argv[1]); d[int(sys.argv[2])-1].get_pixmap(dpi=130).save(sys.argv[3])" <pdf> <page> <png>`) into `{SCRATCH}/qa/`, view it, compare against the companion .md.
If the companion has an error (wrong value/label/stage/arrow direction, missing key content, invented content, or `(unclear)` that the full page resolves): FIX it by rewriting that companion .md only, same format (mermaid: labels double-quoted, edges `A -->|x| B`; timing as a markdown table; LaTeX `$$`). Do not explain beyond the slide. Edit NO other files (the orchestrator re-injects).

Reply under 120 words: per slide `slide N: OK` or `slide N: fixed <what>`; then one line: systematic issue (a figure TYPE that is repeatedly wrong) or "none".
