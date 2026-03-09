---
description: "Research any topic and generate structured codex reference files"
allowed-tools: Read, Grep, Glob, Bash, Write, Edit, AskUserQuestion, Task, WebSearch, WebFetch, Agent
triggers:
  - research
  - chapterwise:research
argument-hint: "<topic or instruction>"
---

# ChapterWise Research

## Overview

Research any topic and produce structured reference files in Codex format, stored in `.chapterwise/research/`. Research is clean and standalone by default — no manuscript scanning unless explicitly requested. The agent decides depth, structure, and web search usage based on topic scope, but the user's natural language always overrides.

Read and follow `${CLAUDE_PLUGIN_ROOT}/references/principles.md` — especially **LLM Judgment, User Override**.

Read and follow `${CLAUDE_PLUGIN_ROOT}/references/language-rules.md` for all progress messages.

---

## Command Flow

### Step 1: Parse the Prompt

Extract from the user's input:

| Signal | What to detect |
|--------|---------------|
| **Topic** | The subject to research |
| **Depth hints** | "deep dive", "comprehensive", "massive compendium", "quick overview", "brief" |
| **Structure hints** | "one file per god", "flat list", "single document", "organize by region" |
| **Format override** | "output as JSON", "use markdown", "codex format" |
| **Web hints** | "use web sources", "search the web", "no web", "from memory only" |
| **Manuscript references** | "relate to my character", "compare with chapter 5", "relevant to my novel" |
| **Output path override** | "put it in my worldbuilding folder", "save to research/mythology/" |

If the user references their manuscript or specific chapters, set context to `manuscript-informed`. Otherwise, default to `standalone`.

---

### Step 2: Load Preferences

Read `.claude/chapterwise.local.md` from the project root (not the plugin root).

Look for the `research` section in the YAML frontmatter:

```yaml
research:
  format: codex-md          # codex-md | codex-json
  default_depth: standard   # standard | deep
  output_path: null          # null = default
```

If the file doesn't exist or has no `research` section, proceed to Step 3 (first-run flow).

If preferences exist, apply them as defaults (prompt language still overrides).

---

### Step 3: First-Run Preference Flow

If no `research.format` preference exists, ask the user:

Use AskUserQuestion:

> "What format do you prefer for research output?"

Options:
- **Codex Markdown** (.codex.md) — Human-readable, YAML frontmatter + prose
- **Codex JSON** (.research.json) — Machine-readable, Codex V1.2 structured format

Save their choice to `.claude/chapterwise.local.md`. Create the file if it doesn't exist. If the file exists, add the `research` section to the frontmatter without disturbing existing content.

Then proceed with research.

---

### Step 4: Determine Scope

Apply the preference cascade (Principle 1) to resolve:

**Depth:**
- Default: `standard`
- Saved preference: `research.default_depth`
- Prompt override: detect "deep", "comprehensive", "massive" → `deep`; detect "brief", "quick", "overview" → `standard`

**Structure (LLM judgment):**

| Topic scope | Agent decision |
|-------------|---------------|
| Narrow, focused topic | Single file |
| Broad topic, standard depth | Folder with overview file, sub-sections as children within it |
| Broad topic, deep mode | Folder with overview + individual sub-files |
| User specifies structure | Obey exactly |

