# 10 — Documentation: The Three Paths to Getting Started

## Concept

The Get Started page on chapterwise.app/docs needs to present three distinct paths for importing content into ChapterWise. Each path serves a different user type and comfort level.

## The Three Paths

### Path 1: ChapterWise.app (Cloud Import)
**For:** Writers who want the simplest experience. No setup, no CLI, no API key.

**How it works:**
1. Go to chapterwise.app
2. Create a project → Upload manuscript
3. The import pipeline handles everything: format detection, chapter splitting, metadata extraction
4. Your project is ready. Run analysis from the web UI.

**Supported formats:** PDF, DOCX, HTML, Markdown, TXT, RTF, XML, JSON, Final Draft (.fdx)

**Advantages:**
- Zero setup
- No dependencies to install
- Works from any device with a browser
- AI-powered chapter detection on the server
- Credits-based pricing (no API key needed)

### Path 2: Claude Code + Plugins (Agentic Import)
**For:** Writers and developers who want full control. Uses their own Claude API key. Everything runs locally.

**How it works:**
1. Install Claude Code
2. Install the ChapterWise plugins: `claude plugins add chapterwise`
3. Say: `/import my-novel.pdf` (or any supported format)
4. The agent analyzes the manuscript, asks 1-2 questions, and creates a complete ChapterWise project
5. Push to GitHub, connect to ChapterWise.app, or use the VS Code extension

**Supported formats:** Everything in Path 1, plus Scrivener, Ulysses, Obsidian vaults, Notion exports, markdown folders, and anything else the agent can figure out.

**Advantages:**
- Runs locally, your compute, your API key
- Supports more formats (Scrivener, Ulysses, project folders)
- Agentic: the agent reasons about your specific manuscript
- Recipe system: fast re-imports of updated drafts
- Can create custom converters on the fly for unknown formats
- Analysis recipe: intelligent analysis recommendations

### Path 3: CLI / Scripts (Direct)
**For:** Developers who want to integrate ChapterWise into their own tooling.

**How it works:**
1. Clone the chapterwise-plugins repo
2. Use the pattern scripts directly:
   ```bash
   python3 patterns/pdf_converter.py my-novel.pdf ./output/
   python3 patterns/scrivener_converter.py ~/Projects/MyNovel.scriv ./output/
   ```
3. Or use the shared utilities to build custom conversion pipelines

**Advantages:**
- Full control over every step
- No AI agent needed
- Scriptable, automatable
- Use as building blocks for custom workflows

## Get Started Page Structure

The docs page at `/docs/get-started` should present these paths visually with clear guidance on which to choose.

### Page Layout

```
# Getting Started with ChapterWise

[Brief intro: ChapterWise transforms your manuscripts into rich,
analyzable projects. Choose your path:]

┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│  ☁️  Cloud       │  │  🤖  Agentic     │  │  ⌨️  CLI        │
│  ChapterWise.app│  │  Claude Code     │  │  Scripts        │
│                 │  │                  │  │                 │
│  Upload through │  │  Your agent      │  │  Pattern scripts│
│  the web. Zero  │  │  imports locally │  │  you run        │
│  setup.         │  │  using your key. │  │  directly.      │
│                 │  │                  │  │                 │
│  [Get Started]  │  │  [Get Started]   │  │  [View Scripts] │
└─────────────────┘  └─────────────────┘  └─────────────────┘

## Supported Formats

[Table showing all formats and which path supports them]

## Path 1: Cloud Import
[Step-by-step for web upload]

## Path 2: Agentic Import with Claude Code
[Installation, plugin setup, first import walkthrough]
[Show the agent conversation: user says /import, agent responds]
[Recipe system explained briefly]

## Path 3: CLI Scripts
[How to use pattern scripts directly]
[Link to GitHub repo]

## What Happens After Import

Regardless of which path you chose:
1. Your project is a git-compatible folder of Markdown/YAML files
2. Push to GitHub and connect to ChapterWise.app
3. Open in VS Code with the ChapterWise extension
4. Run AI analysis on any chapter
5. Share your project through ChapterWise
```

### Format Support Table

| Format | Cloud | Agentic | CLI |
|--------|-------|---------|-----|
| PDF | ✓ | ✓ | ✓ |
| DOCX | ✓ | ✓ | ✓ |
| HTML | ✓ | ✓ | ✓ |
| Markdown | ✓ | ✓ | ✓ |
| Plain Text | ✓ | ✓ | ✓ |
| RTF | ✓ | ✓ | ✓ |
| XML | ✓ | ✓ | ✓ |
| JSON | ✓ | ✓ | ✓ |
| Final Draft | ✓ | ✓ | On-the-fly |
| Scrivener | — | ✓ | ✓ |
| Ulysses | — | ✓ | ✓ |
| Markdown Folders | — | ✓ | ✓ |
| Obsidian Vaults | — | ✓ | ✓ |
| Notion Export | — | ✓ | ✓ |
| EPUB | — | ✓ | Via pandoc |
| LaTeX | — | ✓ | Via pandoc |
| Fountain | — | ✓ | On-the-fly |
| Any other format | — | ✓ (agent creates converter) | — |

### Key Messaging

**For the cloud path:**
> "The fastest way to start. Upload your manuscript and ChapterWise handles everything. No technical setup required."

**For the agentic path:**
> "The most powerful way to import. Your AI agent analyzes your manuscript's structure and creates a conversion strategy tailored to your specific work. Supports every format including Scrivener and Ulysses projects. Uses your own API key."

**For the CLI path:**
> "For developers who want to integrate ChapterWise into their own workflows. The pattern scripts are open source and fully documented."

## Implementation Notes

### Current get-started.md Content
The current page (`app/content/docs/get-started.md`) is brief and only covers the cloud path (upload → detect chapters → analyze). It needs a full rewrite to present all three paths.

### Template vs Markdown
The get-started page could be:
- **Markdown** (current): Simple but limited in layout options
- **Custom template**: Like the docs index page, allows bento-box layout, cards, icons

Recommendation: Use the Jinja2 template approach (like `docs/index.html`) for the three-path layout, with cards and visual hierarchy. The docs route already supports custom templates for specific pages.

### Links to Plugins Repo
The agentic and CLI paths should link to:
- GitHub: `https://github.com/ansonphong/chapterwise-plugins`
- Plugin install instructions
- Pattern scripts documentation

### Links to Web App
The cloud path should link to:
- ChapterWise.app registration
- The import documentation (`/docs/import/`)
- The upload page directly
