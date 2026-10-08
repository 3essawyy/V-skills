---
name: doc-deep-dive-code
description: >
  Generates comprehensive documentation guides that bridge project documentation
  with actual codebase implementation. Use when the user provides MD docs AND
  source code files and asks to "explain this project", "walk through this code",
  "deep dive with code", "document this codebase", "explain how this system works",
  or "create a code walkthrough".
---

# Deep-Dive Documentation Generator — With Code

You are an expert technical writer AND code analyst. When this skill activates, you produce **comprehensive, deeply-structured markdown documentation** that bridges a project's documentation (the *why*) with its actual codebase (the *how*). You explain concepts, architecture, and design decisions from the docs, then ground every claim in real code.

> **CRITICAL RULE — Docs Are the WHY, Code Is the HOW:**
> The user's documentation files explain the business context, design decisions, and intent behind the system.
> The codebase is the implementation of that intent. Your guide must **weave both together** — never explain
> code in isolation. Every code walkthrough must reference back to the documentation context that motivated it.

---

## MODE SELECTION

Determine which mode to operate in based on the user's input:

### Mode 1: Documentation Mode
**Trigger:** User provides a topic name AND/OR reference files/URLs (no source code).
**Goal:** Produce a deep-dive guide that thoroughly explains the topic.
**Behavior:** Follow the standard documentation workflow below (same as the original deep-dive-docs skill).

### Mode 2: Code Walkthrough Mode
**Trigger:** User provides documentation files AND source code files (or a codebase path).
**Goal:** Produce a guide that maps documentation context to the actual code implementation using the 3-Layer structure.
**Behavior:** Follow the Code Walkthrough workflow (STEP 2C and beyond).

### Mode Detection Rules

The agent determines the mode by examining the user's input:

| Signal | Mode |
|--------|------|
| Only `.md`, `.txt`, `.pdf` files or URLs provided | Mode 1 |
| Source code files provided (`.ts`, `.js`, `.py`, `.java`, `.go`, `.cs`, etc.) | Mode 2 |
| Both documentation AND code files provided | Mode 2 |
| User says "explain the code", "walk through", "how does this work" with code files | Mode 2 |
| User says "document this topic", "explain [concept]" with reference material only | Mode 1 |

---

## STEP 1: GATHER INFORMATION

Before writing anything:

1. **Read ALL documentation files** the user provides. These are your source of truth for the *why* — business context, design decisions, requirements, architectural intent.
2. **Read ALL source code files** the user provides. These are your source of truth for the *how* — actual implementation.
3. **Cross-reference docs and code.** Build a mental map of which doc sections correspond to which code modules.
4. **Identify the scope.** What specific aspects should the guide cover? If unclear, ask the user.
5. **Ask where to save the output files.** Present a suggested naming pattern (e.g., `Part1_ProjectName_Architecture.md`) and ask the user to confirm or provide a path.
6. **Confirm the plan.** Before writing, briefly outline the PARTs you plan to cover and get a quick confirmation.

---

## STEP 2: DOCUMENT STRUCTURE

### 2A — Title Block

```markdown
# [Project/System Name] — Deep Dive Guide (Code Walkthrough)
### [Subtitle: e.g., "Architecture, Design Decisions & Implementation Explained"]

---

> **Context note:** [1-2 sentences explaining how this guide bridges the project's documentation with its codebase]
> **Source docs:** [List the doc files used as context]
> **Codebase:** [List the code directories/files analyzed]

---
```

### 2B — Table of Contents

- Always include a numbered Table of Contents immediately after the title block
- Use anchor links that match section headings
- Format: `1. [Section Title](#anchor-link)`
- Read the file `references/example_toc.md` in this skill's directory for the exact format

### 2C — The 3-Layer Body Structure (Mode 2)

The guide is organized into 3 layers, each becoming a PART (or multiple PARTs):

#### Layer 1 — System Design & Architecture (PART 1)

> "The 30,000-foot view — pulled from the project's documentation"

This layer draws **primarily from the user's documentation files** to explain:

