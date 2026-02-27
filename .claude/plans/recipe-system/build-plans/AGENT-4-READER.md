# Agent 4: Reader Recipe — Build Plan

**Agent type:** general-purpose (worktree isolation)
**Design docs:** `reader-recipe/00-OVERVIEW.md` through `03-READER-TEMPLATES.md`
**Language rules:** `LANGUAGE-GUIDE.md` (Reader Recipe section)

---

## What This Agent Builds

| # | File | Lines (est.) | Purpose |
|---|------|-------------|---------|
| 1 | `commands/reader.md` | 300-400 | Reader skill — build custom reading experience |
| 2 | `templates/minimal-reader/index.html` | 150 | Base HTML shell |
| 3 | `templates/minimal-reader/style.css` | 200 | Clean, minimal CSS |
| 4 | `templates/minimal-reader/reader.js` | 250 | Navigation, search, theme toggle |
| 5 | `templates/minimal-reader/README.md` | 30 | Template documentation |
| 5a | `templates/minimal-reader/template.yaml` | 30 | Template metadata and configurable options |
| 5b | `templates/minimal-reader/preview.png` | — | Screenshot for template gallery (placeholder) |
| 6 | `templates/academic-reader/index.html` | 180 | Academic HTML shell |
| 7 | `templates/academic-reader/style.css` | 250 | Serif typography, footnotes, citations |
| 8 | `templates/academic-reader/reader.js` | 250 | Same navigation + academic features |
| 9 | `templates/academic-reader/README.md` | 30 | Template documentation |
| 9a | `templates/academic-reader/template.yaml` | 30 | Template metadata and configurable options |
| 9b | `templates/academic-reader/preview.png` | — | Screenshot for template gallery (placeholder) |

**Two templates to start.** Each template has 5 files: index.html, style.css, reader.js, template.yaml, README.md (preview.png is generated after building). Others (portfolio, interactive fiction, book club, chapbook) come later.

---

## Build Order

### Step 1: Understand Codex rendering

Before writing, study the existing codex rendering system:
- `chapterwise-web/app/templates/codex/codex_shell.html` — How codex projects are rendered on the web
- `chapterwise-web/app/templates/codex/_theme_injection.html` — How `--codex-*` CSS variables work
- `chapterwise-web/app/static/css/codex-theme.css` — Default theme variables
- `chapterwise-web/app/static/css/codex-components.css` — Component styles
- `chapterwise-web/app/static/css/codex-markdown.css` — Content styles

The reader templates should use the same `--codex-*` CSS custom property system so themes are portable.

### Step 2: Build minimal-reader template

The minimal reader is the foundation all other templates build on.

#### `templates/minimal-reader/index.html`

```html
<!DOCTYPE html>
<html lang="en" data-theme="light">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover">
  <title>{{PROJECT_TITLE}}</title>
  <link rel="stylesheet" href="style.css">
</head>
<body>
  <nav id="sidebar">
    <div class="sidebar-header">
      <h1>{{PROJECT_TITLE}}</h1>
      <button id="theme-toggle" aria-label="Toggle theme">☀</button>
    </div>
    <div id="search-box">
      <input type="search" placeholder="Search..." id="search-input">
    </div>
    <ul id="toc">
      <!-- Generated from index.codex.yaml -->
    </ul>
  </nav>

  <main id="content">
    <article id="reader-content">
      <!-- Content injected by reader.js -->
    </article>
    <nav id="page-nav">
      <a id="prev-link" href="#">← Previous</a>
      <a id="next-link" href="#">Next →</a>
    </nav>
  </main>

  <script src="reader.js"></script>
</body>
</html>
```

**Placeholders:** `{{PROJECT_TITLE}}`, `{{TOC_DATA}}`, `{{CONTENT_DATA}}` — the agent replaces these during build.

#### `templates/minimal-reader/style.css`

Uses `--codex-*` custom properties for theming:

