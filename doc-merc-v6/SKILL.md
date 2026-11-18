---
name: doc-merc-v6
description: >
  Generates brief, deterministic, highly-structured Markdown documents — quick notes, guides,
  technical reports, system/architecture explanations, cheat sheets, or full documentation — that
  break complex ideas into simple points. Content is driven by the reader's questions and fixed slot
  templates; hard word caps cut redundancy. Uses the merc aesthetic: color-themed Mermaid diagrams,
  structured tables, styled callouts, collapsible sections, and LaTeX math. Use this whenever the user
  asks to "format", "beautify", "write a guide/report/note", "document this", "explain this
  system/code", "make a pretty document", mentions formulas/equations/LaTeX, or generally wants
  Markdown output to look polished rather than plain. Always prefer this over unstyled Markdown output.
---

# merc-v6 — Brief, Deterministic Markdown Documents

Write **what the reader needs, not what you can**. Every line answers a reader question. Anything else is cut.

**v6 changelog:** reader questions drive content and tier (Step 1). Fixed slot templates per content type, hard word caps, fact → implication points (Step 2). Fixed visual triggers (§3.1). Removed: subtitle, context blockquote, footer, concept-intro template, lead-in sentences. Styling rules unchanged from v5.

---

## CORE PHILOSOPHY

1. **Needed, not possible** — content comes from a fixed question list and slot templates, not from what could be said.
2. **Decompose** — a complex idea becomes a one-line definition plus small parts, each one line.
3. **Brief** — hard numeric caps (§2.2). One statement per idea. No restating.
4. **Deterministic visuals** — a content shape triggers a fixed visual (§3.1). No shape, no visual.
5. **Renderer-proof links** — ToC anchors are explicit `<a id>` tags (§3.10).

---

## STEP 1: LIST READER QUESTIONS → TIER

Before writing, list the questions a reader brings to this topic.

- Each question is one a reader would actually ask to understand, use, or reason about the subject.
- Order by dependency: a question's answer uses only answers above it.
- A question whose answer is one line is not a question — fold it into another section as a bullet.
- "Deep dive" / "comprehensive" → dig into more questions, never more words per question.
- State the list in one line before writing (e.g. `Questions: what is X · how does a request flow · why Y over Z`). Pause only if scope is ambiguous.

Question count sets the tier — mechanically:

| Questions | Tier | Structure |
|-----------|------|-----------|
| **1–2** | **1 — Quick Note** | No H1, no ToC. One H2 per question. |
| **3–6** | **2 — Standard** | H1 + one H2 per question. ToC only if 4+ questions. |
| **7+** | **3 — Deep-Dive** | H1 + ToC + PARTs (H2, noun label grouping related questions) + one numbered H3 per question. |

---

## STEP 2: WRITING RULES

### 2.1 — Headings are the questions

- Section headings are the reader questions, phrased as questions, ≤10 words: `## How does a request reach the DB?`
- Tier 3: PART headings are short noun labels (`## PART 1 — Request Path`); the H3s under them are questions (`### 1.1 How is the token checked?`).
- The ToC lists these headings, so it doubles as the question index.

### 2.2 — Hard caps

| Element | Cap |
|---------|-----|
| Bullet | ≤15 words |
| One-line slot (What, Definition, Context, Trigger, Output) | one sentence, ≤20 words |
| Paragraph | ≤2 sentences |
| Text before a section's first slot/bullet | ≤1 sentence (usually zero) |
| Table cell | ≤15 words |
| Callout | ≤20 words |

Code blocks and formulas are exempt from word counts. Inline `code` counts as one word.

If a point won't fit its cap, it's two points — split it.

### 2.3 — Fact → implication

For systems and code, a point pairs a fact with what the reader can infer from it:

```markdown
- Cache is per-node → stale reads after failover
- Tokens are verified locally → revocation takes up to TTL to apply
```

- Use `→` only when the consequence is non-obvious. A plain fact stays plain.
- Never state a consequence without its cause on the same line.

### 2.4 — Slot templates

Each question section uses **exactly one** template, chosen by what the answer is about. Slots appear **in order**, as bold inline labels. Omit a slot with nothing to say. **Never add a slot.** If a question needs two templates, split it into two questions.

**Component** — a part of a system (service, module, class, table):
```markdown
**What:** one line.
**Responsibility:**
- ...
**In → Out:** `input` → `output`
**Depends on:** A, B
**Implications:**
- fact → consequence
```

**Process** — something that happens over steps (request flow, build, algorithm run):
```markdown
**Trigger:** one line.
**Steps:**
1. ...
**Output:** one line.
**Failure points:**
- step N fails → effect
```

