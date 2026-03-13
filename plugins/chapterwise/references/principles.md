# ChapterWise Core Principles

These principles apply to ALL ChapterWise commands. Read and follow them alongside `language-rules.md`.

---

## Principle 1: LLM Judgment, User Override

The agent makes intelligent, organic decisions about structure, depth, organization, and format — but always yields to explicit user preferences.

### Preference Cascade

Priority (later overrides earlier):

1. **Plugin defaults** — Sane out-of-the-box behavior hardcoded in the command definition
2. **`.claude/chapterwise.local.md`** — Persistent per-project preferences (YAML frontmatter)
3. **Command variant** — e.g., `/research` vs `/research:deep`
4. **Prompt language** — Always wins. Natural language in the user's prompt overrides everything.

### What This Means in Practice

- **File organization:** The agent chooses folder names, file structure, and nesting depth based on content scope — but if the user says "put it in my worldbuilding folder" or "one file per character", obey.
- **Output format:** The agent uses the saved preference or default — but if the user says "output this one as JSON", obey for this invocation without changing the saved preference.
- **Depth and scope:** The agent judges how deep to go based on topic breadth — but if the user says "make it massive" or "keep it brief", obey.
- **Web search:** The agent decides whether to search the web based on topic type — but if the user says "use web sources" or "no web", obey.
- **Structure:** The agent decides single-file vs multi-file based on topic — but if the user specifies structure ("one section per god", "flat list"), obey.

### When Preferences Don't Exist Yet

If a command needs a preference that isn't set in `.claude/chapterwise.local.md`:

1. Apply a sensible default silently (Principle 2 — Clean Defaults)
2. Save the applied default to `.claude/chapterwise.local.md` after the command completes
3. The user can change it later by asking or editing the file directly

### Override vs Mutate

- **Prompt override:** User says "output this one as JSON" → obey for this invocation, do NOT change saved preference
- **Explicit preference change:** User says "always use JSON from now on" → update `.claude/chapterwise.local.md`

---

## Principle 2: Clean Defaults, Rich Options

Commands work with zero configuration. The first run should produce useful output without requiring the user to set preferences, choose options, or read documentation. But power users can customize deeply through preferences, flags, and natural language instructions.

---

## Principle 3: Data Over Flare

Every progress message, completion report, and status update includes real data — chapter counts, word counts, file counts, entity names. Never replace substance with decoration. See `language-rules.md` for the full messaging rules.

---

## Preference Storage: `.claude/chapterwise.local.md`

This is the per-project preferences file for all ChapterWise commands. It uses the Claude Code plugin-settings pattern: YAML frontmatter for structured config, markdown body for freeform notes. Claude reads it automatically in context.

**Location:** `.claude/chapterwise.local.md` (in the user's project, not the plugin)

**Format:**

```markdown
---
research:
  format: codex-md
  default_depth: standard
  output_path: null
---

## ChapterWise Project Notes

Freeform notes about this project that persist across sessions.
```

Note: The `---` delimiters contain YAML only — no markdown headings or `#` comments that could be confused with markdown. Section headers belong in the markdown body below the closing `---`.

**Rules:**
- Create the file on first use if it doesn't exist
- Only add sections for commands that have been used
- Never remove user-written notes from the markdown body
- Read this file at the start of every command execution
