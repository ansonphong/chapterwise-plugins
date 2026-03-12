# Codex Reader — Templates

## The Template Library

As people build Codex Readers, the best designs become templates. A template is just a reader recipe that worked well for someone and can be reused as a starting point.

## Built-In Templates (minimal + academic ship with v2.0.0; others are future additions)

### minimal-reader
The default. A clean, focused reading experience.

- **Aesthetic**: Kindle-like. Warm off-white background, serif body text, generous margins
- **Features**: Chapter navigation (sidebar or bottom), dark mode toggle, reading progress bar
- **Layout**: Single column, centered content, collapsible sidebar
- **Tech**: Single HTML file, ~150 lines, CDN-loaded dependencies
- **Best for**: Novels, short stories, personal reading

```
Design:
┌─────────────────────────────────────┐
│ ≡  The Long Way Home          ☽/☀  │
├─────────────────────────────────────┤
│                                     │
│         Chapter I                   │
│         The Awakening               │
│                                     │
│    The morning light filtered       │
│    through curtains Elena didn't    │
│    recognize. She lay still,        │
│    cataloging sensations...         │
│                                     │
│                                     │
│         ← Prev  |  Next →          │
│                                     │
│  ████████████░░░░░░░  42% read     │
└─────────────────────────────────────┘
```

### academic-reader
For scholarly work, research, and annotation-heavy reading.

- **Aesthetic**: Clean, institutional. Wide margins for notes. Footnote support.
- **Features**: Footnote/endnote rendering, annotation sidebar, citation export, word count per section, bookmarks
- **Layout**: Two-column on wide screens (content + annotation margin)
- **Tech**: Multi-file, ~500 lines
- **Best for**: Academic papers, research manuscripts, annotated editions, non-fiction

```
Design:
┌────────────────────────────────────────────┐
│  📖 Research Paper    [Bookmarks] [Export]  │
├──────────────────────┬─────────────────────┤
│                      │ ANNOTATIONS         │
│  2. Methodology      │                     │
│                      │ ✏️ "This section    │
│  The approach used   │  needs more detail  │
│  combines both       │  on sample size."   │
│  qualitative and     │                     │
│  quantitative¹       │ ¹ See Smith (2024)  │
│  methods...          │   for comparison    │
│                      │                     │
└──────────────────────┴─────────────────────┘
```

### portfolio-site
A multi-project showcase for authors.

- **Aesthetic**: Magazine/editorial. Grid layout for projects, bold typography, author branding
- **Features**: Project grid with cover images, about page, contact, multiple codex projects side by side
- **Layout**: Landing page → project pages → chapter reading
- **Tech**: Multi-page static site with build script, ~1000 lines
- **Best for**: Authors showcasing multiple works, publishing portfolios

```
Design:
┌─────────────────────────────────────────┐
│  JANE SMITH                    About │
├─────────────────────────────────────────┤
│                                         │
│  ┌───────────┐  ┌───────────┐          │
│  │           │  │           │          │
│  │  THE LONG │  │  ANOTHER  │          │
│  │  WAY HOME │  │  NOVEL    │          │
│  │           │  │           │          │
│  │  Novel    │  │  Novella  │          │
│  │  87k words│  │  32k words│          │
│  └───────────┘  └───────────┘          │
│                                         │
│  "Writing that stays with you."         │
└─────────────────────────────────────────┘
```

### interactive-fiction
For branching narratives, CYOA, and experimental storytelling.

- **Aesthetic**: Atmospheric. Full-screen sections, ambient backgrounds, mood-driven
- **Features**: Choice-based navigation (codex attributes define branches), state tracking, multiple endings
- **Layout**: Full-screen passages with navigation choices at bottom
- **Tech**: Single-page app, ~800 lines, uses codex attributes for branching logic
- **Best for**: Interactive fiction, game narratives, experimental writing

### book-club
Shared reading with social features.

- **Aesthetic**: Warm, inviting. Discussion-focused
- **Features**: Reading progress synced across readers, chapter discussion threads (via localStorage or simple backend), shared annotations, reading schedule
- **Layout**: Reader + discussion sidebar
- **Tech**: Multi-page, requires simple backend for shared state (or uses a serverless function)
- **Best for**: Book clubs, classroom reading, collaborative analysis

### chapbook
Minimalist poetry/short form reader.

- **Aesthetic**: Lots of white space. Typography-forward. Each piece gets its own page
- **Features**: Swipe/click between pieces, no sidebar, just content
- **Layout**: One piece per screen, full viewport
- **Tech**: Single HTML file, ~100 lines
- **Best for**: Poetry collections, flash fiction, short prose

## Template Selection

When the writer asks the agent to build a reader, the agent can suggest a template:

```
Agent: "What kind of reader would you like?"

  [Minimal (Recommended)]  — Clean, focused reading. Kindle-like.
  [Academic]               — Footnotes, annotations, research-focused.
  [Portfolio]              — Showcase multiple projects. Author branding.
  [Other]                  — Describe what you want.
```

Or the writer can describe what they want and the agent picks (or builds from scratch):

> Writer: "I want something dark and atmospheric for my horror novel"
> Agent: Starts from minimal-reader, applies dark theme, adds atmospheric background effects, custom typography

## Template Customization

Templates are starting points, not final products. The agent customizes:

- **Colors and theme**: Writer describes an aesthetic, agent generates CSS variables
- **Typography**: Writer names fonts (or describes "something elegant"), agent selects and loads
- **Layout**: Sidebar left/right, top nav, no nav, full-screen sections
- **Features**: Add/remove search, TOC, reading progress, dark mode, etc.
- **Content-specific**: If the codex has images, add a lightbox. If it has spreadsheets, add table rendering.

## Community Templates (Future)

The template library grows with the community:

1. Someone builds a great reader
2. They extract it into a template (reader recipe + generic HTML/CSS/JS)
3. They share it on GitHub or the ChapterWise community
4. Other writers use it as a starting point
5. The agent knows about community templates and can suggest them

This creates a flywheel: more readers built → more templates available → easier to build readers → more people using codex format.

## Template File Structure

Each template is a self-contained folder:

```
templates/minimal-reader/
├── template.yaml          # Template metadata and configurable options
├── index.html             # The reader HTML (with template variables)
├── style.css              # Base styles (with CSS custom properties)
├── reader.js              # Reader logic
└── preview.png            # Screenshot for template gallery
```

The agent reads `template.yaml` to understand what's configurable:

```yaml
name: "Minimal Reader"
description: "Clean, focused reading experience. Kindle-like."
author: "ChapterWise"
version: "1.0"

configurable:
  - key: theme
    type: choice
    options: [light, dark, sepia]
    default: light

  - key: font_body
    type: font
    default: "Source Serif 4"

  - key: font_size
    type: range
    min: 14
    max: 24
    default: 18

  - key: content_width
    type: range
    min: 500
    max: 900
    default: 680

  - key: show_progress
    type: boolean
    default: true

  - key: show_sidebar
    type: boolean
    default: true
```