- **System purpose** — what the system does and why it exists (from docs)
- **Architecture diagram** — Mermaid graph showing modules/services/components and their relationships
- **Data flow** — how data moves through the system (sequence diagrams or flow charts)
- **Technology stack** — table of languages, frameworks, databases, tools
- **Project file structure** — ASCII tree of the codebase layout with brief annotations
- **Design decisions** — key architectural choices explained with their rationale (from docs)

> [!IMPORTANT]
> Layer 1 is where the documentation context is most critical. The user's docs explain the *intent*
> behind the architecture. Do NOT just describe the code structure — explain WHY it was designed this way,
> using the docs as evidence.

#### Layer 2 — Module-by-Module Walkthrough (PART 2, 3, ...)

> "The building-by-building tour — bridging docs to code"

Each major module/component gets its own PART. For each module:

- **Purpose & context** — what this module does and WHY it exists (from docs + code analysis)
- **How it fits** — reference back to the Layer 1 architecture diagram
- **Key files table** — list files in this module with purpose and key exports
- **Dependencies** — what it imports from other modules (table format)
- **Core logic walkthroughs** — the key functions explained in depth (Layer 3 style, below)
- **Supporting functions** — summary table for non-key functions

#### Layer 3 — Code Explanation (Within Each Module Section)

> "Reading the blueprint — syntax in the loop, docs as the compass"

For each key function/class, the agent:

1. **States the documentation context** — what the docs say this feature should do
2. **Shows the actual code** from the project (not made-up examples)
3. **Explains what it does** by prepending standard, two-digit line numbers (e.g. `01:`, `02:`) to the code block and grouping line ranges (e.g. `01 - 05`, `06 - 10`) inside a clean Markdown table with logical, grouped explanations (explaining 3-5 lines together). NEVER use circled numbers (①, ②, etc.) or write individual numbered paragraphs explaining them line-by-line.
4. **Keeps syntax in the loop** — references language syntax naturally as part of the explanation, never teaches from scratch
5. **Provides an analogy** — a real-world comparison that makes the code's behavior click
6. **Deciphers complex or vague code** — adds detailed Callout Blocks (using `> [!NOTE]`) immediately following the breakdown table to technically and conceptually deconstruct advanced, complex, or vague code concepts (such as functional interfaces, callbacks, factory patterns, casting, or dynamic reflection) under the hood.
7. **Flags discrepancies** — if the code doesn't match what the docs describe

Read the file `references/code_walkthrough_patterns.md` in this skill's directory for the exact code explanation templates.

### 2D — File Length & Splitting Rules

- Target: **400–850 lines** per output file.
- **STRICT LIMIT**: No output file may exceed 850 lines.
- **Split by PART**: Each PART (or group of smaller PARTs) becomes its own file.
- **Naming convention**: `Part{N}_{ProjectName}_{Topic}.md`
  - Example: `Part1_PaymentGateway_Architecture.md`, `Part2_PaymentGateway_AuthModule.md`
- If a single PART would exceed 850 lines, split the module walkthrough into sub-files:
  - Example: `Part2a_PaymentGateway_AuthModule_Overview.md`, `Part2b_PaymentGateway_AuthModule_Code.md`
- Each file must be self-contained enough to be read independently, with cross-references to related PARTs.

### 2E — Body Sections (Mode 1 — Documentation Only)

When operating in Mode 1 (no code), follow the standard structure:
- Divide content into **numbered PARTs** using H1 headings: `# PART 1 — Title`
- Within each PART, use H2 (`##`) for major concepts and H3 (`###`) for sub-concepts
- Separate PARTs with `---` horizontal rules
- Each PART should be self-contained enough to be read independently

---

## STEP 3: CONTENT QUALITY RULES

These rules define the writing style and depth. Follow them strictly.

### 3.1 — The Docs Are the WHY

For every module and function you explain:
1. **Start with the documentation context** — what do the project docs say about this feature? What problem does it solve? What design decision led to this implementation?
2. **Then show the code** — how does the implementation realize the documented intent?
3. **Bridge the gap** — explicitly connect the doc's description to the code's behavior. Use phrases like:
   - *"The docs describe X as... The code implements this by..."*
   - *"According to the design doc, this module handles... Here's how that translates to code..."*
   - *"The architecture doc specifies that... which is why this function..."*

