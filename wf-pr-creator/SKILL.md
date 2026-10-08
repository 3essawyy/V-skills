---
name: wf-pr-creator
description: End-to-end Pull Request packaging and documentation workflow. Audits commit history hygiene, decomposes git diffs into file-by-file rationales, detects single/multi-repo topologies, and generates standardized Markdown PR documentation. Use when preparing, packaging, reviewing, or drafting Pull Requests (e.g., "create PR", "make PR", "package PR", "draft PR", "prepare PR", "PR workflow", "generate PR description").
---

# PR Creator Workflow (`wf-pr-creator`)

A structured, end-to-end workflow skill for auditing, packaging, and drafting enterprise-grade Pull Request documentation across single-repo, multi-repo, and decoupled architectures.

---

## 🧭 Workflow Lifecycle

```
[Phase 1: Topology Discovery] ──► Detect single vs multi-repo & upstream target
              │
[Phase 2: Git Hygiene Audit]  ──► Audit commits, flag WIP/personal tags, offer squash
              │
[Phase 3: Diff Decomposition] ──► Analyze git diff --stat & extract "What & Why"
              │
[Phase 4: Document Synthesis] ──► Format standard 4-section canonical PR document
              │
[Phase 5: Output & Storage]   ──► Save to TCs/PRs markdown folder & emit compare URLs
```

---

## Phase 1: Environment & Topology Discovery

Before analyzing changes, determine the workspace structure and target upstream branch:

1. **Topology Detection:**
   * **Single Repository:** The workspace root contains `.git/`.
   * **Multi-Repo / Decoupled Triad / Submodules:** Subdirectories contain their own independent `.git/` directories (e.g., orchestrator, assertion engine, configuration).
   * *Action:* If multi-repo is detected, iterate through all modified sibling repositories and generate isolated PR packages for each active branch.

2. **Branch Resolution:**
   * Identify current working branch: `git branch --show-current`
   * Identify target base branch: Default to `dev` or `main`/`master` unless specified by user.
   * Verify remote tracking: Run `git fetch origin <target_branch>` and detect if the remote branch head has diverged.

---

## Phase 2: Git Hygiene & Commit Squashing Audit

Clean, atomic conventional commits prevent upstream merge clutter and maintain audit traceability.

1. **Inspect Commit History:**
   * Run: `git log origin/<target_branch>..HEAD --oneline`
2. **Audit Checkpoints:**
   * **WIP / Personal Tags:** Check for developer tags (e.g., `kt(...)`, `test(...)`, `wip`, `temp`, `debugging`).
   * **Intermediate Churn:** Check for repetitive patch commits (e.g., `Updated regex`, `fix typo`, `revert`).
3. **Hygiene Action:**
   * If commit history contains intermediate noise, advise the user and offer a clean soft-reset:
     ```bash
     git reset --soft origin/<target_branch>
     ```
   * Formulate a single atomic Conventional Commit message:
     ```text
     <type>(<scope>): <concise imperative headline>
     - Detailed change bullet 1
     - Detailed change bullet 2
     ```
   * *Mandate:* Always ask or confirm before executing commit commands.

---

## Phase 3: Diff Decomposition & Rationalization

Analyze the exact code changes to build meaningful technical documentation:

1. **Inspect Diff Statistics:**
   * Run: `git diff --stat origin/<target_branch>`
   * Run: `git diff origin/<target_branch>` (targeted surgical review of modified hunks)
2. **Categorize Changes by Architectural Layer:**
   * **Core Logic / Application Code:** Production functionality, algorithms, class abstractions.
   * **Test Suites / Mediators / Assertions:** Verification scripts, fixtures, assertion builders.
   * **Configuration & CI/CD Pipelines:** Jenkinsfiles, GitHub Actions, parameters, CSV suites, JSON criteria.
   * **Environment & Metadata:** `.gitignore`, dependencies, build configs.
3. **Decompose Every File:**
   For every changed file, explicitly answer:
   * **What Changed:** Specific methods, parameters, selectors, or regexes modified.
   * **Why:** The architectural driver, defect root cause, or contract specification requiring the change.

---

## Phase 4: Canonical 4-Section PR Synthesis

Format the PR description strictly adhering to the standard 4-section template (see [pr_template.md](references/pr_template.md)):

```markdown
# <type>(<scope>): <headline>

## 🎯 Executive Overview & Architectural Context
- High-signal executive summary of the problem, motivation, and solution.
- Explanation of system-level runtime behavior across environments.

---

## 📂 Detailed File-by-File Changes

### 1. `path/to/file` (<New File | Modified | Deleted>)
* **What Changed:** Bullet points detailing the exact modifications.
* **Why:** The technical rationale, architectural pattern, or bug fix reason.

```<language>
// Illustrative code snippet or diff highlight
```

---

## 🔗 Verification Evidence & Test Execution Report
- Direct hyperlinks to passing CI/CD builds (e.g., Jenkins Orchestrator HTML report, GitHub Actions run).
- Automated test framework outputs (`pytest`, `mvn test`, etc.) with pass/fail counts.
- Terminal logs or reproduction transcripts proving green execution.

---

## ⚠️ Post-Merge Action Required
- Critical operational tasks required immediately following upstream merge:
  * Reverting temporary branch-test overrides (e.g., Pearl scripts or submodules cloning feature branches back to `dev`).
  * Feature flag activations, secret configurations, or downstream service syncs.
  * If none required, state: *"None. Zero downstream migration or config repointing required."*
```

---

## Phase 5: Output, Storage & Compare URLs

1. **Terminal Presentation:**
   * Always output the complete, copy-pasteable Markdown block in monospace code fencing inside the chat response.
2. **Local Persistence (Markdown File Storage):**
   * Detect repository documentation patterns to write a permanent markdown record:
     * **Pattern A (Test Case Docs):** If `docs/TCs/<FeatureName>/` exists, write to:  
       `docs/TCs/<FeatureName>/PR_<REPO_NAME>_<FEATURE>.md`
     * **Pattern B (Dedicated PR Docs):** If `docs/PRs/` exists, write to:  
       `docs/PRs/PR_<REPO_NAME>_<FEATURE>.md`
     * **Pattern C (Root / Standard Docs):** Otherwise, write to `docs/PR_<FEATURE>.md` or project root.
3. **Dispatch URLs:**
   * Emit direct, clickable GitHub/GitLab compare URLs:
     `https://<server>/<org>/<repo>/compare/<target_branch>...<source_branch>?expand=1`