**Concept** — an idea, rule, or abstraction:
```markdown
**Definition:** one line.
**Parts:** `X = A + B + C`
- **A** — one line
- **B** — one line
**Implications:**
- fact → consequence
**Example:** only if the concept is abstract — code or one concrete instance.
```

**Decision** — a choice between alternatives:
```markdown
**Context:** one line.
**Options:** table (§3.2), or §3.7 if a cell needs >15 words.
**Pick:** X — why, ≤15 words.
**Cost:** what the pick gives up.
```

**Fallback** — content that fits none of the four: plain bullets under the §2.2 caps, `→` where relevant. No prose.

### 2.5 — Cut list (never write these)

- H3 subtitle, "How this guide fits" blockquote, footer metadata
- Intro paragraphs that preview a section's subsections
- Lead-ins: "The diagram/table below shows…", "Let's look at…", "This section covers…"
- Closers: "In summary…", "To recap…", "Overall…"
- Filler words: "essentially", "basically", "simply", "it's important to note", "in other words", "as mentioned", "in order to" (→ "to")
- Analogies — unless the Concept's **Example** slot needs one because no concrete instance exists
- A second statement of anything already stated

---

## STEP 3: STYLING & FORMATTING TOOLKIT

Full pattern reference lives in this skill's `references/` directory:

- **Patterns & syntax:** [style_guide.md](references/style_guide.md) — every pattern below, in full syntax
- **ToC & anchor rules:** [example_toc.md](references/example_toc.md)
- **Full worked example:** [example_full_doc.md](references/example_full_doc.md) — a complete Tier 3 document in the v6 format; check it when assembling a longer doc

### 3.1 — Visual trigger map

Visuals are triggered by content shape, not chosen by taste. Styling of each visual follows §3.2–3.9 unchanged.

| Content shape | Visual |
|---------------|--------|
| Process with 4+ steps | Mermaid flow (§3.3) in the **Steps** slot, replacing the list |
| Process with ≤3 steps | numbered list |
| 3+ components interacting | one architecture diagram (§3.3), at the first section that needs it |
| Decision options | table (§3.2); §3.7 if a cell needs >15 words |
| ≥2 items compared on ≥2 attributes, or ≥3 records with shared fields | table (§3.2) |
| Concept **Parts** that are ordered layers (3+) | `block-beta` stack (§3.8) |
| Formula meeting §3.9 trigger | LaTeX |
| Directory/file layout | ASCII tree (§3.4) |
| Anything else | no visual |

Never put a sentence before a visual explaining what it shows. The heading already says.

### 3.2 — Visual Tables & Complex HTML Data

Tables are the **default format** for two content shapes — this is a mechanical trigger, not a judgment call:
- **Comparing ≥2 named items across ≥2 shared attributes** → comparison table. Dimension in bold first column, left-aligned, ≤15 words/cell.
- **Listing ≥3 structured records** (parameters, configs, endpoints, mappings) → reference table.

If content has this shape, use a table. Only skip it when the content genuinely lacks shared structure, or when a cell's reasoning would run past ~15 words — in that case use the Decision/Options pattern (§3.7) for that content, not prose bullets as a workaround.

**Complex Tables & Footnote Rule:**
When dealing with complex data that requires merged cells or multi-tier headers:
1. **HTML for Merged Cells:** Abandon Markdown pipe tables (`|...|`) and generate semantic HTML `<table>` blocks utilizing `<thead>`, `<tbody>`, `colspan`, and `rowspan`. 
2. **Visual Dividers:** Use spanning rows (e.g., `<th colspan="3" style="background-color: #f8f9fa;">Section Name</th>`) to organize grouped sections inside tables, replacing standalone markdown headers where appropriate.
3. **Footnote Extraction:** Never place table footnotes or legends inside empty/fragmented trailing table rows (e.g., `| * | Note... | | |`). Extract them into a dedicated blockquote `> ### 📝 Notes & Footnotes` directly below the table.

### 3.3 — Styled Mermaid Diagrams

Use for any process, architecture, sequence, or hierarchy that's genuinely spatial or sequential — not for content that's just as clear as a bullet list.

- Start every diagram with a theme directive so colors render consistently across viewers:
  ```
  %%{init: {'theme':'base'}}%%
  ```
- Colors are **role-based**, not just cycled in node order — pick the role that matches what the node *is*:

| Role | Fill | Stroke | Use for |
|------|------|--------|---------|
| Primary / entry point | `#1a1a2e` | `#e94560` | actors, entry nodes |
| Core / process | `#16213e` | `#0f3460` | main processing steps |
| Data / storage | `#0f3460` | `#533483` | databases, caches, state |
| Success / output | `#2d3436` | `#00b894` | success paths, results |
| External / accent | `#2d3436` | `#6c5ce7` | external systems, warnings |