```css
:root {
  --codex-bg-primary: #ffffff;
  --codex-bg-secondary: #f8f9fa;
  --codex-text-primary: #1a1a1a;
  --codex-text-secondary: #6b7280;
  --codex-accent: #2563eb;
  --codex-border: #e5e7eb;
  --codex-font-body: system-ui, -apple-system, sans-serif;
  --codex-font-heading: inherit;
  --codex-max-width: 720px;
}

[data-theme="dark"] {
  --codex-bg-primary: #1a1a2e;
  --codex-bg-secondary: #16213e;
  --codex-text-primary: #e0e0e0;
  --codex-text-secondary: #9ca3af;
  --codex-accent: #4a9eff;
  --codex-border: #374151;
}

/* Layout, typography, sidebar, content area, responsive... */
```

#### `templates/minimal-reader/reader.js`

```javascript
// Minimal Codex Reader
// - Parse TOC from embedded data
// - Navigate between chapters
// - Search across content
// - Toggle light/dark theme
// - Responsive sidebar

(function() {
  // TOC navigation
  // Chapter loading (from embedded or file-based content)
  // Search (client-side full text)
  // Theme toggle (light/dark)
  // Keyboard navigation (← → for prev/next)
  // Mobile sidebar toggle
})();
```

### Step 3: Build academic-reader template

Extends minimal with:
- Serif typography (Playfair Display headings, Source Serif Pro body)
- Footnote support (hover to preview, click to scroll)
- Pull quotes / epigraph styling
- Chapter number + title header treatment
- Table of contents with page numbers
- Print-friendly CSS (`@media print`)

### Step 4: Write `commands/reader.md`

```markdown
---
description: "Build a custom reading experience for your manuscript or atlas"
allowed-tools: Read, Grep, Glob, Bash, Write, Edit, AskUserQuestion, Task
triggers:
  - reader
  - build reader
  - codex reader
  - chapterwise:reader
argument-hint: "[project-path] [--template name]"
---

**Migration note:** Deprecated stubs keep only namespaced triggers (for example `chapterwise-analysis:analysis`) to avoid collisions with unified plain triggers like `analysis`.

# ChapterWise Reader

Build a custom, self-contained reading experience from a Codex project.
Output is static HTML/CSS/JS — open in any browser, host anywhere.

## Command Routing

### `/reader` (no args) — Interactive Builder
1. Find project root (look for index.codex.yaml)
2. Detect content type:
   - If `type: atlas` in index → activate atlas components
   - If `atlases` array exists → offer to include atlas in reader
   - Otherwise → standard manuscript reader
3. Choose template or build custom
4. Build reader
5. Save recipe

### `/reader --template minimal` — Direct Template
[Skip template selection, use specified template]

---

## BUILD READER

### Step 1: Scan Project
[Read index.codex.yaml]
[Count chapters, detect structure]
[Check for atlas (atlases array in index)]
[Progress: "Scanning project... {N} files, {M} parts."]

### Step 2: Choose Template
[Present available templates]
"Which reader style?"
  [Minimal] [Academic] [Custom]

If Custom:
  "Describe the look you want — fonts, colors, layout, mood."
  [Agent designs custom CSS from description]

### Step 3: Parse Content
[Read all chapter files]
[Extract: title, content (as HTML), word count, tags]
[Build TOC data structure from index.codex.yaml hierarchy]

For atlas projects:
  [Read atlas sections: characters, timeline, themes, etc.]
  [Build atlas navigation: section → subsection → entries]
  [Generate atlas-specific components:]
  [- Character cards with traits and arc summaries]
  [- Timeline events in chronological order]
  [- Theme list with chapter references]

### Step 4: Build Reader
[Copy template files to output directory]
[Replace {{PLACEHOLDERS}} with real data:]
  - {{PROJECT_TITLE}} → project name
  - {{TOC_DATA}} → JSON table of contents
  - {{CONTENT_DATA}} → all chapter content as embedded JSON or separate files
  - {{THEME_VARIABLES}} → custom --codex-* overrides from style.yaml

[For large projects (50+ chapters): split content into per-chapter files]
[For small projects: embed all content in a single HTML file]

[Progress: "Building reader shell... HTML, CSS, navigation."]

### Step 5: Wire Interactivity
[If atlas: generate atlas-specific components]
[Add search index (client-side)]
[Add keyboard navigation]
[Add theme toggle]
[Progress: "Wiring interactivity... search, theme toggle."]

### Step 6: Validate Reader Output
[Validate: index.html exists and contains expected structure (doctype, head, body)]
[Validate: all CSS/JS files referenced in HTML actually exist on disk]
[Validate: TOC data matches project structure (same chapter count, same titles)]
[Validate: if atlas reader — character cards, timeline, theme sections all present]
[Validate: no broken internal links (href="#chapter-X" has matching id)]
[Auto-fix: missing alt text on images → add from chapter title]
[Auto-fix: broken relative paths → correct based on output directory structure]
[If issues fixed: "Fixed 2 broken links in the reader."]
[If unfixable: "The reader references 3 chapters that don't exist — check your project."]
[If clean: say nothing]

### Step 7: Output
[Write to ./reader/ or specified output directory]
[Progress: "Done. Open index.html to preview."]
[Show file tree]

### Step 8: Save Recipe
[Save to .chapterwise/reader-recipe/recipe.yaml]
[Save template choice, custom CSS, project metadata]

---

## ATLAS-SPECIFIC RENDERING

When the reader detects `type: atlas` or `atlases` array:

### Character Cards
[Grid layout: name, role, trait tags, arc summary, chapter count badge]
[Click → expand to full profile]
[Link to chapters where character appears]

### Timeline View
[Vertical list of events in chronological order]
[Each event: title, chapter reference, characters involved]
[Act dividers between structural sections]

### Theme Section
[List of themes with prominence indicators]
[Each theme: description, chapters where it appears, evolution summary]

### Cross-Reference Links
[Character names in timeline → link to character profile]
[Chapter references → link to chapter in reader]

---

## CUSTOM READER

When user says "Custom":
1. Ask for design description
2. Agent reads the minimal template as reference
3. Agent generates custom CSS and any additional JS
4. Uses --codex-* variables for consistency
5. Saves custom template files in reader recipe folder

---

## ERROR HANDLING
[No index.codex.yaml: "I can't find a codex project here. Import your manuscript first with /import."]
[Empty project: "This project has no content files. Add chapters first."]
[Missing chapter files: "Warning: {N} chapter files referenced in the index are missing. Building reader from available files."]
[Browser compatibility: minimal-reader targets modern browsers only (ES2020+)]

## LANGUAGE RULES
[Phases: Scan, Build/Scaffold, Wire, Done]
[Progress: plain + functional. "Building reader shell...", "Wiring interactivity...", "Done."]
[The reader recipe has the LEAST cooking language — it's mostly functional.]
```

