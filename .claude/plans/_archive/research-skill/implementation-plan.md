# `/research` Command Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Create a `/research` command that generates structured research reference files on any topic, stored as codex files in `.chapterwise/research/`. Supports both standalone and manuscript-informed research, with configurable output format and depth.

**Architecture:** Prompt-augmented generation command (no scripts). The command markdown file contains all agent instructions for preference management, topic scoping, web search decisions, output structuring, and credits tracking. A companion `references/principles.md` file codifies the "LLM Judgment, User Override" principle for reuse across all commands.

**Tech Stack:** Claude Code command (markdown with YAML frontmatter), Codex V1.2 format (JSON and Markdown variants)

---

### Task 1: Create Core Principles Reference File

**Files:**
- Create: `plugins/chapterwise/references/principles.md`

**Step 1: Write the principles reference**

Create the shared principles file that all commands can reference. This establishes "LLM Judgment, User Override" as a foundational ChapterWise principle.

**Step 2: Verify file is discoverable**

Run: `ls plugins/chapterwise/references/`
Expected: `atlas-section-schemas.md`, `language-rules.md`, `principles.md`

**Step 3: Commit**

```bash
git add plugins/chapterwise/references/principles.md
git commit -m "feat: add core principles reference — LLM Judgment, User Override"
```

---

### Task 2: Create `/research` Command

**Files:**
- Create: `plugins/chapterwise/commands/research.md`

**Step 1: Write the research command definition**

Full command with YAML frontmatter (triggers, allowed-tools, description) and comprehensive agent instructions covering:
- Preference loading from `.claude/chapterwise.local.md`
- First-run preference prompting
- Topic scoping and depth judgment
- Web search decision-making
- Manuscript-awareness rules
- Output format templates (both JSON and Markdown)
- Credits system (models + web sources)
- File organization rules
- User briefing format

Follow the conventions from `analysis.md` and `atlas.md` for structure and language.

**Step 2: Verify command is registered**

The plugin uses auto-discovery from the `commands/` folder, so no manifest changes needed. Verify:

Run: `ls plugins/chapterwise/commands/research*.md`
Expected: `research.md`

**Step 3: Commit**

```bash
git add plugins/chapterwise/commands/research.md
git commit -m "feat: add /research command — topic research with codex output"
```

---

### Task 3: Create `/research:deep` Command Variant

**Files:**
- Create: `plugins/chapterwise/commands/research-deep.md`

**Step 1: Write the deep research variant**

Thin command that sets depth to `deep` and references the main research command's logic. Triggers on `/research:deep`. Produces multi-document compendiums with overview + sub-files.

**Step 2: Commit**

```bash
git add plugins/chapterwise/commands/research-deep.md
git commit -m "feat: add /research:deep command — multi-document compendium mode"
```

---

### Task 4: Validate Integration

**Step 1: Verify all command triggers are unique**

Grep all command files for trigger conflicts:

Run: `grep -h "triggers:" plugins/chapterwise/commands/*.md`

Verify no collisions with existing triggers.

**Step 2: Verify references are consistent**

Check that `research.md` references `principles.md` and `language-rules.md` correctly using `${CLAUDE_PLUGIN_ROOT}/references/` paths.

**Step 3: Final commit if any fixes needed**

```bash
git add -A
git commit -m "fix: resolve any integration issues with /research command"
```
