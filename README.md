# Universal Agent Skills for Gemini CLI

A curated, production-tested suite of **Quality-of-Life (QoL)** skills for [Gemini CLI](https://github.com/google/gemini-cli). These skills expand your CLI agent's capabilities across technical documentation styling, presentation ingestion, architectural stress-testing, and Git workflow automation.

---

## 🚀 Skills Catalog

| Skill | Category | Primary Focus & Capabilities | Trigger Phrases |
| :--- | :--- | :--- | :--- |
| **`doc-merc-v4`** | Documentation | Formats beautiful, executive-grade Markdown with styled callouts, themed Mermaid diagrams, and boxed ASCII banners. | *"format this"*, *"beautify"*, *"merc-style"*, *"make a pretty doc"* |
| **`doc-deep-dive`** | Documentation | Produces deeply structured, publication-quality technical guides and architectural specifications. | *"deep dive into"*, *"create a guide"*, *"document this topic"* |
| **`doc-deep-dive-code`** | Documentation | Bridges reference documentation with actual codebases, producing step-by-step code walkthroughs. | *"code walkthrough"*, *"deep dive with code"*, *"explain this codebase"* |
| **`doc-react-laravel-notes`** | Study & Learning | Generates indexed study notes (`00-index.md`, `01-topic.md`...) with Mermaid sequence flows and code examples. | *"notes on React"*, *"Laravel study guide"*, *"transcribe lecture notes"* |
| **`convert-pptx-pdf2md-v1`** | Conversion | Ingests PDF slide decks into structured Markdown with dual visual co-existence (rendered diagrams + visible PNGs). | *"convert pdf deck"*, *"slides to markdown"*, *"extract presentation"* |
| **`convert-pptx2md-v2`** | Conversion | Converts `.pptx` presentations into Markdown with 2D spatial canvas reconstruction and shape-grid table synthesis. | *"convert pptx"*, *"powerpoint to md"*, *"parse presentation slides"* |
| **`wf-pr-creator`** | Engineering Workflow | End-to-end PR packager: audits commit history hygiene, decomposes git diffs, and synthesizes 4-section PR markdown. | *"create PR"*, *"package PR"*, *"draft PR description"*, *"PR workflow"* |
| **`wf-session-archive`** | Engineering Workflow | Synthesizes active CLI chat logs into durable Roman-numeral Master Findings and safely archives poison context. | *"archive sessions"*, *"wrap session"*, *"consolidate findings"*, *"session refactor"* |
| **`wf-grill-me`** | Design & Architecture | Relentless Socratic interview partner that probes architectural edge cases and assumptions until consensus is reached. | *"grill me"*, *"stress test my plan"*, *"review my design aggressively"* |

---

## 📦 Installation & Setup

Gemini CLI automatically discovers skills residing in your personal configuration directory:

### 1. Clone into your Gemini skills directory
```bash
# Windows (PowerShell)
cd $HOME\.gemini
git clone https://github.com/<your-username>/<repo-name>.git skills

# macOS / Linux
cd ~/.gemini
git clone https://github.com/<your-username>/<repo-name>.git skills
```

If you already have a `~/.gemini/skills` directory, you can initialize this repo directly inside it or clone into a subfolder.

### 2. Prerequisites
* **Python 3.10+** (required for `convert-*` and `wf-session-archive` helper scripts):
  ```bash
  pip install pymupdf python-pptx pillow
  ```

---

## 🛠️ Usage

Skills are activated dynamically by Gemini CLI based on your conversational intent and matching triggers. You can also explicitly request an agent to invoke a specific skill by name:

```text
> Activate doc-merc-v4 and format this API guide.
> Use wf-pr-creator to prepare a Pull Request description for my active branch.
> Grill me on this microservices migration plan.
```

---

## 🛡️ License

Distributed under the [MIT License](LICENSE).