---

## Testing Checklist

- [ ] `/reader` on a simple codex project → minimal reader builds
- [ ] `index.html` opens in browser and renders correctly
- [ ] Navigation works (sidebar TOC, prev/next, keyboard arrows)
- [ ] Theme toggle works (light ↔ dark)
- [ ] Search works (find text across chapters)
- [ ] `/reader --template academic` → academic reader builds
- [ ] `/reader` on an atlas project → atlas-specific components render
- [ ] Character cards display in atlas reader
- [ ] Timeline view renders in atlas reader
- [ ] Recipe saved at `.chapterwise/reader-recipe/recipe.yaml`
- [ ] Custom reader: agent generates custom CSS from description
- [ ] Large project (50+ files): content split into per-chapter files
- [ ] Validation: reader output passes all checks (valid HTML, all assets exist, TOC matches)
- [ ] Self-healing: introduce a broken CSS link, run build → auto-corrected
- [ ] Cross-reference: reader TOC matches project index.codex.yaml chapter list exactly
- [ ] Recipe validation: `recipe_validator.py` passes on `.chapterwise/reader-recipe/`

---

## Dependencies on Phase 0

- `scripts/recipe_manager.py` — recipe creation/loading
- `scripts/recipe_validator.py` — recipe manifest validation after reader build
- Plugin directory structure with `templates/` directory

## Dependencies on Other Agents

- **Import Agent** creates the codex project the reader renders
- **Atlas Agent** creates atlas projects with `type: atlas` — reader detects this
- Reader can work independently on any existing codex project

---

## What This Agent Does NOT Build

- Import, analysis, or atlas commands
- Additional templates (portfolio, interactive fiction, book club, chapbook — future)
- Server-side rendering
- Web app integration