- Use `<br/>` for multiline labels; keep node labels descriptive, not just IDs.
- **Brackets & Special Characters Protection:** Never place raw square brackets `[]` or nested parentheses `()` directly inside unquoted node labels (e.g., `Node([Data [Box]])`). Doing so breaks the Mermaid compiler and triggers parsing errors. Always wrap the entire label inside double quotes within the parenthesized shapes (e.g., `Node(["Data [Box]"])`).
- **Renderer-safe subset (v4):** a diagram that compiles in `mmdc` can still fail in a preview extension (VS Code, Obsidian, MPE). Stay inside the subset that renders everywhere. Full rules + before/after: style_guide.md §6e.
  - Edge labels: `A -->|label| B` only, never `A -- label --> B`.
  - **Markdown-looking labels (v5):** Mermaid 11 reads a label that starts like Markdown (`-`, `+`, `*`, `1.`, `#`, `>`) as Markdown, so an edge labelled `"-"` shows "Unsupported markdown: list" and VS Code's *Markdown Preview Mermaid Support* can show an empty box. Quote the symbol (`|"'-'"|`) or spell it (`|"minus"|`). Applies to literal-character edges in automata/regex diagrams.
  - Several diagrams in one doc: give node ids a per-diagram prefix (`a_n1`, `b_n1`) so ids never collide.
  - Shapes: `["..."]`, `("...")`, `(("..."))`, `((("...")))`, `{"..."}` only. No stadium `([...])`, no newer shape syntax.
  - Labels: plain ASCII. No emoji; write `>=`, `<=`, `!=`, `->` instead of `≥ ≤ ≠ →`; spell `&` as "and"; no `|` inside a node label (use a comma); keep spaces around `<` / `>` so they can't look like an HTML tag next to `<br/>`.
  - Styling: `classDef` + `:::class` on nodes. No nested subgraphs, and never `style` a subgraph id.
  - Shapes Mermaid can't draw (Venn/overlap, concentric rings): use a table, a linear chain (outer → inner), or a small ASCII sketch (§3.4) instead of forcing it.
- **Validate before delivering:** if `mmdc` (`@mermaid-js/mermaid-cli`) is on PATH, run `mmdc -i <file>.md -o <temp-dir>/out.md` and fix any block it rejects. Write the output to a temp dir, never next to the source file. If `mmdc` isn't installed, say the diagrams are unvalidated. A parse-only check is not enough: render with Mermaid 11 and look for the text "Unsupported markdown" or "Syntax error" in the output.

### 3.4 — ASCII Art (bordered containers retired)

The full bordered container (`┌─...─┐` wrapping multiple rows, closed with `└─...─┘`) is **retired** — it has broken in real use for both paragraph content and plain short lists. Only two shapes survive: directory trees (7a) and small diamond/multi-path sketches (7c), neither of which has a closing right-hand border to misalign. Everything that used to be a bordered box — flat lists, recap cards, linear flows — now goes to §3.7/§3.8 or a plain Markdown list. See style_guide.md §7 for the full decision rule.

### 3.5 — Custom Callouts

- `> **Key Idea:** [core insight]` — at most one per PART (Tier 3) or per doc (Tier 2); none in Tier 1. Only for a cross-cutting insight **no slot already states**. If it repeats a What/Definition line, delete it.
- `> [!IMPORTANT]` — must-not-miss detail (one line, ≤20 words)
- `> [!NOTE]` — supplementary context (one line, ≤20 words)

### 3.6 — Extended Toolkit

- **Collapsible sections** — for genuinely optional/supplementary content only: full config dumps, verbose logs, rarely-needed appendices. **Never** for primary code examples, class/method skeletons, or anything the reader needs to see to follow the main explanation — those stay inline, uncollapsed, always. Default is *don't collapse*; only reach for this when secondary material (rule of thumb: 40+ lines) would otherwise overwhelm the main reading flow:
  ```markdown
  <details>
  <summary><strong>Click to expand: Full config example</strong></summary>

  [content]

  </details>
  ```
- **Task lists** — for setup steps, migration checklists: `- [ ]` / `- [x]`
- **Footnotes** — for citations/asides that would clutter inline flow: `text.[^1]` with `[^1]: source.` at the bottom
- **Footer metadata** — **retired in v6** (it restated the title).

### 3.7 — Decision/Options Framework

