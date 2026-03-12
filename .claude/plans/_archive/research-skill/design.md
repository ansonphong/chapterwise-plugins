# `/research` Command — Design Document

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Create a `/research` command that generates structured research reference files on any topic, stored as codex files in `.chapterwise/research/`. Supports standalone knowledge generation and manuscript-informed research when explicitly requested.

**Architecture:** Prompt-augmented generation — no custom scripts. The command file contains agent instructions for topic scoping, preference management, web search decisions, output structuring, and credits tracking. Output format (Codex Markdown or Codex JSON) is user-configurable via `.claude/chapterwise.local.md`.

**Tech Stack:** Claude Code command (markdown with YAML frontmatter), Codex V1.2 format

---

## Foundational Principle: LLM Judgment, User Override

This is a **core ChapterWise principle** that applies to ALL commands, not just `/research`.

> The agent makes intelligent, organic decisions about structure, depth, organization, and format — but always yields to explicit user preferences.

**Preference cascade** (later wins):

1. **Plugin defaults** — Sane out-of-the-box behavior
2. **`.claude/chapterwise.local.md`** — Persistent per-project preferences
3. **Command variant** — `/research` vs `/research:deep`
4. **Prompt language** — Always wins. Natural language overrides everything.

This principle governs every decision the agent makes: file organization, depth of output, format choice, folder naming, web search usage, manuscript awareness. The agent exercises good judgment, but the user's word is final.

This principle should be codified in `references/principles.md` for all commands to reference.

---

## Command Structure

```
plugins/chapterwise/
├── commands/
│   └── research.md              # Main /research command (handles both standard and deep)
└── references/
    └── principles.md            # Core principles including "LLM Judgment, User Override"
```

No scripts required. Research is a prompt-augmented generation task — the command definition itself contains all agent instructions.

---

## Invocation

```
/research <topic or instruction>
/research:deep <topic or instruction>
```

**Examples spanning the full spectrum:**

```bash
# Simple standalone research
/research cyanide poisoning

# Agent judges this needs breadth
/research Sumerian Gods

# Explicit deep dive — compendium mode
/research:deep all trickster gods across world mythologies

# User controls structure via natural language
/research medieval siege tactics, one section per weapon type
/research:deep Sumerian gods, one file per deity, include family trees

# Manuscript-informed (user explicitly pulls the thread)
/research relate Enlil to my character Archon in chapter 5
/research how does my character diverge from ancient trickster gods
/research patterns of trickster gods who were captured and chained to the earth
```

---

## Output Location & File Organization

**Default root:** `.chapterwise/research/`

**Organization is agent-judged, user-overridable.**

The agent decides folder structure based on topic scope, depth, and user instructions:

| Scenario | Output |
|----------|--------|
| Narrow topic, standard depth | `.chapterwise/research/cyanide-poisoning.codex.md` — single file |
| Broad topic, standard depth | `.chapterwise/research/sumerian-gods/overview.codex.md` — folder with overview, sub-sections as children within the file |
| Any topic, deep mode | `.chapterwise/research/trickster-gods/overview.codex.md` + `loki.codex.md` + `anansi.codex.md` + `coyote.codex.md` — full compendium |
| User says "one file per god" | Individual files per entity, regardless of depth setting |
| User says "put it in my worldbuilding folder" | Writes to `worldbuilding/` instead of default path |

**Folder naming:** Slugified from topic. Agent uses judgment to pick clean, descriptive names.

**Re-running:** If a research file already exists for the same topic, the agent updates in place rather than creating duplicates. New model credits are appended.

---

## Data Model

### Codex V1.2 JSON (`.research.json`)

```json
{
  "metadata": {
    "formatVersion": "1.2",
    "created": "2026-03-09T10:30:00Z",
    "updated": "2026-03-09T10:30:00Z"
  },
  "id": "sumerian-gods",
  "type": "research",
  "name": "Sumerian Gods",
  "summary": "Comprehensive overview of the Sumerian pantheon and their roles in Mesopotamian cosmology.",
  "body": "# Sumerian Gods\n\nThe Sumerian pantheon represents one of the oldest...",
  "tags": ["mythology", "sumerian", "ancient-near-east", "mesopotamia"],
  "attributes": [
    { "key": "topic", "value": "Sumerian Gods", "dataType": "string" },
    { "key": "depth", "value": "standard", "dataType": "string" },
    { "key": "sources", "value": "web-augmented", "dataType": "string" },
    { "key": "context", "value": "standalone", "dataType": "string" }
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
        "url": "https://example.com/sumerian-pantheon",
        "title": "The Sumerian Pantheon — Ancient History Encyclopedia",
        "accessedAt": "2026-03-09T10:30:00Z"
      },
      {
        "url": "https://jstor.org/stable/12345",
        "title": "Enlil and the Me: Divine Authority in Sumer",
        "accessedAt": "2026-03-09T10:31:00Z"
      }
    ]
  },
  "children": [
    {
      "id": "major-deities",
      "type": "research-section",
      "name": "Major Deities",
      "body": "The Sumerian pantheon was headed by...",
      "children": [
        {
          "id": "anu",
          "type": "research-entry",
          "name": "Anu — Sky Father",
          "summary": "Supreme god of the heavens...",
          "body": "Anu (also known as An) was the god of the sky..."
        },
        {
          "id": "enlil",
          "type": "research-entry",
          "name": "Enlil — Lord Wind",
          "summary": "God of wind, air, earth, and storms...",
          "body": "Enlil was considered the most powerful god..."
        }
      ]
    }
  ]
}
```

