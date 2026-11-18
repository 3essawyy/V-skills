# Table of Contents — Template

The exact format to use for Tables of Contents in generated guides. Headings are reader questions (v6); anchors are explicit. This replaces the v1 auto-slug anchor scheme (see "Why the change" below).

---

## Standard ToC Format

```markdown
## Table of Contents

1. [First Major Section Title](#part-1)
2. [Second Major Section Title](#part-2)
3. [Third Major Section Title](#part-3)
4. [Fourth Major Section Title](#part-4)
```

Each entry links to an explicit anchor placed directly above the matching PART heading:

```markdown
<a id="part-1"></a>
## PART 1 — First Major Section Title
```

---

## Anchor ID Rules

1. Anchor ids are short and sequential — they do **not** need to encode the heading text.
2. Top-level parts: `part-1`, `part-2`, `part-3`, ...
3. Numbered subsections (if they also need a direct link, e.g. from a "See also"): `part-2-1`, `part-2-2`, ...
4. Place the `<a id="...">` tag on its own line, immediately above the heading it anchors.
5. Never rely on a renderer's auto-generated slug for a ToC link — see below.

---

## Why the Change from Auto-Slugged Anchors

The original approach derived anchors from the heading text (lowercase, spaces → hyphens, em-dash → `--`). That specific mapping happens to match GitHub's slugger, but **other renderers slugify differently** — VS Code's Markdown preview, Obsidian, and static site generators handle punctuation, em-dashes, and repeated hyphens inconsistently. A ToC built this way can render correctly on GitHub and silently 404 everywhere else.

Question headings make this worse — renderers disagree on whether `?` survives the slug. Explicit `<a id="...">` anchors sidestep the whole problem: the anchor is whatever you say it is, in every renderer that supports HTML-in-Markdown (which is effectively all of them).

---

## Real Example (Tier 3 — PARTs group question H3s)

```markdown
## Table of Contents

1. [Request Path](#part-1)
   - [How does a request reach the service?](#part-1-1)
   - [How is the caller authenticated?](#part-1-2)
2. [Storage](#part-2)
   - [Where is session state kept?](#part-2-1)
   - [What happens when the cache node dies?](#part-2-2)
3. [Scaling Decisions](#part-3)
   - [Why shard by tenant, not by user?](#part-3-1)
```

```markdown
<a id="part-1"></a>
## PART 1 — Request Path

<a id="part-1-1"></a>
### 1.1 How does a request reach the service?

**Trigger:** ...
```

**Tier 2** — no PARTs; the ToC lists the question H2s directly:

```markdown
1. [What does the gateway do?](#part-1)
2. [How does a request flow through it?](#part-2)
3. [How are routes configured?](#part-3)
4. [Why a gateway instead of direct calls?](#part-4)
```

---

## Rules

- Number every top-level ToC item (1, 2, 3...).
- Each item links to its heading's explicit anchor.
- Link text = the heading text (the question). Never paraphrase it.
- ToC appears immediately after the H1 and `---` separator, followed by another `---`.
- PART headings are **H2** (`##`), not H1 — only the document title is H1.
- ToC is included for Tier 2 docs with 4+ questions, and every Tier 3 doc (see SKILL.md Step 1). Tier 3 ToCs list question H3s nested under their PART.
- If the guide is split into multiple files, the index file's ToC links to the separate files instead of anchors.
