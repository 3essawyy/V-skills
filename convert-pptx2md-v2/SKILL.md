---
name: convert-pptx2md-v2
description: Advanced PowerPoint (PPTX) to Complete Markdown converter (v2) with 2D spatial layout reconstruction, implicit shape grid-to-table synthesis, asset discrimination (diagrams vs bullet icons), speaker notes isolation, and verified GitHub Flavored Markdown anchor linking.
---

# convert-pptx2md-v2 — Advanced PowerPoint to Complete Markdown Skill

Use this skill when converting PowerPoint presentations (`.pptx`) into complete, high-fidelity Markdown documents. **pptx2md-v2** is the presentation-counterpart to **docx2md-v2**, specifically engineered to solve the architectural challenges unique to slide canvases.

---

## 1. Why PowerPoint Conversion Differs from DOCX

Word documents follow a linear 1D flow of text and inline tables. In contrast, PowerPoint presentations are **2D spatial canvases**:
1. **Spatial Layout vs Linear Flow:** Text boxes, callout cards, and badges are placed at arbitrary `(x, y)` coordinates. Naive text extraction scrambles content across multi-column slides.
2. **Implicit Shape Grids vs Native Tables:** Slide authors frequently build matrices, comparisons, and calendars using multiple individual shape rectangles rather than native PowerPoint `Table` objects.
3. **Asset Discrimination:** Slide decks often mix dozens of tiny 400-byte bullet icons (dots, arrows) with high-value full-slide architecture diagrams or roadmap graphics.
4. **Speaker Notes & Facilitator Scripts:** Crucial enterprise knowledge and training guidance frequently reside in slide speaker notes rather than visual bullet points.

---

## 2. Core Pillars of pptx2md-v2

### A. 2D Spatial Sorting & Multi-Column Reconstruction
* Sorts shapes vertically by `top` coordinate, then horizontally by `left`.
* Groups side-by-side elements (e.g. 3-role cards, 2-column before/after comparisons) into logical visual units rather than interleaving their lines.

### B. Implicit Shape Grid-to-Table Synthesis
* Detects aligned shape clusters (e.g., governance calendars, comparison cards, sizing matrices) and converts them into semantic HTML `<table>` blocks (`<thead>`, `<tbody>`, `colspan`, `rowspan`) adhering to docx2md-v2 standards, or clean GitHub Flavored Markdown tables.

### C. Asset Discrimination (Hero Graphics vs Bullet Icons)
* Extracts all media to `assets/<deck-slug>/`.
* **Hero Graphics & Diagrams** (images $> 10\text{ KB}$ or $> 200\times 200\text{ px}$): Anchored contextually in Markdown (`![Slide X - Title](assets/...)` or `<img src="..." width="..."/>`).
* **Bullet Icons** (images $< 2\text{ KB}$): Mapped to standard Unicode/Markdown emojis (`🔴`, `🟢`, `🟠`, `✅`, `📅`, `🧑‍💻`, `🧪`, `⚙️`) to avoid cluttered and fragile image links.

### D. Speaker Notes Isolation
* Extracts `slide.notes_slide` and formats any facilitator scripts into styled callout blocks:
  ```markdown
  > 💡 **Speaker Notes & Facilitator Guidance:**
  > ...
  ```

### E. Verified GFM Slug Anchor Matching
* Standardizes all heading slugs according to GitHub Flavored Markdown (GFM) punctuation removal rules so that 100% of Table of Contents links resolve correctly.

---

## 3. Quick Start Workflow

To convert any `.pptx` presentation using the pptx2md-v2 automation engine:

```bash
python ~/.gemini/skills/convert-pptx2md-v2/scripts/convert_pptx.py <input_pptx_path> [output_md_path] [--asset-dir <dir_name>]
```

### Example
```bash
python ~/.gemini/skills/convert-pptx2md-v2/scripts/convert_pptx.py "MyPresentation.pptx" "MyPresentation.md" --asset-dir "assets/my-presentation"
```

---

## 4. Formatting & Aesthetic Standards

* **Slide Titles:** Use `## Slide XX: <Slide Title>` with hierarchical sub-headings for sections.
* **Knowledge Checks:** Format self-assessment or quiz prompts as callouts:
  ```markdown
  > ### ✋ Check Your Understanding
  > **Question:** ...
  ```
* **Quotes & Principles:** Emphasize core guiding principles in styled blockquotes:
  ```markdown
  > *"Predictable delivery through aligned execution."*
  ```