### Codex Lite Markdown (`.codex.md`)

```markdown
---
type: research
topic: Sumerian Gods
depth: standard
sources: web-augmented
context: standalone
tags: [mythology, sumerian, ancient-near-east, mesopotamia]
models:
  - Claude Opus 4.6 (Anthropic) — primary-researcher
web_sources:
  - "[The Sumerian Pantheon](https://example.com/sumerian-pantheon)" (2026-03-09)
  - "[Enlil and the Me](https://jstor.org/stable/12345)" (2026-03-09)
---

# Sumerian Gods

The Sumerian pantheon represents one of the oldest...

## Major Deities

### Anu — Sky Father

Anu (also known as An) was the god of the sky...

### Enlil — Lord Wind

Enlil was considered the most powerful god...
```

### Credits System

- **`credits.models`** — Array. Any LLM that contributes adds itself with `name`, `provider`, and `role`. If research is augmented later by a different model, that model appends to the array.
- **`credits.webSources`** — Array. Every `WebFetch` call produces a citation with URL, page title, and access timestamp. Agent must cite all web sources used.
- Both fields are **append-friendly** for incremental research sessions.

### Key Attributes

| Attribute | Values | Purpose |
|-----------|--------|---------|
| `topic` | Free text | The research subject |
| `depth` | `standard` \| `deep` | How extensive the research is |
| `sources` | `llm-knowledge` \| `web-augmented` | Whether web sources were used |
| `context` | `standalone` \| `manuscript-informed` | Whether the manuscript was referenced |

---

## Preference System

### File: `.claude/chapterwise.local.md`

This is the **per-project preferences file for all ChapterWise commands**. Uses the Claude Code plugin-settings pattern (YAML frontmatter + markdown body). Claude reads it automatically in context.

```yaml
---
# ChapterWise Preferences

research:
  format: codex-md              # codex-md | codex-json
  default_depth: standard       # standard | deep
  output_path: null             # null = .chapterwise/research/ (default)

# Future command preferences live here too
# analysis:
#   auto_run_modules: [summary, characters]
# reader:
#   default_template: minimal
---

## Project Notes

Any freeform notes the user or agent wants to persist about this project.
```

### First-Run Behavior

When `/research` is invoked and no `research.format` preference exists in `.claude/chapterwise.local.md`:

1. Agent asks:
   > "What format do you prefer for research output?
   > - **Codex Markdown** (`.codex.md`) — Human-readable, YAML frontmatter + prose
   > - **Codex JSON** (`.research.json`) — Machine-readable, V1.2 structured format
   >
   > I'll remember your choice for this project."

2. Agent writes the answer to `.claude/chapterwise.local.md`
3. Agent proceeds with research

### Override Without Changing Preference

If the user says "output this one as JSON" in the prompt, the agent obeys for that invocation without modifying the saved preference. Prompt language overrides, but doesn't mutate persistent config unless explicitly asked.

---

## Agent Decision Flow

```
1. PARSE PROMPT
   ├── Extract: topic, depth hints, structural instructions
   ├── Detect: /research vs /research:deep
   └── Detect: manuscript references (explicit only)

2. LOAD PREFERENCES
   ├── Read .claude/chapterwise.local.md
   ├── If no research preferences exist → ask format preference, save it
   └── Apply preference cascade (defaults → saved prefs → command variant → prompt)

3. DETERMINE SCOPE
   ├── Depth: standard or deep (from variant, prompt language, or default)
   ├── Structure: single file or multi-file (agent judges from topic breadth + user instructions)
   └── Format: codex-md or codex-json (from preference or prompt override)

4. DETERMINE SOURCES
   ├── Well-known topic → LLM knowledge first
   ├── Niche, recent, or needs verification → WebSearch + WebFetch
   └── User can force: "use web sources" or "no web search"

5. DETERMINE CONTEXT
   ├── Default: standalone (clean research, no manuscript scanning)
   └── Manuscript-informed: ONLY if user explicitly references their project/chapters

6. RESEARCH
   ├── Generate content with appropriate depth
   ├── If web-augmented: search, fetch, cite all sources
   └── Structure into codex format (children, sections, entries)

7. WRITE OUTPUT
   ├── Create folder structure if multi-file
   ├── Write codex files with full credits (models + web sources)
   └── Use slugified topic names for files/folders

8. BRIEF USER
   └── Report: what was created, where it lives, key findings summary
```

