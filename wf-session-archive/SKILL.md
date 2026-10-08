---
name: wf-session-archive
description: Consolidates, updates master findings, and archives active session logs in docs/sessions to deprecated_archive. Use when wrapping sessions, archiving sessions, consolidating session logs, updating master findings, or performing session refactoring across any project.
---

# Session Wrap and Archive

This skill provides a standardized, cross-project workflow to synthesize active session logs into consolidated **Master Findings** and archive legacy logs into **`deprecated_archive/`**.

## Why Session Archiving Matters
As projects grow, raw session markdown logs accumulate in `docs/sessions/`. These logs often contain temporary false leads, debugging dead-ends, and outdated assumptions. If left in active context, they become **"poison context"** for AI agents. This skill purifies active project knowledge into durable Master Journey files while safely preserving raw history behind explicit warning headers.

---

## Directory Topology Standard

Any project adhering to this documentation architecture maintains:

```text
docs/sessions/
├── master_findings/       # Verified, long-term architectural truth (Roman numerals)
│   ├── I_Journey_of_...md
│   ├── II_Journey_of_...md
│   └── ...
├── deprecated_archive/    # Historical logs prepended with [!WARNING] (not to be read by agents)
│   ├── 1._session_...md
│   └── ...
└── (top-level)            # Clean root; only holds brand new or currently active session logs
```

---

## Workflow: Step-by-Step Procedure

Follow these phases sequentially whenever triggered:

### Phase 1: Ingestion & Discovery

1. Locate the sessions folder: Check `docs/sessions/` (or search for `sessions/` relative to workspace root).
2. Scan for **active session files**: Identify all top-level `.md` files directly in `docs/sessions/` (excluding the `master_findings/` and `deprecated_archive/` subdirectories).
3. If no active top-level `.md` files exist, inform the user that `docs/sessions/` is already clean and exit.
4. Read and extract the critical takeaways from each active session:
   - **Architectural & Design Shifts:** Refactorings, structural utilities, teardown lifecycles.
   - **Feature Implementations:** Key endpoints, test suites, E2E orchestration handshakes.
   - **Discoveries & Gotchas:** Backend defects, validation gaps, unexpected framework behaviors, unbroken rules.

---

### Phase 2: Synthesis Strategy (Append vs. New Roman Numerals)

Inspect `docs/sessions/master_findings/` (create the directory if it does not exist) and decide the synthesis strategy:

1. **Thematic Pillars:**
   - Infer the relevant thematic domains based on the project's content (e.g., Architecture/Clean Code, API/Feature Implementations, Defects/Logic Mechanics, UI Automation).
2. **Decision Matrix:** Consult `references/master_findings_patterns.md` for full criteria:
   - **Append:** If the new content directly continues an existing theme and the file remains under ~250 lines, append a new numbered section to that master file and update its Table of Contents.
   - **Create New Roman Numeral:** If the content represents a new domain, a major milestone (e.g. Part 2), or would bloat an existing file past ~250 lines, allocate the next Roman numeral sequentially (`I`, `II`, `III`, `IV`, `V`, `VI`, `VII`, `VIII`, etc.).

---

### Phase 3: Writing Master Findings

Format all master findings according to the **`merc` aesthetic**:

1. **Header Block:** Include title, Roman numeral prefix (`[Roman]_Journey_of_[Domain].md`), and scope metadata callout block (`> **Scope:** ...`).
2. **Table of Contents:** Numbered section links matching document headings.
3. **Milestone Graph:** Include a Mermaid flowchart (`graph TD`) mapping the progression.
4. **Contrast Tables:** Summarize legacy vs. refactored behaviors and concrete impacts.
5. **Verified Golden Snippets:** Include only finalized, production-grade logic.

---

### Phase 4: Atomic Archiving Pipeline

Once the master findings are written and confirmed:

1. Run the deterministic archiver script:
   ```bash
   python <path-to-skill>/scripts/archive_sessions.py --dir docs/sessions
   ```
   *(Or run with `--dry-run` first if safety verification is needed).*

2. **What the script executes:**
   - Automatically ensures `docs/sessions/deprecated_archive/` exists.
   - Idempotently checks and prepends the universal deprecation block to each active log:
     ```markdown
     > [!WARNING]
     > **DEPRECATED ARCHIVE FILE**
     > This session log contains outdated context, historical assumptions, and potentially obsolete decisions. It is kept strictly for historical tracking. Do not use this file for LLM decision-making or active context ingestion. Please refer to the consolidated Master files in `docs/sessions/master_findings/` or current documentation for the accurate, verified project state.
     ```
   - Moves each processed file into `docs/sessions/deprecated_archive/`.

---

### Phase 5: Verification & Quality Check

1. Verify that `docs/sessions/` is clean:
   - Subdirectory `master_findings/` holds the updated or newly created Journey files.
   - Subdirectory `deprecated_archive/` holds the archived logs with warning headers.
   - The root of `docs/sessions/` contains no orphaned raw session files.
2. Provide a concise, high-signal report to the user summarizing:
   - Which master findings files were modified or created.
   - List of session files successfully moved to `deprecated_archive/`.
   - Clean state confirmation of `docs/sessions/`.