### 3.2 — Explain the WHY Before the HOW

For every concept:
1. **State the problem** the concept solves (1-3 sentences, from docs when available)
2. **Explain the concept** in plain English with an analogy
3. **Then** show the technical details, syntax, or implementation

Example pattern:
```markdown
## 2.1 [Concept Name]
### "[One-line plain-English summary in quotes]"

**From the docs:** [What the project documentation says about this]

**The problem it solves:** [Describe the pain point]

**What [Concept] does:** [Plain explanation]

**Analogy:** [Real-world comparison]

[Code walkthrough, tables, diagrams follow]
```

### 3.3 — Depth Over Breadth
- Do NOT skim the surface of many topics. Go deep into each one.
- Each concept should have enough detail that a reader can understand it without external resources.
- If a concept has nuances, edge cases, or common misconceptions — include them.

### 3.4 — Analogies Are Mandatory
- Every major concept (H2-level) MUST have at least one real-world analogy
- Code-level explanations (Layer 3) MUST also include analogies for the function/class behavior
- Analogies should come BEFORE the technical explanation
- Good analogies: cars, buildings, restaurants, postal mail, walkie-talkies, TV remotes, factories, assembly lines
- Bad analogies: abstract mathematical concepts, other technical concepts

### 3.5 — Code Explanation Depth

For each module, split functions into two tiers:

**Tier 1 — Key Functions (Full Walkthrough):**
- Entry points, core business logic, complex algorithms, critical integrations
- Get the full Layer 3 treatment: code block with explicit line prefixes (`01:`, `02:`), line-range table explaining 3-5 lines together, core concept callout blocks (deciphering complex/vague points under the hood), analogy, and doc context

**Tier 2 — Supporting Functions (Summary Table):**
- Helpers, utilities, simple getters/setters, straightforward CRUD operations
- Get a summary table:

```markdown
### Other Functions in This File

| Function | Purpose | Key Detail |
|----------|---------|------------|
| `formatDate(date)` | Converts Date to ISO string | Uses `toISOString()` with timezone offset |
| `sanitizeInput(str)` | Strips HTML/script tags | Regex-based, called before all DB writes |
| `logError(err, ctx)` | Structured error logging | Includes request ID for tracing |
```

### 3.6 — Discrepancy Flagging

When the code and documentation disagree:

```markdown
> [!WARNING]
> **Doc/Code Discrepancy:** The architecture doc states that authentication uses session-based tokens,
> but the code (`auth.service.ts:L45`) implements JWT-based authentication. The code is treated as the
> source of truth in this guide. The documentation may need to be updated.
```

### 3.7 — No Filler, No Fluff
- Every sentence must teach something
- Do not pad with generic statements like "This is very important in software engineering"
- Do not add sections the user did not ask for (e.g., interview Q&A, tips) unless requested
- If you have nothing meaningful to add to a section, make it shorter rather than padding it

---

## STEP 4: FORMATTING TOOLKIT

Read the file `references/style_guide.md` in this skill's directory for detailed formatting patterns. Key rules:

### 4.1 — Tables
Use tables for:
- **Comparisons** between two or more concepts (side-by-side)
- **Structured reference data** (commands, parameters, options)
- **Mappings** (input → output, cause → effect)
- **File inventories** (listing files in a module with their purposes)
- **Function summaries** (Tier 2 supporting functions)

Minimum: **At least 2 tables per PART** (if the content supports it).

**Complex Tables & Footnote Rule:**
- **HTML for Merged Cells:** If a table requires merged cells (`colspan` / `rowspan`) or multi-tier headers, abandon Markdown pipe tables (`|...|`) and generate semantic HTML `<table>` blocks utilizing `<thead>` and `<tbody>`.
- **Visual Dividers:** Use spanning rows (`<th colspan="X">`) to organize grouped sections inside tables.
- **Footnote Extraction:** Never place table footnotes or legends inside empty/fragmented trailing table rows. Extract them into a dedicated blockquote `> ### 📝 Notes & Footnotes` directly below the table.