**Format:**
- Saved preference or first-run choice
- Prompt override for this invocation (don't mutate saved preference)

---

### Step 5: Determine Sources

The agent decides whether to use web search based on topic type:

| Scenario | Decision |
|----------|----------|
| Well-known topic (major history, famous figures, established science) | LLM knowledge first. Web if gaps detected. |
| Niche topic (obscure mythology, specific technical details, regional history) | Web search by default |
| Recent events, current data, statistics | Web search required |
| User says "use web sources" or "search for this" | Always search |
| User says "no web" or "from memory" | LLM knowledge only |

When using web search:
1. Use WebSearch to find relevant sources
2. Use WebFetch to read promising results
3. Cite every web source in the `credits.webSources` array
4. Include URL, page title, and access timestamp for each source

---

### Step 6: Determine Context

**Default: Standalone.** Do NOT scan the manuscript unless the user explicitly asks.

| User says | Context |
|-----------|---------|
| "research Sumerian Gods" | `standalone` — pure research, no manuscript |
| "research Sumerian Gods relevant to my novel" | `manuscript-informed` — scan project for context |
| "relate Enlil to my character Archon" | `manuscript-informed` — read specific chapters |
| "how does my character diverge from trickster gods" | `manuscript-informed` — deep manuscript scan + research |

When manuscript-informed:
1. Read `index.codex.yaml` to understand the project
2. Read relevant chapter files as needed
3. Blend research with manuscript context in the output
4. Set `context: manuscript-informed` in the output attributes

---

### Step 7: Research

Execute the research based on resolved scope, sources, and context.

**Progress message:** `"Researching {topic}..."`

If web-augmented: `"Researching {topic}... searching web sources."`

If manuscript-informed: `"Researching {topic}... cross-referencing with manuscript."`

Generate thorough, well-structured content. For deep mode, aim for comprehensive coverage. For standard mode, aim for a solid, useful reference document.

---

### Step 8: Write Output

**Output root:** `.chapterwise/research/` (or user-specified path)

**Folder and file naming:** Use LLM judgment to create clean, descriptive slugs from the topic.

Examples:
- Topic "Sumerian Gods" → `sumerian-gods/`
- Topic "How cyanide poisoning works" → `cyanide-poisoning.codex.md` (single file)
- Topic "All trickster gods across mythology" (deep) → `trickster-gods/overview.codex.md` + sub-files

**If updating existing research:** If a research file already exists for the same topic, update in place. Append new model credits rather than replacing.

#### Codex Markdown Format (.codex.md)

```markdown
---
type: research
topic: "{topic}"
depth: standard
sources: llm-knowledge
context: standalone
tags: [tag1, tag2, tag3]
credits:
  models:
    - Claude Opus 4.6 (Anthropic) — primary-researcher
  web_sources:
    - "[Page Title](https://example.com)" (2026-03-09)
---

# {Topic Title}

{Structured research content with sections and subsections...}
```

#### Codex V1.2 JSON Format (.research.json)

```json
{
  "metadata": {
    "formatVersion": "1.2",
    "created": "{ISO 8601}",
    "updated": "{ISO 8601}"
  },
  "id": "{topic-slug}",
  "type": "research",
  "name": "{Topic Title}",
  "summary": "{One-line summary of the research}",
  "body": "{Main markdown content}",
  "tags": ["tag1", "tag2"],
  "attributes": [
    {"key": "topic", "value": "{topic}", "dataType": "string"},
    {"key": "depth", "value": "standard", "dataType": "string"},
    {"key": "sources", "value": "llm-knowledge", "dataType": "string"},
    {"key": "context", "value": "standalone", "dataType": "string"}
  ],
  "credits": {
    "models": [
      {
        "name": "Claude Opus 4.6",
        "provider": "Anthropic",
        "role": "primary-researcher"
      }
    ],
    "webSources": [
      {
        "url": "https://example.com",
        "title": "Page Title",
        "accessedAt": "{ISO 8601}"
      }
    ]
  },
  "children": []
}
```

#### Credits Rules

- **`credits.models`** — Add yourself to this array. Include your model name, provider, and role. If this research is later augmented by a different model or provider, that model appends itself.
- **`credits.webSources`** — Every WebFetch call produces a citation. Include URL, page title, and access date. Never omit a source that was actually used.
- When updating existing research, append new credits — never replace the existing list.

#### Children Structure

For multi-section research, use the `children` array (JSON) or subsections (Markdown):

**JSON children types:**
- `research-section` — A major section grouping
- `research-entry` — An individual entity or topic entry

**Example (deep mode, one entry per deity):**

```json
"children": [
  {
    "id": "major-deities",
    "type": "research-section",
    "name": "Major Deities",
    "body": "Overview of the primary gods...",
    "children": [
      {
        "id": "anu",
        "type": "research-entry",
        "name": "Anu — Sky Father",
        "summary": "Supreme god of the heavens",
        "body": "Anu (also known as An) was..."
      }
    ]
  }
]
```

---

### Step 9: Brief the User

Report what was created:

**Single file:**
> "Done. Research saved to `.chapterwise/research/cyanide-poisoning.codex.md`."

**Multi-file:**
> "Done. {N} research files saved to `.chapterwise/research/sumerian-gods/`."

Then show the file tree:

```
.chapterwise/research/sumerian-gods/
├── overview.codex.md
├── anu.codex.md
├── enlil.codex.md
├── enki.codex.md
└── inanna.codex.md
```

If web sources were used, note the count:
> "{N} web sources cited."

---

## Key Attributes Reference

| Attribute | Values | Purpose |
|-----------|--------|---------|
| `topic` | Free text | The research subject |
| `depth` | `standard` \| `deep` | How extensive the research is |
| `sources` | `llm-knowledge` \| `web-augmented` | Whether web sources were used |
| `context` | `standalone` \| `manuscript-informed` | Whether the manuscript was referenced |

---

## Research-Specific Language Rules

Follow `${CLAUDE_PLUGIN_ROOT}/references/language-rules.md` for all shared rules.

| Phase | Verb | Example |
|-------|------|---------|
| Start research | Researching | "Researching Sumerian mythology..." |
| Web search | Searching | "Searching web sources... 5 relevant pages found." |
| Manuscript scan | Cross-referencing | "Cross-referencing with manuscript... 3 chapters mention Enlil." |
| Writing output | Writing | "Writing research files... 5 entries." |
| Completion | Done | "Done. 5 research files saved to .chapterwise/research/sumerian-gods/." |

---

## Error Handling

| Situation | Response |
|-----------|----------|
| No topic provided | "What would you like to research?" (use AskUserQuestion) |
| Web search returns no results | Fall back to LLM knowledge. Note `sources: llm-knowledge` in output. |
| Web fetch fails on a URL | Skip that source, continue with others. Do not cite failed fetches. |
| Output directory not writable | Report the error and suggest an alternative path. |
| Manuscript referenced but no codex files found | "No Codex project found here. Running standalone research instead." Set context to `standalone`. |
| Existing research file found for same topic | Update in place. Append new credits. Merge content intelligently. |
