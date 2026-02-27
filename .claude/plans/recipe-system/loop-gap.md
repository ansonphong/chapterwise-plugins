# Recipe System Plan Gap Scanner — Ralph Loop Prompt

> **Usage:** `/ralph-loop:ralph-loop ".claude/plans/recipe-system/loop-gap.md" --max-iterations 50 --completion-promise "NO GAPS REMAINING"`

You are an iterative plan-quality auditor. Each iteration, you spawn **one parallel Opus agent per plan file** to find gaps, then collect results and fix everything.

## Plan Directory

```
.claude/plans/recipe-system/
```

## Editable Files (one agent each)

| # | File | Agent Focus |
|---|------|-------------|
| 1 | `01-PLUGIN-STRUCTURE.md` | Plugin structure — file layout matches master plan, directory names consistent across all docs |
| 2 | `02-RECIPE-SYSTEM.md` | Recipe system — recipe folder paths, YAML schema fields match implementation plan |
| 3 | `LANGUAGE-GUIDE.md` | Language guide — all recipe types covered, examples match command names in plugin structure |
| 4 | `IMPLEMENTATION-PLAN.md` | Implementation plan — file inventory matches plugin structure, merge strategy consistent |
| 5 | `import-recipe/00-OVERVIEW.md` | Import overview — command names, file paths match plugin structure and master plan |
| 6 | `import-recipe/01-AGENT-WORKFLOW.md` | Import workflow — steps reference correct scripts/patterns from plugin structure |
| 7 | `import-recipe/02-PATTERN-SCRIPTS.md` | Pattern scripts — script names, interfaces match build plan tasks |
| 8 | `import-recipe/03-INTERVIEW-AND-PREFERENCES.md` | Interview — preferences.yaml fields match recipe.yaml schema in 02-RECIPE-SYSTEM |
| 9 | `import-recipe/04-OUTPUT-FORMAT.md` | Output format — codex structure matches codex_writer expectations |
| 10 | `import-recipe/05-SUPPORTED-SOURCES.md` | Supported sources — format list matches converter files in build plans |
| 11 | `analysis-recipe/00-OVERVIEW.md` | Analysis overview — command name, module references match plugin structure |
| 12 | `analysis-recipe/01-ANALYSIS-RECIPE.md` | Analysis recipe — course system, module loader interface match build plan |
| 13 | `atlas-recipe/00-OVERVIEW.md` | Atlas overview — command name, four-pass pipeline consistent with build plan |
| 14 | `atlas-recipe/01-ATLAS-RECIPE.md` | Atlas recipe — pass descriptions, section names match atlas-sections doc |
| 15 | `atlas-recipe/02-UPDATE-ATLAS.md` | Atlas update — incremental update flow, staleness logic consistent |
| 16 | `atlas-recipe/03-ATLAS-SECTIONS.md` | Atlas sections — section names match atlas recipe, field names consistent |
| 17 | `reader-recipe/00-OVERVIEW.md` | Reader overview — command name, template names match plugin structure |
| 18 | `reader-recipe/01-READER-RECIPE.md` | Reader recipe — atlas dependency, template names match build plan |
| 19 | `reader-recipe/02-READER-ARCHITECTURE.md` | Reader architecture — HTML/CSS/JS files match template file list in build plan |
| 20 | `reader-recipe/03-READER-TEMPLATES.md` | Reader templates — template names (minimal, academic) match build plan tasks |
| 21 | `build-plans/PHASE-0-SCAFFOLD.md` | Phase 0 — directory names match plugin structure, task IDs match master plan |
| 22 | `build-plans/AGENT-1-IMPORT.md` | Agent 1 Import — file list matches Phase 2 tasks in master plan |
| 23 | `build-plans/AGENT-2-ANALYSIS.md` | Agent 2 Analysis — file list matches Phase 3 tasks in master plan |
| 24 | `build-plans/AGENT-3-ATLAS.md` | Agent 3 Atlas — file list matches Phase 3 tasks in master plan |
| 25 | `build-plans/AGENT-4-READER.md` | Agent 4 Reader — file list, template inventory match Phase 3 tasks in master plan |
| 26 | `build-plans/PHASE-2-4-INTEGRATION.md` | Integration — merge steps cover all 4 agents, test flow references correct commands |
| 27 | `ralph-loop/00-master-plan.md` | Master plan — task IDs sequential, file paths match plugin structure, test commands valid |
| 28 | `ralph-loop/2026-02-27-phase-1-scaffold.md` | Phase 1 detail — tasks match master plan Tasks 1-10, file paths consistent |
| 29 | `ralph-loop/2026-02-27-phase-2-import.md` | Phase 2 detail — tasks match master plan Tasks 11-18, script interfaces consistent |
| 30 | `ralph-loop/2026-02-27-phase-3-parallel.md` | Phase 3 detail — tasks match master plan Tasks 19-24, parallel agent dispatch consistent with build-plans AGENT-2/3/4, no hidden cross-agent dependencies |
| 31 | `ralph-loop/2026-02-27-phase-4-patterns.md` | Phase 4 detail — tasks match master plan Tasks 25-30, converter pattern convention (JSON-in/out, CONFIG block) consistent with import-recipe/02-PATTERN-SCRIPTS and 05-SUPPORTED-SOURCES |
| 32 | `ralph-loop/2026-02-27-phase-5-cross-cutting.md` | Phase 5 detail — tasks match master plan Tasks 31-32, status and pipeline command specs consistent with LANGUAGE-GUIDE and 00-OVERVIEW cross-cutting sections |
| 33 | `ralph-loop/2026-02-27-phase-6-migration.md` | Phase 6 detail — tasks match master plan Tasks 33-35, deprecation stub content consistent with 01-PLUGIN-STRUCTURE migration section and PHASE-2-4-INTEGRATION |
| 34 | `ralph-loop/2026-02-27-phase-7-verification.md` | Phase 7 detail — tasks match master plan Tasks 36-39, QA checks reference correct command files and banned phrases list consistent with LANGUAGE-GUIDE |

