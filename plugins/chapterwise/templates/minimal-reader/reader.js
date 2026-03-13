/**
 * Minimal Codex Reader
 *
 * Reads the project manifest from the embedded <script id="manifest"> tag,
 * renders the table of contents, loads chapter content on click, and provides
 * search, theme toggle, and keyboard navigation.
 *
 * Dependencies: marked.js (loaded from CDN in index.html)
 * Browser target: ES2020+ (modern browsers only)
 */

(function () {
  'use strict';

  // ============================================================
  // 1. State
  // ============================================================

  const state = {
    manifest: null,        // Parsed manifest object
    chapters: [],          // Flat ordered list of all chapters
    currentIndex: -1,      // Index of currently displayed chapter in flat list
    searchIndex: [],       // Search index: [{id, title, text}]
    searchTimeout: null,   // Debounce timer for search
    isSearching: false,    // Whether search results are shown
  };

  // ============================================================
  // 2. DOM References
  // ============================================================

  const dom = {
    sidebar: document.getElementById('sidebar'),
    sidebarToggle: document.getElementById('sidebar-toggle'),
    sidebarOverlay: document.getElementById('sidebar-overlay'),
    toc: document.getElementById('toc'),
    tocContainer: document.getElementById('toc-container'),
    searchInput: document.getElementById('search-input'),
    searchClear: document.getElementById('search-clear'),
    searchResults: document.getElementById('search-results'),
    searchResultList: document.getElementById('search-result-list'),
    searchEmpty: document.getElementById('search-empty'),
    readerContent: document.getElementById('reader-content'),
    pageNav: document.getElementById('page-nav'),
    prevLink: document.getElementById('prev-link'),
    nextLink: document.getElementById('next-link'),
    prevTitle: document.getElementById('prev-title'),
    nextTitle: document.getElementById('next-title'),
    themeToggle: document.getElementById('theme-toggle'),
    projectTitle: document.getElementById('project-title'),
  };

  // ============================================================
  // 3. Manifest Parsing
  // ============================================================

  function loadManifest() {
    const el = document.getElementById('manifest');
    if (!el) {
      console.error('Codex Reader: no manifest found. Make sure {{MANIFEST}} was replaced during build.');
      return null;
    }
    try {
      return JSON.parse(el.textContent);
    } catch (err) {
      console.error('Codex Reader: failed to parse manifest JSON:', err);
      return null;
    }
  }

  /**
   * Flatten the nested chapter tree into a single ordered array
   * for prev/next navigation.
   */
  function flattenChapters(chapters) {
    const flat = [];
    function walk(items) {
      items.forEach(item => {
        if (item.content !== undefined || item.path !== undefined) {
          flat.push(item);
        }
        if (item.children && item.children.length) {
          walk(item.children);
        }
      });
    }
    walk(chapters);
    return flat;
  }

  // ============================================================
  // 4. Table of Contents Rendering
  // ============================================================

  function renderTOC(structure, chapters) {
    const toc = dom.toc;
    toc.innerHTML = '';

    if (!structure || !structure.length) {
      // Flat chapter list (no parts)
      chapters.forEach((ch, idx) => {
        toc.appendChild(makeTOCItem(ch, idx));
      });
      return;
    }

    // Structured (parts containing chapters)
    structure.forEach(group => {
      const groupEl = document.createElement('li');
      groupEl.className = 'toc-group';

      if (group.title) {
        const label = document.createElement('span');
        label.className = 'toc-group-label';
        label.textContent = group.title;
        groupEl.appendChild(label);
      }

      if (group.children && group.children.length) {
        const nested = document.createElement('ul');
        nested.className = 'toc-nested';
        group.children.forEach(chId => {
          const idx = state.chapters.findIndex(c => c.id === chId);
          if (idx !== -1) {
            nested.appendChild(makeTOCItem(state.chapters[idx], idx));
          }
        });
        groupEl.appendChild(nested);
      }

      toc.appendChild(groupEl);
    });
  }

  function makeTOCItem(chapter, idx) {
    const li = document.createElement('li');
    li.className = 'toc-item';
    li.dataset.idx = idx;

    const a = document.createElement('a');
    a.className = 'toc-link';
    a.href = '#' + (chapter.id || slugify(chapter.title));
    a.textContent = chapter.title;
    a.addEventListener('click', e => {
      e.preventDefault();
      loadChapter(idx);
      closeSidebarMobile();
    });

    li.appendChild(a);
    return li;
  }

  function setActiveTOCItem(idx) {
    document.querySelectorAll('.toc-link.active').forEach(el => el.classList.remove('active'));
    const item = document.querySelector(`.toc-item[data-idx="${idx}"] .toc-link`);
    if (item) {
      item.classList.add('active');
      // Scroll into view in the sidebar without affecting main content
      const container = dom.tocContainer;
      const itemTop = item.getBoundingClientRect().top;
      const containerTop = container.getBoundingClientRect().top;
      const offset = itemTop - containerTop - container.clientHeight / 2;
      container.scrollTop += offset;
    }
  }

  // ============================================================
  // 5. Chapter Loading
  // ============================================================

  async function loadChapter(idx) {
    const chapter = state.chapters[idx];
    if (!chapter) return;

    state.currentIndex = idx;
    setActiveTOCItem(idx);
    updatePageNav(idx);
    updateDocumentTitle(chapter.title);
    updateURL(chapter);

    // Render content
    dom.readerContent.innerHTML = renderChapterHTML(chapter, idx);
    window.scrollTo({ top: 0, behavior: 'instant' });
  }

  function renderChapterHTML(chapter, idx) {
    const chapterNumber = idx + 1;
    const wordCountText = chapter.wordCount
      ? `${chapter.wordCount.toLocaleString()} words`
      : '';

    const tagsHTML = chapter.tags && chapter.tags.length
      ? `<span class="chapter-meta">${chapter.tags.join(' · ')}</span>`
      : '';

    const metaHTML = [wordCountText, tagsHTML].filter(Boolean).join(' &nbsp;·&nbsp; ');

    let body = '';
    if (chapter.content) {
      body = typeof marked !== 'undefined'
        ? marked.parse(chapter.content)
        : escapeHTML(chapter.content).replace(/\n/g, '<br>');
    } else if (chapter.path) {
      // File-based content: show loading state, then fetch
      setTimeout(() => fetchAndRenderChapter(chapter, idx), 0);
      body = '<p class="welcome-hint">Loading...</p>';
    }

    // Atlas section rendering
    if (chapter.type === 'characters' && chapter.entries) {
      body = renderCharacterCards(chapter.entries);
    } else if (chapter.type === 'timeline' && chapter.entries) {
      body = renderTimeline(chapter.entries);
    } else if (chapter.type === 'themes' && chapter.entries) {
      body = renderThemes(chapter.entries);
    }

    return `
      <div class="chapter-header">
        <span class="chapter-number">Chapter ${chapterNumber}</span>
        <h1 class="chapter-title">${escapeHTML(chapter.title)}</h1>
        ${metaHTML ? `<div class="chapter-meta">${metaHTML}</div>` : ''}
      </div>
      <div class="chapter-body">${body}</div>
    `;
  }

  async function fetchAndRenderChapter(chapter, idx) {
    try {
      const res = await fetch(chapter.path);
      if (!res.ok) throw new Error('HTTP ' + res.status);
      const text = await res.text();
      const html = typeof marked !== 'undefined' ? marked.parse(text) : escapeHTML(text);
      const bodyEl = document.querySelector('.chapter-body');
      if (bodyEl && state.currentIndex === idx) {
        bodyEl.innerHTML = html;
      }
    } catch (err) {
      const bodyEl = document.querySelector('.chapter-body');
      if (bodyEl) {
        bodyEl.innerHTML = `<p style="color:var(--codex-text-muted)">Could not load chapter content.</p>`;
      }
    }
  }

  // ============================================================
  // 6. Atlas Components
  // ============================================================

  function renderCharacterCards(entries) {
    if (!entries || !entries.length) return '<p class="welcome-hint">No characters found.</p>';
    const grid = entries.map(char => {
      const role = char.role || 'supporting';
      const traits = (char.traits || char.tags || [])
        .map(t => `<span class="trait-tag">${escapeHTML(t)}</span>`)
        .join('');
      const arc = char.arc || char.summary || '';
      const chapters = char.chapterCount
        ? `Appears in ${char.chapterCount} chapter${char.chapterCount !== 1 ? 's' : ''}`
        : '';
      return `
        <div class="character-card" id="char-${slugify(char.name)}">
          <div class="character-card-name">${escapeHTML(char.name)}</div>
          <span class="character-card-role role-${slugify(role)}">${escapeHTML(role)}</span>
          ${traits ? `<div class="character-card-traits">${traits}</div>` : ''}
          ${arc ? `<div class="character-card-arc">${escapeHTML(arc)}</div>` : ''}
          ${chapters ? `<div class="character-card-footer">${chapters}</div>` : ''}
        </div>
      `;
    }).join('');
    return `
      <h2 class="atlas-section-header">Characters</h2>
      <div class="character-grid">${grid}</div>
    `;
  }

  function renderTimeline(entries) {
    if (!entries || !entries.length) return '<p class="welcome-hint">No timeline events found.</p>';
    let currentAct = null;
    const items = entries.map(event => {
      let actDivider = '';
      if (event.act && event.act !== currentAct) {
        currentAct = event.act;
        actDivider = `<li class="timeline-act-divider">${escapeHTML(event.act)}</li>`;
      }
      const characters = (event.characters || []).join(', ');
      return `
        ${actDivider}
        <li class="timeline-entry" id="event-${slugify(event.title)}">
          <div class="timeline-event-title">${escapeHTML(event.title)}</div>
          ${event.chapter ? `<div class="timeline-event-meta">${escapeHTML(event.chapter)}</div>` : ''}
          ${characters ? `<div class="timeline-event-characters">${escapeHTML(characters)}</div>` : ''}
        </li>
      `;
    }).join('');
    return `
      <h2 class="atlas-section-header">Timeline</h2>
      <ul class="timeline">${items}</ul>
    `;
  }

  function renderThemes(entries) {
    if (!entries || !entries.length) return '<p class="welcome-hint">No themes found.</p>';
    const items = entries.map(theme => {
      const chapters = theme.chapters ? `Appears in: ${escapeHTML(theme.chapters.join(', '))}` : '';
      return `
        <div class="theme-entry" id="theme-${slugify(theme.name)}">
          <div class="theme-name">${escapeHTML(theme.name)}</div>
          ${theme.prominence ? `<span class="theme-prominence">${escapeHTML(theme.prominence)}</span>` : ''}
          ${theme.description ? `<p class="theme-description">${escapeHTML(theme.description)}</p>` : ''}
          ${chapters ? `<div class="theme-chapters">${chapters}</div>` : ''}
        </div>
      `;
    }).join('');
    return `
      <h2 class="atlas-section-header">Themes</h2>
      <div>${items}</div>
    `;
  }

  // ============================================================
  // 7. Navigation
  // ============================================================

  function updatePageNav(idx) {
    const hasPrev = idx > 0;
    const hasNext = idx < state.chapters.length - 1;

    dom.pageNav.hidden = false;

    if (hasPrev) {
      dom.prevLink.hidden = false;
      dom.prevTitle.textContent = state.chapters[idx - 1].title;
      dom.prevLink.onclick = e => { e.preventDefault(); loadChapter(idx - 1); };
    } else {
      dom.prevLink.hidden = true;
    }

    if (hasNext) {
      dom.nextLink.hidden = false;
      dom.nextTitle.textContent = state.chapters[idx + 1].title;
      dom.nextLink.onclick = e => { e.preventDefault(); loadChapter(idx + 1); };
    } else {
      dom.nextLink.hidden = true;
    }

    if (!hasPrev && !hasNext) {
      dom.pageNav.hidden = true;
    }
  }

  function updateDocumentTitle(chapterTitle) {
    const projectTitle = state.manifest.title || '';
    document.title = chapterTitle
      ? `${chapterTitle} — ${projectTitle}`
      : projectTitle;
  }

  function updateURL(chapter) {
    const hash = '#' + (chapter.id || slugify(chapter.title));
    history.replaceState(null, '', hash);
  }

  function navigateByHash() {
    const hash = window.location.hash.slice(1);
    if (!hash) {
      // Load first chapter by default
      if (state.chapters.length) loadChapter(0);
      return;
    }
    const idx = state.chapters.findIndex(
      ch => ch.id === hash || slugify(ch.title) === hash
    );
    if (idx !== -1) loadChapter(idx);
    else if (state.chapters.length) loadChapter(0);
  }

  // ============================================================
  // 8. Search
  // ============================================================

  function buildSearchIndex(chapters) {
    return chapters.map(ch => ({
      id: ch.id || slugify(ch.title),
      title: ch.title || '',
      text: stripHTML(ch.content || ''),
    }));
  }

  function performSearch(query) {
    const q = query.trim().toLowerCase();
    if (!q) {
      clearSearch();
      return;
    }

    state.isSearching = true;
    dom.searchResults.hidden = false;
    dom.tocContainer.hidden = true;
    dom.searchClear.hidden = false;

    const results = [];
    state.searchIndex.forEach((entry, idx) => {
      const titleMatch = entry.title.toLowerCase().includes(q);
      const bodyMatch = entry.text.toLowerCase().includes(q);
      if (titleMatch || bodyMatch) {
        // Find excerpt around match
        let excerpt = '';
        const pos = entry.text.toLowerCase().indexOf(q);
        if (pos !== -1) {
          const start = Math.max(0, pos - 60);
          const end = Math.min(entry.text.length, pos + q.length + 60);
          excerpt = (start > 0 ? '...' : '') +
            entry.text.slice(start, end).replace(
              new RegExp(escapeRegex(query.trim()), 'gi'),
              match => `<mark>${escapeHTML(match)}</mark>`
            ) +
            (end < entry.text.length ? '...' : '');
        }
        results.push({ idx, title: entry.title, excerpt, titleMatch });
      }
    });

    // Sort: title matches first
    results.sort((a, b) => (b.titleMatch ? 1 : 0) - (a.titleMatch ? 1 : 0));

    renderSearchResults(results, query);
  }

  function renderSearchResults(results, query) {
    dom.searchResultList.innerHTML = '';

    if (!results.length) {
      dom.searchEmpty.hidden = false;
      return;
    }

    dom.searchEmpty.hidden = true;
    results.slice(0, 20).forEach(result => {
      const li = document.createElement('li');
      li.className = 'search-result-item';
      li.setAttribute('role', 'option');
      li.innerHTML = `
        <div class="search-result-title">${escapeHTML(result.title)}</div>
        ${result.excerpt ? `<div class="search-result-excerpt">${result.excerpt}</div>` : ''}
      `;
      li.addEventListener('click', () => {
        loadChapter(result.idx);
        clearSearch();
        dom.searchInput.value = '';
        closeSidebarMobile();
      });
      dom.searchResultList.appendChild(li);
    });
  }

  function clearSearch() {
    state.isSearching = false;
    dom.searchResults.hidden = true;
    dom.tocContainer.hidden = false;
    dom.searchClear.hidden = true;
    dom.searchEmpty.hidden = true;
  }

  // ============================================================
  // 9. Theme Toggle
  // ============================================================

  function applyTheme(theme) {
    document.documentElement.dataset.theme = theme;
    dom.themeToggle.querySelector('.theme-icon').innerHTML =
      theme === 'dark' ? '&#9790;' : '&#9788;';
    localStorage.setItem('codex-theme', theme);
  }

  function toggleTheme() {
    const current = document.documentElement.dataset.theme || 'light';
    applyTheme(current === 'dark' ? 'light' : 'dark');
  }

  function loadSavedTheme() {
    const saved = localStorage.getItem('codex-theme');
    if (saved) {
      applyTheme(saved);
    } else if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
      applyTheme('dark');
    }
  }

  // ============================================================
  // 10. Mobile Sidebar
  // ============================================================

  function openSidebarMobile() {
    dom.sidebar.classList.add('open');
    dom.sidebarOverlay.hidden = false;
    dom.sidebarToggle.setAttribute('aria-expanded', 'true');
    document.body.style.overflow = 'hidden';
  }

  function closeSidebarMobile() {
    dom.sidebar.classList.remove('open');
    dom.sidebarOverlay.hidden = true;
    dom.sidebarToggle.setAttribute('aria-expanded', 'false');
    document.body.style.overflow = '';
  }

  // ============================================================
  // 11. Keyboard Navigation
  // ============================================================

  function setupKeyboardNav() {
    document.addEventListener('keydown', e => {
      // Don't intercept when typing in input fields
      if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;

      switch (e.key) {
        case 'ArrowRight':
        case 'ArrowDown':
          if (state.currentIndex < state.chapters.length - 1) {
            e.preventDefault();
            loadChapter(state.currentIndex + 1);
          }
          break;

        case 'ArrowLeft':
        case 'ArrowUp':
          if (state.currentIndex > 0) {
            e.preventDefault();
            loadChapter(state.currentIndex - 1);
          }
          break;

        case '/':
          e.preventDefault();
          dom.searchInput.focus();
          dom.searchInput.select();
          openSidebarMobile();
          break;

        case 'Escape':
          if (state.isSearching) {
            clearSearch();
            dom.searchInput.value = '';
          }
          closeSidebarMobile();
          break;
      }
    });
  }

  // ============================================================
  // 12. Utility Functions
  // ============================================================

  function slugify(str) {
    return String(str)
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, '-')
      .replace(/^-+|-+$/g, '');
  }

  function escapeHTML(str) {
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;');
  }

  function escapeRegex(str) {
    return str.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  }

  function stripHTML(html) {
    const div = document.createElement('div');
    div.innerHTML = html;
    return div.textContent || div.innerText || '';
  }

  // ============================================================
  // 13. Event Listeners
  // ============================================================

  function setupEventListeners() {
    // Theme toggle
    dom.themeToggle.addEventListener('click', toggleTheme);

    // Search input with debounce
    dom.searchInput.addEventListener('input', e => {
      clearTimeout(state.searchTimeout);
      state.searchTimeout = setTimeout(() => {
        performSearch(e.target.value);
      }, 200);
    });

    // Search clear button
    dom.searchClear.addEventListener('click', () => {
      dom.searchInput.value = '';
      clearSearch();
      dom.searchInput.focus();
    });

    // Mobile sidebar toggle
    dom.sidebarToggle.addEventListener('click', () => {
      if (dom.sidebar.classList.contains('open')) {
        closeSidebarMobile();
      } else {
        openSidebarMobile();
      }
    });

    // Mobile overlay click to close
    dom.sidebarOverlay.addEventListener('click', closeSidebarMobile);

    // Handle back/forward browser navigation
    window.addEventListener('popstate', navigateByHash);
  }

  // ============================================================
  // 14. Init
  // ============================================================

  function init() {
    // Load and parse the manifest
    state.manifest = loadManifest();
    if (!state.manifest) {
      dom.readerContent.innerHTML = '<p style="color:var(--codex-text-muted);padding:2rem">Reader configuration not found. Rebuild the reader.</p>';
      return;
    }

    // Update project title in sidebar
    if (state.manifest.title && dom.projectTitle) {
      dom.projectTitle.textContent = state.manifest.title;
    }

    // Flatten chapters for sequential navigation
    state.chapters = flattenChapters(state.manifest.chapters || []);

    // Build search index
    state.searchIndex = buildSearchIndex(state.chapters);

    // Render table of contents
    renderTOC(state.manifest.structure || null, state.chapters);

    // Apply saved theme (before first render to avoid flash)
    loadSavedTheme();

    // Set up all event listeners
    setupEventListeners();
    setupKeyboardNav();

    // Load chapter from URL hash, or first chapter
    navigateByHash();
  }

  // Run after DOM is ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }

})();
