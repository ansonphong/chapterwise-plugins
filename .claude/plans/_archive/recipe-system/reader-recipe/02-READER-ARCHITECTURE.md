# Codex Reader — Architecture

## How a Codex Reader Works

Every Codex Reader, regardless of complexity level, does the same fundamental things:

1. **Parse** `index.codex.yaml` to understand the project structure
2. **Load** chapter content (Markdown or Codex YAML body fields)
3. **Render** content as styled HTML
4. **Navigate** between chapters via the project hierarchy

Everything else (themes, search, TOC, typography) is built on top of these four primitives.

## The Parsing Layer

### Reading index.codex.yaml

The index file is the entry point. A reader needs to:

```javascript
// Pseudocode for any Codex Reader
async function loadProject(indexPath) {
    const indexYaml = await fetch(indexPath).then(r => r.text());
    const index = parseYAML(indexYaml);

    // index.children contains the project tree
    // Each child is either inline content or an include reference
    const tree = await resolveIncludes(index.children, basePath);

    return {
        title: index.title,
        summary: index.summary,
        attributes: index.attributes,
        tree: tree  // Fully resolved navigation tree
    };
}
```

### Resolving Includes

Children in the index can be:
- **Inline**: Content directly in the index file
- **Include references**: `include: ./chapter-01.md` pointing to separate files

```javascript
async function resolveIncludes(children, basePath) {
    return Promise.all(children.map(async child => {
        if (child.include) {
            const content = await fetch(basePath + child.include).then(r => r.text());
            return parseFile(content, child.include);
        }
        return child; // Inline content
    }));
}
```

### Parsing Content Files

Codex Lite (`.md`) files have YAML frontmatter + Markdown body:

```javascript
function parseCodexLite(text) {
    const [_, frontmatter, body] = text.match(/^---\n([\s\S]*?)\n---\n([\s\S]*)$/);
    return {
        metadata: parseYAML(frontmatter),
        body: body
    };
}
```

Codex YAML (`.codex.yaml`) files have the body in the `body` field:

```javascript
function parseCodexYAML(text) {
    const data = parseYAML(text);
    return {
        metadata: data,
        body: data.body || ''
    };
}
```

## The Rendering Layer

### Markdown to HTML

The reader needs a Markdown renderer. Options the agent can choose from:

| Library | Size | Features | CDN Available |
|---------|------|----------|---------------|
| marked.js | 32KB | Fast, standard | Yes |
| markdown-it | 90KB | Extensible, plugins | Yes |
| showdown | 40KB | GitHub-flavored | Yes |
| micromark | 15KB | Minimal, fast | Yes |

For Level 1 readers, the agent uses a CDN-loaded library. For Level 2+, it can bundle.

### Content Display

```html
<!-- Basic content area -->
<article id="reader-content" class="prose">
    <!-- Rendered HTML from Markdown goes here -->
</article>
```

The reader applies typography styles via CSS:

```css
.prose {
    font-family: var(--font-body);
    font-size: var(--font-size);
    line-height: var(--line-height);
    max-width: var(--content-width);
    margin: 0 auto;
    padding: 2rem;
}
```

## The Navigation Layer

### Building the Tree

From the resolved index, build a navigation tree:

```javascript
function buildNavTree(tree, container) {
    const ul = document.createElement('ul');
    tree.forEach(item => {
        const li = document.createElement('li');
        const a = document.createElement('a');
        a.textContent = item.metadata.name || item.metadata.title;
        a.href = '#' + slugify(item.metadata.name);
        a.addEventListener('click', () => loadChapter(item));
        li.appendChild(a);

        // Recursive for nested structure
        if (item.children && item.children.length) {
            buildNavTree(item.children, li);
        }
        ul.appendChild(li);
    });
    container.appendChild(ul);
}
```

### Chapter Loading

Single-page readers load chapters dynamically:

```javascript
async function loadChapter(item) {
    const html = renderMarkdown(item.body);
    document.getElementById('reader-content').innerHTML = html;
    window.scrollTo(0, 0);

    // Update navigation state
    setActiveNavItem(item);
    updateTitle(item.metadata.name);
    updateURL(item);
}
```

Multi-page readers pre-generate all pages as static HTML.

## The Theme Layer

### CSS Custom Properties

Every Codex Reader uses CSS variables for theming:

```css
:root {
    /* Colors */
    --bg: #faf9f6;
    --text: #2d2d2d;
    --accent: #c49b66;
    --border: #e0ddd8;
    --nav-bg: #f5f3ef;

    /* Typography */
    --font-display: 'Crimson Pro', serif;
    --font-body: 'Source Serif 4', serif;
    --font-size: 18px;
    --line-height: 1.7;
    --content-width: 680px;
}

[data-theme="dark"] {
    --bg: #1a1a1a;
    --text: #e0ddd8;
    --accent: #c49b66;
    --border: #333;
    --nav-bg: #222;
}
```

### Theme Toggle

```javascript
function toggleTheme() {
    const current = document.documentElement.dataset.theme;
    document.documentElement.dataset.theme = current === 'dark' ? 'light' : 'dark';
    localStorage.setItem('theme', document.documentElement.dataset.theme);
}
```

## Reference: ChapterWise Codex Shell Components

The agent studies these to understand how a production reader works:

### index_tree_renderer.js
- Builds the project tree from `index.codex.yaml`
- Handles URL generation (slugification rules must match `url_path_resolver.py`)
- Manages tree expand/collapse state
- Highlights active item

### codex_theme_engine.js
- CSS custom property injection from theme YAML
- Theme persistence in localStorage
- Supports custom themes defined in the codex project

### codex_navigator.js
- SPA-style navigation (loads chapters without full page reload)
- Browser history integration (back/forward buttons work)
- Preloading of adjacent chapters

### table-of-contents-panel.js
- Extracts headings from rendered HTML
- Builds a nested TOC
- Scrollspy: highlights current section as user reads

### search_panel.js
- Full-text search across all loaded chapters
- Result highlighting
- Search index built on initial load

### typography-loader.js
- Google Fonts loading
- Font size/family/line-height controls
- Saved to localStorage

## Minimal Viable Reader

The simplest possible Codex Reader is ~100 lines of HTML/CSS/JS:

```html
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>My Novel</title>
    <script src="https://cdn.jsdelivr.net/npm/js-yaml@4/dist/js-yaml.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
    <style>
        /* ~30 lines of CSS for a clean reading experience */
    </style>
</head>
<body>
    <nav id="sidebar"></nav>
    <main id="content"></main>
    <script>
        // ~50 lines of JS: load index, build nav, render chapters
    </script>
</body>
</html>
```

This is the Level 1 reader. The agent generates it in seconds. From there, the writer iterates.