## Read-Only Reference Files (agents can read but NEVER edit)

```
.claude/plans/recipe-system/00-OVERVIEW.md
.claude/plans/recipe-system/10-DOCS-AND-THREE-PATHS.md
```

## Gap Categories (every agent checks ALL of these for its file)

### 1. Cross-Reference Integrity
- Task IDs match between master/foundation and phase docs
- Test class names match between master and phase docs
- Test file paths match between master and phase docs
- pytest command strings target the correct file::class
- File lists match between master and phase docs
- Phase checkpoint commands cover all files in the phase

### 2. Internal Consistency
- Task numbering sequential, no gaps or duplicates
- Checklist items match tasks defined in same doc
- Every task has: checkbox, bold task number, description, Test line, Files line
- Test commands use valid pytest syntax
- No dangling references to nonexistent tasks/files/classes

### 3. Completeness
- Every phase doc task appears in master plan
- Every master plan task for a phase appears in that phase doc
- Phase checkpoints include test commands AND review scope
- Import paths reference modules that exist after prior tasks
- Rationale/Implementation present where non-obvious

### 4. Terminology & Naming
- Consistent terminology (follow existing conventions)
- Class names: PascalCase, descriptive
- Test classes start with `Test`
- File names: snake_case.py, kebab-case.svelte
- Command file names: kebab-case.md
- Recipe folder paths: `.chapterwise/{type}-recipe/` consistently

### 5. Dependency & Ordering
- No forward references without dependency notes
- Phase ordering logical
- Task ordering within phase follows build sequence
- Phase 3 parallel tasks have no hidden dependencies on each other

### 6. Structural Quality
- No orphan tasks (in phase but not master)
- No phantom tasks (in master but not phase)
- Consistent markdown formatting
- No duplicate content between design docs and build plans (build plans should reference, not repeat)

### 7. Contract & API Gaps
- Script interfaces (JSON stdin → stdout) consistent across all docs that reference them
- recipe.yaml schema fields match all docs that reference recipe contents
- Command trigger names consistent across plugin structure, implementation plan, and build plans
- Module names in analysis recipe match actual module file list
- Atlas section names consistent between atlas recipe and atlas sections doc
- Template file lists match between reader architecture and build plan

## Procedure (follow EXACTLY each iteration)

### Step 1 — Spawn parallel agents

Use the **Task tool** to spawn one **Opus agent** (`model: "opus"`, `subagent_type: "general-purpose"`) per editable file (34 agents total). All in a **single message** for parallel execution.

Each agent's prompt MUST include:
1. Its primary file (the one it audits and can edit)
2. Full list of all other plan files (for cross-reference)
3. The 7 gap categories above
4. Instructions: read primary fully, read master for cross-ref, fix own file, report cross-file gaps, preserve checkboxes, no new tasks, no deletions

### Step 2 — Collect and apply fixes

After all agents return:
- Apply cross-file fixes agents couldn't make
- Compile summary of everything fixed

### Step 3 — Code review gate

If fixes were made, spawn a **single Opus review agent** (`model: "opus"`, `subagent_type: "superpowers:code-reviewer"`) with a prompt covering: what was fixed, files to review, correctness checklist (no new mismatches, sequential IDs, checkboxes preserved), no scope creep (no invented/deleted tasks, no edits to read-only files), consistency checks.

Handle review results: fix Critical/Important immediately, note Minor, proceed if clean.

### Step 4 — Decide: loop or stop

- **Gaps found and fixed** → `/compact`, loop again
- **Zero gaps across all agents** → `<promise>NO GAPS REMAINING</promise>`

## Rules

- **DO NOT invent new tasks or features.**
- **DO NOT delete tasks.**
- **DO NOT modify read-only reference files.**
- **Preserve checkbox states** (`[x]`/`[ ]`).
- **Prefer phase doc's version** when fixing mismatches.
- **Fix ALL gaps per pass**, not just one.
- **Be specific** — exact strings, not vague summaries.
