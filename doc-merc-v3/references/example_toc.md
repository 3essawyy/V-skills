# Table of Contents — Template

The exact format to use for Tables of Contents in generated guides. This replaces the v1 auto-slug anchor scheme (see "Why the change" below).

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

Explicit `<a id="...">` anchors sidestep the whole problem: the anchor is whatever you say it is, in every renderer that supports HTML-in-Markdown (which is effectively all of them).

---

## Real Example (from an ISTQB-style guide)

```markdown
## Table of Contents

1. [Test Design Techniques — Black-Box](#part-1)
2. [Test Design Techniques — White-Box](#part-2)
3. [Experience-Based Techniques](#part-3)
4. [Test Process Activities](#part-4)
5. [Defect Management](#part-5)
6. [Static Testing](#part-6)
7. [Test Management](#part-7)
8. [Verification vs. Validation](#part-8)
```

```markdown
<a id="part-1"></a>
## PART 1 — Test Design Techniques — Black-Box

...

<a id="part-2"></a>
## PART 2 — Test Design Techniques — White-Box

...
```

---

## Rules

- Number every ToC item (1, 2, 3...).
- Each item links to its matching PART heading's explicit anchor.
- ToC appears immediately after the title block and `---` separator.
- After the ToC, add another `---` before PART 1 begins.
- PART headings are **H2** (`##`), not H1 — only the document title is H1.
- ToC is only included for Tier 2 docs with 4+ sections, or any Tier 3 doc (see SKILL.md Step 1). Skip it for short/quick documents.
- If the guide is split into multiple files, the index file's ToC links to the separate files instead of anchors.
