Re-transcribe dense wiring diagrams from lecture slides (course topic: {DOMAIN}; e.g. datapaths, circuits, block diagrams, networks). An earlier cheap model drew these as Mermaid with unreliable wiring (missing paths, invented edges, wrong muxes/junctions). Make each diagram match the slide exactly.

For each slide assigned below (deck dir `{DIR}`, PDF `{PDF}`, stem `{STEM}`, slides {SLIDES}):
1. Render the full PDF page: `python -c "import fitz,sys; d=fitz.open(sys.argv[1]); d[int(sys.argv[2])-1].get_pixmap(dpi=140).save(sys.argv[3])" <pdf> <page> <png>` into `{SCRATCH}/redo/`. Also view the crop `media/{STEM}/slide_NN_fig_01.png` if the page is cluttered.
2. Read the current companion `{DIR}/media/{STEM}/slide_NN_fig_01.md`.
3. Rewrite it (Write tool) so that:
   - Every block on the slide is a node and every drawn wire is an edge, direction exactly as drawn, labelled with the signal/port name shown. Do not add wires the slide does not draw; do not drop ones it does. Where crossing wires make a tap point ambiguous, say so in one line.
   - If the slide highlights an active path (colored/bold wires, circled signals, control values), list them in one line below the diagram.
   - Keep any non-diagram content of the current file that is correct (tables, code, verbatim text). Fix anything wrong.
   - Format: ```mermaid, `flowchart LR` or `TD` matching the direction the slide draws it (keep the existing direction if unsure), node labels in double quotes, edges ONLY `A -->|label| B` or `A --> B`, plain ASCII labels, no nested subgraphs, no styling. Then at most one line on what the slide uses the figure for. Transcribe only; no textbook additions.
4. Edit NO other files. Write each file directly (no generator scripts that template several slides).

Reply under 100 words: per slide `slide N: rewritten (<main corrections>)` or `unchanged`.
