# Codex Reader Recipe — Overview

## What It Is

The Codex Reader is a custom reading experience the agent builds for your codex content. Vibe-code your own reader. The agent studies ChapterWise's codex shell as a reference implementation and helps you scaffold something that's yours: your design, your typography, your layout, your code.

## The Name

It's called a **Reader**, not a viewer. People don't "view" novels. They read them. A Codex Reader is a purpose-built reading application for your literary content. It could be a single HTML file, a full static site, or anything in between.

## The Idea

ChapterWise.app already has a powerful codex shell with tree navigation, TOC, themes, typography, search. It's beautiful and full-featured. But some people want to own their presentation layer:

- An author wants a custom reading experience for their portfolio
- A developer wants to build a book club site powered by codex data
- A writer wants a personal reader with their preferred fonts and colors
- A publisher wants to white-label a reading experience

The agent reads the reference implementation (`codex_shell.html`, `index_tree_renderer.js`, `codex_theme_engine.js`), understands the patterns, and builds something custom. Not a copy. A fresh implementation using the writer's preferred tech, aesthetic, and feature set.

## Documents in This Directory

| Doc | Purpose |
|-----|---------|
| `00-OVERVIEW.md` | This document |
| `01-READER-RECIPE.md` | Full spec: levels, reference mapping, recipe format, templates |
| `02-READER-ARCHITECTURE.md` | How a Codex Reader works: parsing index.codex.yaml, rendering content, navigation |
| `03-READER-TEMPLATES.md` | Template library: minimal, academic (ship with v2.0.0), plus future: portfolio, interactive fiction, book-club, chapbook |

## Core Behaviors

- **Three levels**: Static HTML (single file, open in browser) → Enhanced (tree nav, TOC, themes) → Custom Publishing (multi-page static site, deploy-ready)
- **Reference-informed, not copied**: Agent studies the ChapterWise codex shell to learn patterns, then builds something fresh
- **Iterative**: Writer says "build me a reader," agent builds it, writer says "darker, bigger fonts, sidebar on right," agent iterates
- **Tech-agnostic**: Vanilla HTML/CSS/JS by default. React, Vue, Svelte if the writer prefers.
- **Self-contained**: The reader works without ChapterWise.app. Just HTML + your codex files.
- **Recipe saved**: Like import and analysis recipes, the reader recipe saves design choices for iteration