---

## Manuscript-Awareness Rules

**Default: Clean standalone research.** The agent does NOT scan the manuscript unless the user explicitly asks.

| User says | Agent behavior |
|-----------|---------------|
| "research Sumerian Gods" | Pure research. No manuscript awareness. |
| "research Sumerian Gods relevant to my novel" | Scans project codex files for context, tailors research. |
| "relate Enlil to my character Archon" | Reads relevant chapters, blends research with manuscript analysis. |
| "how does my character diverge from ancient trickster gods" | Deep manuscript scan + research synthesis. |

When manuscript-informed, the `context` attribute is set to `"manuscript-informed"` and relevant source files can be tracked in attributes.

---

## Web Search Rules

**Default: Agent decides.** Consistent with the core principle.

| Scenario | Agent behavior |
|----------|---------------|
| Well-known topic (major historical events, famous figures) | LLM knowledge first. Web if gaps detected. |
| Niche topic (obscure mythology, specific technical details) | Web search by default. |
| Recent events or current data | Web search required. |
| User says "use web sources" | Always search. |
| User says "no web" or "from memory" | LLM knowledge only. |

All web sources must be cited in `credits.webSources` with URL, title, and access date.

---

## Command Definition Outline

**File:** `plugins/chapterwise/commands/research.md`

```yaml
---
description: "Research any topic and generate structured codex reference files"
allowed-tools: ["Read", "Write", "Edit", "Glob", "Grep", "WebSearch", "WebFetch", "Agent", "Bash", "AskUserQuestion"]
triggers: ["/research"]
argument-hint: "<topic or instruction>"
---
```

The command body will contain:

1. **Principle statement** — Reference to "LLM Judgment, User Override"
2. **Preference loading** — Instructions to read `.claude/chapterwise.local.md`
3. **First-run flow** — Format preference prompting and persistence
4. **Research execution** — Topic scoping, web search decisions, depth judgment
5. **Output templates** — Both JSON and Markdown codex templates with credits
6. **File organization rules** — Single vs multi-file decision criteria
7. **Manuscript awareness rules** — Clean by default, context only when asked
8. **Credits requirements** — Model self-registration, web source citation
9. **Briefing format** — How to report results to the user

**File:** `plugins/chapterwise/commands/research-deep.md`

```yaml
---
description: "Deep research — generate a multi-document compendium on any topic"
allowed-tools: ["Read", "Write", "Edit", "Glob", "Grep", "WebSearch", "WebFetch", "Agent", "Bash", "AskUserQuestion"]
triggers: ["/research:deep"]
argument-hint: "<topic or instruction>"
---
```

Thin wrapper that sets `depth: deep` and references the main research command's logic. Alternatively, this can be handled within `research.md` itself via argument detection — implementation decision to be made during build.

---

## Implementation Tasks

### Task 1: Core Principle Reference File
- Create `plugins/chapterwise/references/principles.md`
- Document "LLM Judgment, User Override" as a foundational ChapterWise principle
- Include the preference cascade definition
- This file will be referenced by `/research` and future commands

### Task 2: Research Command Definition
- Create `plugins/chapterwise/commands/research.md`
- Full command definition with YAML frontmatter and agent instructions
- Include both output format templates (JSON + Markdown)
- Include credits system specification
- Include all decision flows (scope, sources, context, structure)
- Reference `principles.md`

### Task 3: Research Deep Variant
- Create `plugins/chapterwise/commands/research-deep.md` OR handle within `research.md`
- Sets depth to deep by default
- Multi-document compendium behavior

### Task 4: Preference System Bootstrap
- Document the `.claude/chapterwise.local.md` pattern
- First-run preference prompting flow
- Ensure the command creates the file if it doesn't exist

### Task 5: Testing & Validation
- Test `/research cyanide poisoning` → single file, standalone
- Test `/research:deep Sumerian Gods` → multi-file compendium
- Test first-run preference flow
- Test prompt override ("output as JSON this time")
- Test manuscript-informed: `/research relate X to my character Y`
- Test web search citation tracking
- Validate codex output against V1.2 schema
