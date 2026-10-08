# Standard Pull Request Template

Use this canonical 4-section layout when formatting Pull Request descriptions.

```markdown
# <type>(<scope>): <concise imperative headline>

## 🎯 Executive Overview & Architectural Context
A clear, high-signal narrative explaining:
- **Problem Statement:** What issue, limitation, or requirement prompted this change?
- **Architectural Solution:** How does this implementation address the problem at the system level?
- **Workflow Impact:** How does this change behave at runtime across relevant environments/tiers?

---

## 📂 Detailed File-by-File Changes

### 1. `path/to/file1.ext` (<New File | Modified | Deleted>)
* **What Changed:**
  - Bulleted summary of specific functions, classes, configuration keys, or regexes changed.
* **Why:**
  - Architectural rationale, bug explanation, or interface compliance justifying the edit.

```<language>
// Highlight critical diff snippet or new implementation pattern
```

### 2. `path/to/file2.ext` (<New File | Modified | Deleted>)
* **What Changed:**
  - Bulleted summary of changes.
* **Why:**
  - Rationale for the change.

---

## 🔗 Verification Evidence & Test Execution Report
Concrete, verifiable proof that the code works as expected:
* **Automated Test Results:** Command executed and pass/fail summary (e.g., `pytest`, `mvn test`, `npm test`).
* **CI/CD Pipeline Evidence:** Direct hyperlink or build ID to passing CI/CD orchestrator run:
  👉 [View CI Build Report](<URL>)
* **Log Snippets / Terminal Proof:** Console excerpt demonstrating green exit status or expected behavior.

---

## ⚠️ Post-Merge Action Required
Explicit operational or configuration tasks required immediately after merge:
* **Configuration Repointing:** Batch scripts, environment variables, or config branches that must be repointed back to default branches (e.g., `dev` or `main`).
* **Feature Flags / Secrets:** Any environment variables or tokens that must be activated on deployment.
* **Downstream Dependencies:** Other repositories, PRs, or microservices that need to be triggered or synced.
* *(If no post-merge action is required, explicitly state: "None. Zero downstream migration or config repointing required.")*
```