For "here are N alternatives, each with reasoning" content — proposals, trade-off discussions, mitigation options. This is prose-length content with no spatial relationship between items, so it's neither a table (cells too long) nor a diagram (nothing to point at). Full pattern: style_guide.md §15.

### 3.8 — Block Diagrams (`block-beta`)

For anything that used to be a bordered box: flat equal-weight lists wanting a "card" look (solid fill), and short-label hierarchies/layered stacks (gradient fill). Not for paragraph-length content — that's §3.7. `block-beta` is a newer, beta-status Mermaid type with less consistent cross-renderer support than `graph`/`flowchart`; use it deliberately. If a plain Markdown list would work just as well with no containment needed, prefer that — it's simpler and has zero rendering risk. Full pattern + caveats: style_guide.md §16.

### 3.9 — LaTeX Math (formulas, equations, derivations)

Mechanical trigger: a formula gets LaTeX if it has fractions, sums/integrals, roots, sub/superscripts, Greek letters, matrices, or a multi-step derivation. Trivial cases (`n = 5`, `O(n)`, `2x`) stay plain text or `code`.

- Inline: `$E = mc^2$`. Blocks: a ```` ```math ```` fence (safe inside lists, callouts, and quotes), or `$$...$$` on its own lines at top level only.
- **Literal dollar signs** must be escaped `\$` (`costs \$5 and \$10`), or they pair up as math.
- **In tables:** never use a bare `|` in math (it splits the cell); write `\lvert x \rvert`, `\mid`, `\Vert`. Keep formulas short.
- **In Mermaid labels:** no LaTeX (renderer support is inconsistent). Prefer ASCII spellings (`>=`, `x^2`, `sum`); use a Unicode letter (`α`, `Σ`) only when there's no readable ASCII form (§3.3 renderer-safe subset).
- Prefer a short line of prose before a block formula saying what the symbols mean. Full patterns: style_guide.md §17.

### 3.10 — Title Block & Table of Contents (Tier 2/3 only)

- H1 = the topic, nothing else (no "— Deep Dive Guide" suffix). Then `---`, then the ToC (if required), then `---`.
- ToC links use **explicit HTML anchors**, not auto-generated slugs:
  ```markdown
  <a id="part-1"></a>
  ## PART 1 — Section Title
  ```
  and the ToC entry links to `#part-1`. Auto-slug anchors are **not** reliable across renderers — GitHub, VS Code, Obsidian, and static-site generators all slugify differently, especially around punctuation like question marks and em-dashes. Use short sequential ids: `part-1`, `part-1-2`, etc.

---

## STEP 4: DOCUMENT STRUCTURE & FLOW

- Only the document title is H1. Tier 2 questions are H2; Tier 3 PARTs are H2 with numbered question H3s (`## PART 1 — Title` → `### 1.1 How does …?`).
- Horizontal rules (`---`) divide major sections only, not every subsection.
- Code blocks: always specify language, add inline comments for non-obvious lines, split input/output into separate blocks when both are shown. Code is exempt from word caps.

---

## STEP 5: SAVE & DELIVER

- Save as a `.md` file, filename in kebab-case matching the document topic (e.g. `rate-limiting.md`), unless the user names a different path.
- The file's H1 title and the filename topic should match.

---

## REVIEW CHECKLIST BEFORE SAVING

1. **Questions:** every section heading is a reader question; nothing in the doc answers none of them.
2. **Tier match:** tier equals the question-count rule (Step 1).
3. **Slots:** each section uses exactly one template, slots in order, none added (§2.4).
4. **Caps:** no bullet >15 words, no paragraph >2 sentences, ≤1 sentence before a section's content (§2.2).
5. **No repeats:** no idea stated twice; no item from the cut list (§2.5); Key Idea doesn't restate a slot.
6. **Visuals:** every visual matches a §3.1 trigger; every trigger that fired has its visual.
7. **Anchor check:** every ToC link points to an explicit `<a id="...">` anchor that exists.
8. **Heading hierarchy:** at most one H1 (the title).
9. **Nothing wrongly collapsed:** no primary code or content the reader needs inline sits in `<details>` (§3.6).
10. **Math check:** formulas meeting §3.9 use LaTeX; literal `$` escaped `\$`; no bare `|` in table math; no LaTeX in Mermaid labels; block math inside callouts/lists uses ```` ```math ````.
11. **Mermaid check:** every diagram stays in the §3.3 renderer-safe subset (`-->|label|` edges, core shapes, ASCII labels, no emoji, `classDef` styling, no nested subgraphs), passed `mmdc` if available, and no label starts with a Markdown marker (`-`, `+`, `*`, `1.`, `#`).