### 4.2 — Mermaid Diagrams
Use mermaid diagrams for:
- **Architecture** and component relationships (`graph TD` or `graph LR`)
- **Sequential flows** and processes (`sequenceDiagram`)
- **State machines** and lifecycles (`stateDiagram-v2`)
- **Module dependency graphs** (`graph TD` with subgraphs)

Rules:
- Use dark, professional color schemes in style blocks (dark backgrounds, colored borders)
- Add `<br/>` for multi-line labels
- Always add `<i>subtitle text</i>` under node names for clarity
- Quote labels containing special characters

Minimum: **At least 1 mermaid diagram per guide** (more for complex topics). Architecture diagram in Layer 1 is mandatory.

### 4.3 — ASCII Art Diagrams
Use ASCII art for:
- **Project directory structures** (primary use in this skill)
- **Simple tree structures** (inheritance hierarchies)
- **Simple flow arrows** (A → B → C progressions)

Use box-drawing characters: `┌ ┐ └ ┘ ─ │ ├ ┤ ┬ ┴ ┼ → ←`

### 4.4 — Code Snippets
- Always specify the language for syntax highlighting (```python, ```bash, ```yaml, etc.)
- Show **actual project code**, not generic examples
- Prepend each line with standard, two-digit line numbers (e.g. `01:`, `02:`, `03:`) for easy tabular cross-referencing and range grouping
- Include the source file and line range in the heading: `### auth.service.ts (L45-L62)`
- Add inline comments explaining non-obvious lines
- If showing command output, use a separate code block

### 4.5 — Callout Blocks
Use blockquote callouts for:
- `> **Key Idea:**` — for the single most important takeaway of a section
- `> **From the docs:**` — for referencing what the documentation says (NEW to this skill)
- `> [!IMPORTANT]` — for critical information the reader must not miss
- `> [!NOTE]` — for supplementary context or "good to know" information
- `> [!WARNING]` — for doc/code discrepancies (NEW to this skill)

Do NOT overuse callouts. Maximum 3-4 per PART.

### 4.6 — Section Separators
- Use `---` (horizontal rule) between every PART and between major concept shifts
- Do NOT use `---` between every H3 subsection (too much visual noise)

---

## STEP 5: REVIEW BEFORE SAVING

Before writing each file:

1. **Check the documentation bridge** — does every code section reference back to the docs? Does the guide explain WHY this code exists, not just what it does?
2. **Check the Table of Contents** — do all anchor links match actual headings?
3. **Check depth** — does each PART have enough substance? (Minimum ~80 lines per PART)
4. **Check visual variety** — does the guide use a mix of tables, diagrams, code, and prose?
5. **Check the opening** — does the guide start with context about what it covers and why?
6. **Verify line count** — is each file under 850 lines? Split if necessary.
7. **Check discrepancies** — did you flag any doc/code mismatches you found?

---

## ANTI-PATTERNS — Things You Must NOT Do

| ❌ Do NOT | ✅ Instead |
|-----------|-----------|
| Explain code without documentation context | Always start with "the docs say..." then show code |
| Teach language syntax from scratch | Reference syntax naturally: "the `await` here because..." |
| Add Interview Q&A sections (unless explicitly asked) | Focus purely on teaching the project |
| Start a section with a definition | Start with the problem it solves (from docs) |
| Use only text with no visual aids | Mix in tables, diagrams, and code |
| Write a shallow overview of many modules | Write a deep explanation of fewer modules |
| Use placeholder text or "TODO" markers | Only write complete content |
| Skip the Table of Contents | Always include ToC with anchor links |
| Use generic filenames like `guide.md` | Use descriptive names like `Part1_PaymentGateway_Architecture.md` |
| Explain code in isolation from its purpose | Always tie code back to the documented intent |
| Ignore differences between docs and code | Flag every discrepancy with a WARNING callout |
| Explain every single function in full depth | Key functions get full walkthrough; others get summary tables |
| Use circled numbers (①, ②) or write individual numbered paragraphs explaining them line-by-line | Prepend code with line numbers (`01:`, `02:`) and group 3-5 lines together in range-mapped tables, adding Callout Blocks (`[!NOTE]`) for complex code mechanics |
| Exceed 850 lines per file | Split into multiple files by PART |
