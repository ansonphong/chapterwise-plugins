# Codex Reader Recipe — Full Specification

## Concept

Separate from the import and analysis recipes. The reader recipe helps writers and developers scaffold their own standalone reader for codex content. It's about owning your presentation layer.

ChapterWise.app has a beautiful codex shell (`codex_shell.html`) with tree navigation, table of contents, theme picker, search, and typography controls. The reader recipe lets the agent help someone build their own version, as simple or as complex as they want.

## Philosophy

This is the "own your code" promise made real:
- Your data is in open formats (Markdown, YAML)
- The reader is a reference you can study, fork, rebuild
- The agent is your co-developer, not your dependency
- Build your own reading experience, or use ChapterWise's

## What the Agent Can Build

### Level 1: Static HTML Reader
A single HTML file that renders a codex project. No server, no build step. Open in a browser.

```
my-novel-reader/
├── index.html        # Single-page app that reads codex files
├── style.css         # Custom theme
└── my-novel/         # The codex project (or symlink to it)
    ├── index.codex.yaml
    └── chapters/...
```

The agent generates `index.html` with:
- JavaScript that reads `index.codex.yaml` and builds a navigation tree
- Markdown rendering (using a CDN-loaded library like marked.js)
- Chapter loading and display
- Basic theme (light/dark toggle)
- Responsive layout

### Level 2: Enhanced Reader
Adds features from the ChapterWise codex shell:

- **Tree navigation** — Collapsible sidebar from the index
- **Table of contents** — Generated from headings within each chapter
- **Search** — Full-text search across chapters
- **Typography controls** — Font family, size, line height
- **Theme system** — Multiple themes with CSS custom properties
- **Reading progress** — Track where you are in the manuscript

### Level 3: Custom Publishing
The agent helps scaffold a full static site:

- **Multiple pages** — One HTML page per chapter, generated from codex
- **Custom design** — Writer describes their aesthetic, agent builds it
- **Navigation** — Previous/next chapter links, breadcrumbs
- **Static site generator** — Python script that rebuilds HTML from codex on demand
- **Deploy-ready** — Works on GitHub Pages, Netlify, Vercel

## Reference Implementation

The agent studies the ChapterWise codex shell as reference:

| Component | Reference File | What to Learn |
|-----------|---------------|---------------|
| Tree navigation | `codex_shell.html`, `index_tree_renderer.js` | How to build a project tree from index.codex.yaml |
| Content rendering | `_codex_fragment.html` | How codex YAML/markdown is rendered to HTML |
| Theme system | `codex_theme_engine.js`, `_theme_injection.html` | CSS custom properties for theming |
| TOC panel | `table_of_contents_panel.html`, `table-of-contents-panel.js` | Heading extraction and scrollspy |
| Typography | `display_settings_panel.html`, `typography-loader.js` | Font loading and size controls |
| Search | `search_panel.js` | Full-text search implementation |
| URL generation | `index_tree_renderer.js` | How URLs are built from codex structure |

The agent doesn't copy these files directly. It reads them to understand the patterns, then builds something appropriate for the writer's needs. A static reader doesn't need Alpine.js or Flask template syntax. It needs vanilla JS (or the writer's preferred framework).

## How It Works

### Writer Says:
> "Build me a simple reader for my novel"

### Agent:
1. Reads the project's `index.codex.yaml` to understand the structure
2. Asks 1-2 questions:
   - "Simple single-page reader, or a full multi-page site?"
   - "Any design preferences? Dark mode, specific fonts, minimal/rich?"
3. Generates the reader files
4. Opens in browser for preview
5. Writer iterates: "Make the font bigger," "Add a dark mode," "Change the sidebar color"

### Output:
A self-contained reader that reads the codex project and renders it. No ChapterWise account needed. No server needed. Just HTML, CSS, and JS.

## Reader Recipe Structure

Saved in `.chapterwise/reader-recipe/` for iteration:

```yaml
# reader-recipe.yaml
version: "1.0"
created: "2026-02-27T16:00:00Z"

project: "The Long Way Home"
reader_type: "single_page"  # single_page, multi_page, static_site

design:
  theme: dark
  font_display: "Crimson Pro"
  font_body: "Source Serif 4"
  accent_color: "#C49B66"
  layout: sidebar_left

features:
  - tree_navigation
  - dark_mode_toggle
  - chapter_toc
  - reading_progress
  - responsive

output:
  directory: "./reader/"
  entry_point: "index.html"
```

## Self-Validation and Self-Healing

Reader builds must validate output before reporting success:

1. Verify `index.html` exists and has valid top-level structure
2. Verify all referenced CSS/JS assets exist on disk
3. Verify TOC structure matches `index.codex.yaml`
4. Run `recipe_validator.py` on `.chapterwise/reader-recipe/`

Auto-fix behavior:
- Fix broken relative asset paths
- Rebuild missing TOC entries from index data
- Regenerate missing reader metadata in `recipe.yaml`

If unresolved issues remain after auto-fix attempts, the agent reports exact files and stops.

## Why This Matters

1. **Differentiation** — No other writing tool helps you build your own reader. Scrivener exports to PDF/EPUB. ChapterWise exports to "build whatever you want."

2. **Agentic publishing** — The agent isn't just converting formats. It's building you a custom publishing tool. This is what "agentic" really means: the AI as a developer working for you.

3. **Ecosystem growth** — Open format + reader recipe = people building novel readers, story portfolios, interactive fiction readers, book club sites. All powered by codex data.

4. **Staying ahead** — When every writing app can import and export, the differentiator is "can your AI help you build custom tools?" ChapterWise can.

## Relationship to Other Recipes

```
Import Recipe  →  Your manuscript is now codex data
Analysis Recipe  →  Your manuscript is now deeply understood
Reader Recipe  →  Your manuscript is now a custom reading experience
```

Three recipes. Three transformations. All powered by the same agent.

## Future: Reader Templates

As the community builds readers, the best ones become templates:

- `minimal-reader` — Clean, single-page, Kindle-like
- `academic-reader` — Footnotes, annotations, citation support
- `portfolio-site` — Multi-project showcase for authors
- `interactive-fiction` — Branching narrative reader
- `book-club` — Shared reading with annotations and discussions

The agent can start from a template and customize, or build from scratch. Templates are just reader recipes that worked well for someone else.
