/**
 * Academic Codex Reader
 *
 * Extends the minimal reader with:
 * - Footnote rendering (hover popup + bottom-of-chapter list)
 * - Annotation sidebar (analysis data display)
 * - Academic chapter header treatment
 * - Italic chapter titles in nav
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
    manifest: null,
    chapters: [],
    currentIndex: -1,
    searchIndex: [],
    searchTimeout: null,
    isSearching: false,
    footnotePopupVisible: false,
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
    annotationMargin: document.getElementById('annotation-margin'),
    pageNav: document.getElementById('page-nav'),
    prevLink: document.getElementById('prev-link'),
    nextLink: document.getElementById('next-link'),
    prevTitle: document.getElementById('prev-title'),
    nextTitle: document.getElementById('next-title'),
    themeToggle: document.getElementById('theme-toggle'),
    projectTitle: document.getElementById('project-title'),
    footnotePopup: document.getElementById('footnote-popup'),
    footnotePopupContent: document.getElementById('footnote-popup-content'),
    footnotePopupClose: document.getElementById('footnote-popup-close'),
  };

  // ============================================================
  // 3. Manifest Parsing
  // ============================================================

  function loadManifest() {
    const el = document.getElementById('manifest');
    if (!el) {
      console.error('Academic Codex Reader: no manifest found.');
      return null;
    }
    try {
      return JSON.parse(el.textContent);
    } catch (err) {
      console.error('Academic Codex Reader: failed to parse manifest JSON:', err);
      return null;
    }
  }

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
  // 4. Table of Contents
  // ============================================================

  function renderTOC(structure, chapters) {
    const toc = dom.toc;
    toc.innerHTML = '';

    if (!structure || !structure.length) {
      chapters.forEach((ch, idx) => {
        toc.appendChild(makeTOCItem(ch, idx));
      });
      return;
    }

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
      const container = dom.tocContainer;
      const offset = item.getBoundingClientRect().top - container.getBoundingClientRect().top - container.clientHeight / 2;
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

    // Clear annotation margin
    dom.annotationMargin.innerHTML = '';

    // Render chapter
    dom.readerContent.innerHTML = renderChapterHTML(chapter, idx);
    window.scrollTo({ top: 0, behavior: 'instant' });

    // Post-render: process footnotes and analysis data
    processFootnotes(chapter);
    renderAnalysisAnnotations(chapter);
  }

  function renderChapterHTML(chapter, idx) {
    const chapterNumber = idx + 1;
    const wordCountText = chapter.wordCount
      ? `${chapter.wordCount.toLocaleString()} words`
      : '';
    const metaHTML = wordCountText || '';

    let body = '';
    if (chapter.content) {
      body = typeof marked !== 'undefined'
        ? marked.parse(chapter.content)
        : escapeHTML(chapter.content).replace(/\n/g, '<br>');
    } else if (chapter.path) {
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
        processFootnotes(chapter);
      }
    } catch {
      const bodyEl = document.querySelector('.chapter-body');
      if (bodyEl) {
        bodyEl.innerHTML = `<p style="color:var(--codex-text-muted)">Could not load chapter content.</p>`;
      }
    }
  }

  // ============================================================
  // 6. Footnote Processing
  // ============================================================

  /**
   * After rendering, find footnote references in the text and:
   * 1. Replace [^1] markers with clickable superscripts
   * 2. Collect footnote definitions
   * 3. Render footnote list at bottom of chapter
   * 4. Wire hover popup
   */
  function processFootnotes(chapter) {
    const body = document.querySelector('.chapter-body');
    if (!body) return;

    // Collect any footnote data from the chapter manifest entry
    const footnotes = chapter.footnotes || [];
    if (!footnotes.length) {
      // Also scan rendered HTML for markdown footnote patterns
      // marked.js renders footnotes as <section class="footnotes">
      const renderedFootnoteSection = body.querySelector('section.footnotes, .footnotes');
      if (renderedFootnoteSection) {
        styleRenderedFootnotes(renderedFootnoteSection);
      }
      wireFootnoteRefs(body, []);
      return;
    }

    // Build footnote section from manifest data
    const section = document.createElement('div');
    section.className = 'footnotes-section';
    section.innerHTML = `<div class="footnotes-heading">Notes</div>`;
    const list = document.createElement('ol');
    list.className = 'footnotes-list';

    footnotes.forEach((fn, i) => {
      const li = document.createElement('li');
      li.className = 'footnote-item';
      li.id = `fn-${i + 1}`;
      li.innerHTML = `
        <span class="footnote-item-number">${i + 1}.</span>
        <span class="footnote-item-text">${escapeHTML(fn.text || fn)}</span>
      `;
      list.appendChild(li);
    });

    section.appendChild(list);
    body.appendChild(section);

    wireFootnoteRefs(body, footnotes);
  }

  function styleRenderedFootnotes(section) {
    // marked.js renders <section class="footnotes"> — add our classes
    section.classList.add('footnotes-section');
    const hr = section.querySelector('hr');
    if (hr) {
      hr.replaceWith(Object.assign(document.createElement('div'), {
        className: 'footnotes-heading',
        textContent: 'Notes'
      }));
    }
    const ol = section.querySelector('ol');
    if (ol) ol.className = 'footnotes-list';
    section.querySelectorAll('li').forEach(li => li.classList.add('footnote-item'));
  }

  function wireFootnoteRefs(body, footnotes) {
    // Wire clicks on <sup> footnote markers (.footnote-ref or data-footnote-ref)
    body.querySelectorAll('[data-footnote-ref], sup a[href^="#fn"]').forEach(ref => {
      ref.classList.add('footnote-ref');
      ref.addEventListener('click', e => {
        e.preventDefault();
        const fnId = ref.getAttribute('href') || ref.dataset.footnoteRef;
        const fnNum = parseInt(fnId.replace(/\D/g, '')) || 1;
        const fnData = footnotes[fnNum - 1];
        const fnText = fnData ? (fnData.text || fnData) : null;

        // Fall back to rendered footnote item text
        const fnItem = document.getElementById('fn-' + fnNum) ||
          document.getElementById('fn' + fnNum) ||
          document.getElementById('user-content-fn-' + fnNum);

        const text = fnText ||
          (fnItem ? fnItem.querySelector('.footnote-item-text, p')?.textContent : null) ||
          'Footnote ' + fnNum;

        showFootnotePopup(text, e.clientX, e.clientY);
      });

      // Keyboard accessibility
      ref.addEventListener('keydown', e => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          ref.click();
        }
      });
    });
  }

  function showFootnotePopup(text, x, y) {
    dom.footnotePopupContent.textContent = text;
    dom.footnotePopup.hidden = false;
    state.footnotePopupVisible = true;

    // Position near the click, keeping within viewport
    const popup = dom.footnotePopup;
    popup.style.top = '0';
    popup.style.left = '0';

    requestAnimationFrame(() => {
      const pw = popup.offsetWidth;
      const ph = popup.offsetHeight;
      const vw = window.innerWidth;
      const vh = window.innerHeight;

      let left = x + 12;
      let top = y + 12;

      if (left + pw > vw - 12) left = vw - pw - 12;
      if (top + ph > vh - 12) top = y - ph - 12;
      if (top < 12) top = 12;
      if (left < 12) left = 12;

      popup.style.left = left + 'px';
      popup.style.top = top + 'px';
    });
  }

  function hideFootnotePopup() {
    dom.footnotePopup.hidden = true;
    state.footnotePopupVisible = false;
  }

  // ============================================================
  // 7. Analysis Annotations
  // ============================================================

  /**
   * If the chapter has analysis data (from .analysis.json integration),
   * render it in the annotation margin.
   */
  function renderAnalysisAnnotations(chapter) {
    const margin = dom.annotationMargin;
    margin.innerHTML = '';

    const analysis = chapter.analysis;
    if (!analysis || typeof analysis !== 'object') return;

    const panel = document.createElement('div');
    panel.className = 'analysis-panel';

    const heading = document.createElement('div');
    heading.className = 'analysis-panel-heading';
    heading.textContent = 'Analysis';
    panel.appendChild(heading);

    // Render key analysis fields
    const displayFields = [
      { key: 'tone', label: 'Tone' },
      { key: 'pacing', label: 'Pacing' },
      { key: 'pov', label: 'Point of View' },
      { key: 'tension', label: 'Tension' },
      { key: 'themes', label: 'Themes' },
      { key: 'characters_present', label: 'Characters' },
      { key: 'summary', label: 'Summary' },
      { key: 'writing_style', label: 'Style' },
    ];

    let hasContent = false;

    displayFields.forEach(({ key, label }) => {
      const value = analysis[key];
      if (!value) return;

      const entry = document.createElement('div');
      entry.className = 'analysis-entry';

      const valueText = Array.isArray(value)
        ? value.join(', ')
        : String(value);

      entry.innerHTML = `
        <div class="analysis-key">${escapeHTML(label)}</div>
        <div class="analysis-value">${escapeHTML(valueText)}</div>
      `;
      panel.appendChild(entry);
      hasContent = true;
    });

    if (hasContent) {
      margin.appendChild(panel);
    }
  }

  // ============================================================
  // 8. Atlas Components
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
  // 9. Navigation
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

    if (!hasPrev && !hasNext) dom.pageNav.hidden = true;
  }

  function updateDocumentTitle(chapterTitle) {
    const projectTitle = state.manifest.title || '';
    document.title = chapterTitle ? `${chapterTitle} — ${projectTitle}` : projectTitle;
  }

  function updateURL(chapter) {
    history.replaceState(null, '', '#' + (chapter.id || slugify(chapter.title)));
  }

  function navigateByHash() {
    const hash = window.location.hash.slice(1);
    if (!hash) {
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
  // 10. Search
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
    if (!q) { clearSearch(); return; }

    state.isSearching = true;
    dom.searchResults.hidden = false;
    dom.tocContainer.hidden = true;
    dom.searchClear.hidden = false;

    const results = [];
    state.searchIndex.forEach((entry, idx) => {
      const titleMatch = entry.title.toLowerCase().includes(q);
      const bodyMatch = entry.text.toLowerCase().includes(q);
      if (titleMatch || bodyMatch) {
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

    results.sort((a, b) => (b.titleMatch ? 1 : 0) - (a.titleMatch ? 1 : 0));
    renderSearchResults(results);
  }

  function renderSearchResults(results) {
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
  // 11. Theme Toggle
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
  // 12. Mobile Sidebar
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
  // 13. Keyboard Navigation
  // ============================================================

  function setupKeyboardNav() {
    document.addEventListener('keydown', e => {
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
          if (state.footnotePopupVisible) {
            hideFootnotePopup();
          } else if (state.isSearching) {
            clearSearch();
            dom.searchInput.value = '';
          } else {
            closeSidebarMobile();
          }
          break;
      }
    });

    // Close footnote popup on outside click
    document.addEventListener('click', e => {
      if (state.footnotePopupVisible &&
          !dom.footnotePopup.contains(e.target) &&
          !e.target.closest('.footnote-ref')) {
        hideFootnotePopup();
      }
    });
  }

  // ============================================================
  // 14. Utility
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
  // 15. Event Listeners
  // ============================================================

  function setupEventListeners() {
    dom.themeToggle.addEventListener('click', toggleTheme);

    dom.searchInput.addEventListener('input', e => {
      clearTimeout(state.searchTimeout);
      state.searchTimeout = setTimeout(() => performSearch(e.target.value), 200);
    });

    dom.searchClear.addEventListener('click', () => {
      dom.searchInput.value = '';
      clearSearch();
      dom.searchInput.focus();
    });

    dom.sidebarToggle.addEventListener('click', () => {
      if (dom.sidebar.classList.contains('open')) {
        closeSidebarMobile();
      } else {
        openSidebarMobile();
      }
    });

    dom.sidebarOverlay.addEventListener('click', closeSidebarMobile);

    // Footnote popup close button
    if (dom.footnotePopupClose) {
      dom.footnotePopupClose.addEventListener('click', hideFootnotePopup);
    }

    window.addEventListener('popstate', navigateByHash);
  }

  // ============================================================
  // 16. Init
  // ============================================================

  function init() {
    state.manifest = loadManifest();
    if (!state.manifest) {
      dom.readerContent.innerHTML = '<p style="color:var(--codex-text-muted);padding:2rem">Reader configuration not found. Rebuild the reader.</p>';
      return;
    }

    if (state.manifest.title && dom.projectTitle) {
      dom.projectTitle.textContent = state.manifest.title;
    }

    state.chapters = flattenChapters(state.manifest.chapters || []);
    state.searchIndex = buildSearchIndex(state.chapters);

    renderTOC(state.manifest.structure || null, state.chapters);

    loadSavedTheme();
    setupEventListeners();
    setupKeyboardNav();

    navigateByHash();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }

})();
