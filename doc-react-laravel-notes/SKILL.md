---
name: doc-react-laravel-notes
description: Generates a numbered, indexed set of Markdown study-note files (00-index.md, 01-topic.md, 02-topic.md...) for React frontend, Laravel/PHP backend, and full-stack React+Laravel topics, each with an embedded Mermaid diagram and working code examples. Use this skill whenever the user hands off a topic, a batch/list of topics, or raw subtitle/transcript text from a course or video to turn into study notes for React, Laravel, or a React+Laravel project, asks for "notes on X", wants Markdown files with Mermaid diagrams for a frontend/backend learning sequence, or is studying to build a React+Laravel project. Trigger even on a bare list of topics or a raw subtitle dump with no further instruction — treat that content itself as the request.
---

# React/Laravel Study Notes

Turns a list of topics into a numbered sequence of Markdown study-note files that build toward being able to implement a real React + Laravel project.

## Assumed reader background

Write for someone who already has:
- A solid **Node.js backend engineering** background (comfortable with servers, routing, middleware-as-a-concept, async, REST APIs, ORMs in general)
- **HTML/CSS fundamentals**
- **No prior React or Laravel experience**

Do NOT re-explain: what an API is, what HTTP methods are, general async/await, general programming concepts, or anything a competent Node.js backend dev already knows. DO explain: React/Laravel-specific idioms, conventions, and "the React way" / "the Laravel way" of doing things they'd otherwise do differently in Node.

## Workflow

1. **Get the topic list.** Input arrives in one of two forms:
   - **A plain topic list** — one per line, comma-separated, or already numbered. Preserve the given order as the learning sequence.
   - **Raw subtitle/transcript text** from a course or video (e.g. an `.srt`/`.vtt` file, or pasted subtitle text, often hours long). In this case:
     a. Strip timestamps, cue numbers, and formatting artifacts — work from the spoken content only.
     b. Segment the transcript into a sequence of **distinct teaching topics** based on genuine content shifts (a new concept, a new feature, a new file/tool introduced), not arbitrary time chunks. An 11-hour crash course might yield anywhere from ~15 to 40+ topics — don't force an artificial count.
     c. Merge trivial/filler segments (intros, "let's take a break," recaps that don't add new content) into the topic they belong with, or drop them if they carry no teaching content.
     d. **Show the extracted topic list to the user before generating files**, in order, so they can reorder, merge, split, or cut anything before you generate a potentially large batch. Skip this confirmation step only if the user has explicitly said to just go ahead.
   - If a single given topic is very broad (e.g. just "React"), don't silently expand it into many files — ask the user to confirm scope first, same as above.
2. For each topic, generate one file: `NN-kebab-case-topic.md` (zero-padded two-digit prefix, starting at `01`).
3. Save all files to `/mnt/user-data/outputs` (flat folder — no subfolders unless the batch has 15+ topics, in which case ask whether to split into `frontend/` and `backend/`).
4. **Generate `00-index.md`** — see "Index file" below — so the whole set is navigable as one entry point.
5. Call `present_files` with the index file first, then all note files. Don't paste full file contents into the chat reply — the files ARE the deliverable.

## Note structure (every file)

1. **`# Title`** — the topic name, plain and specific
2. **Why this matters** (1–2 sentences) — only include if the practical motivation isn't obvious from the title; skip otherwise, don't pad
3. **Concept** — explanation calibrated to the assumed background above
4. **Diagram** — exactly one Mermaid diagram, picked to fit the topic:
   - `sequenceDiagram` — request/response cycles, lifecycle timing, event order
   - `flowchart` — data flow, control flow, decision branches
   - `graph TD` — component trees, module/dependency structure
   - `classDiagram` — OOP structure (common for Laravel models/services, rare for React)
   - Keep it focused: 5–10 nodes max. Don't try to diagram the whole topic, just the part that's spatial/sequential enough to need a picture.
5. **Code example(s)** — working, idiomatic code:
   - React topics → JSX/React code
   - Laravel topics → PHP/Laravel code
   - Full-stack topics → both sides, clearly separated with headers
   - **Node.js-equivalent rule**: for a Laravel/backend concept that's non-trivial and doesn't map 1:1 onto plain Express/Node (e.g. service providers, Eloquent relationships/accessors, form requests, queues, middleware groups, Artisan/migrations), add a short **"Node.js equivalent"** callout showing the closest Express/Node.js pattern side by side. Skip this callout when the concept is basically identical to what they already do in Node (e.g. a plain GET route) — it would just be noise.
6. **Gotchas / production notes** — short bullet list of real pitfalls or decisions that matter in an actual project. Never include deprecated APIs, legacy class-component patterns, superseded Laravel conventions, or other historical trivia that won't help him ship — current, actively-used practice only.
7. **Next up** — one line pointing to what the next numbered file builds toward. Omit on the last topic in the batch.

## Depth calibration

Target "medium-deep": enough that he can actually build on it in a real project, not an exhaustive reference doc and not a shallow cheat sheet. As a rough guide, ~150–350 lines of Markdown, scaled to the topic's actual complexity — a simple topic shouldn't be padded to hit a line count, and a genuinely dense topic (e.g. Eloquent relationships) can run longer.

## Index file (`00-index.md`)

Every batch gets one `00-index.md`, generated last (after you know the final topic list and any files that got merged/split during generation). It's the entry point for navigating the set:

1. **`# <Course/Batch title>`** — short, descriptive, inferred from the topics (e.g. "React + Laravel Crash Course Notes")
2. **One-line summary** of what the batch covers and the assumed background (Node.js + HTML/CSS, no prior React/Laravel)
3. **A table of contents**, in learning order, as a Markdown table or list with a relative link to each file plus a one-line description of what it covers:
   ```markdown
   | # | Topic | Covers |
   |---|-------|--------|
   | 01 | [useState and useEffect](01-react-usestate-useeffect.md) | Component state, side effects, cleanup |
   | 02 | [Eloquent Relationships](02-laravel-eloquent-relationships.md) | hasMany/belongsTo, eager loading, N+1 |
   ```
4. If the batch mixes frontend and backend topics, you may add a second grouped view (e.g. "Frontend" / "Backend" / "Full-stack" subsections listing the same links by category) **in addition to** the ordered table — don't replace the learning-order table, since order matters more than category here.
5. Keep the index itself short — it's a map, not a summary of every file's content. Descriptions are one line each.

If notes are later added to an existing batch, regenerate `00-index.md` to include them rather than leaving it stale.

## Mermaid specifics

- Always use fenced ` ```mermaid ` code blocks so they render.
- Use current Mermaid syntax (no deprecated directive styles).
- Label nodes with real terms from the topic, not generic "Step 1 / Step 2" placeholders.

## File naming & organization

- `01-react-hooks-basics.md`, `02-laravel-routing.md`, etc. — always two-digit zero-padded, continuing the count across the whole batch regardless of frontend/backend mix, unless the user asked for separate frontend/backend sequences.
- Flat output folder by default.

## Input handling

- Accept topics as a raw list — one per line, comma-separated, or already numbered by the user. Normalize into the `NN-slug.md` scheme regardless of how they were passed in.
- Accept raw subtitle/transcript text pasted directly in chat, or as an uploaded file (`.srt`, `.vtt`, `.txt`). If it's an uploaded file not already in context, read it from `/mnt/user-data/uploads` first — check for a relevant file-reading skill if the format needs it. Then follow the transcript-segmentation steps in the Workflow section above.
- If the user passes a mix of React and Laravel topics without specifying order, keep the order they gave — don't silently group by frontend/backend.
