# ChapterWise Unified Plugin — Master Plan

> **For Claude:** This is a Ralph Loop master plan. Read the Execution Rules below, then execute ALL unchecked tasks continuously.

## How to Start

Run this command to kick off Ralph Loop:

```
/ralph-loop:ralph-loop "Execute .claude/plans/recipe-system/ralph-loop/00-master-plan.md" --completion-promise "ALL CHAPTERWISE RECIPE SYSTEM TASKS COMPLETE" --max-iterations 55
```

**CRITICAL: The kickoff prompt MUST be a single short line referencing this file. Ralph reads all instructions from the file itself.**

---

## Execution Rules

**CRITICAL: Execute ALL tasks in one continuous run. NEVER stop between tasks.**

When Ralph reads this file, follow these rules:

1. **Execute ALL unchecked tasks in sequence** — start at the first `- [ ]` and do not stop until every task is `- [x]` or the completion promise is output.
2. **For each regular task:**
   - Read the phase file referenced for full details.
   - Execute the task (create files, write code, modify existing files).
   - Run the task-specific test/verify command.
   - If tests pass, commit and check off (`- [ ]` → `- [x]`).
   - **Immediately continue to the next unchecked task.**
3. **For CHECKPOINT tasks:**
   - Run the verification suite specified.
   - If tests FAIL: fix failures, re-run until pass, commit fixes.
   - Run code review via `superpowers:requesting-code-review`.
   - If review has findings: fix, re-test, re-review.
   - Only check off when BOTH tests AND review pass.
   - **Then immediately continue to the next task.**
4. **PARALLEL DISPATCH tasks** — When you see `[PARALLEL]`, dispatch all sub-tasks as parallel Task agents (each in a worktree). Wait for all to complete, then merge results and continue.
5. **NEVER STOP between tasks.** Fix issues inline and keep going.

---

## Overview

**Goal:** Merge all ChapterWise plugins into one unified `chapterwise` plugin (v2.0.0) with four recipe commands (import, analysis, atlas, reader) plus two cross-cutting commands (status, pipeline).

**Architecture:** Single Claude Code plugin with commands/ (skills), modules/ (analysis), patterns/ (import converters), scripts/ (utilities), templates/ (reader), schemas/ (validation). Each recipe saves state to `.chapterwise/{type}-recipe/` in the user's project.

**Working directory:** `/Users/phong/Projects/chapterwise-plugins/`

**Original Reference:** `.claude/plans/recipe-system/` (28 design docs + 7 build plans)

**Design docs the agents MUST read:**
- `LANGUAGE-GUIDE.md` — ALL agents must follow language rules
- `01-PLUGIN-STRUCTURE.md` — Canonical file layout
- `02-RECIPE-SYSTEM.md` — How recipes work
- Per-recipe design docs in their subdirectory

---

## Task Checklist

### Phase 1: Scaffold (`2026-02-27-phase-1-scaffold.md`)

- [x] **Task 1:** Create unified plugin directory structure
  - Test: `ls plugins/chapterwise/.claude-plugin/plugin.json && echo PASS`
  - Files: `plugins/chapterwise/.claude-plugin/plugin.json`, directories

- [x] **Task 2:** Copy existing commands from chapterwise-codex
  - Test: `ls plugins/chapterwise/commands/format.md plugins/chapterwise/commands/explode.md plugins/chapterwise/commands/lite.md && echo PASS`
  - Files: 13 `.md` files from `chapterwise-codex/commands/` → `chapterwise/commands/`

- [x] **Task 3:** Copy existing commands from chapterwise (insert.md)
  - Test: `ls plugins/chapterwise/commands/insert.md && echo PASS`
  - Files: `plugins/chapterwise/commands/insert.md`

- [x] **Task 4:** Copy analysis modules from chapterwise-analysis
  - Test: `ls plugins/chapterwise/modules/summary.md plugins/chapterwise/modules/characters.md plugins/chapterwise/modules/_output-format.md && echo PASS`
  - Files: 31+ `.md` files from `chapterwise-analysis/modules/` → `chapterwise/modules/`

- [x] **Task 5:** Copy scripts from chapterwise-codex and chapterwise-analysis
  - Test: `python3 -c "import json; print('PASS')" && ls plugins/chapterwise/scripts/module_loader.py plugins/chapterwise/scripts/staleness_checker.py plugins/chapterwise/scripts/analysis_writer.py plugins/chapterwise/scripts/word_count.py && echo PASS`
  - Files: All `.py` from both `scripts/` directories → `chapterwise/scripts/`

- [x] **Task 6:** Build recipe infrastructure scripts (`recipe_manager.py`, `codex_validator.py`, `recipe_validator.py`)
  - Test: `echo '{"project_path":"/tmp/test-recipe","type":"import"}' | python3 plugins/chapterwise/scripts/recipe_manager.py create >/dev/null && python3 -c "import ast; ast.parse(open('plugins/chapterwise/scripts/codex_validator.py').read()); ast.parse(open('plugins/chapterwise/scripts/recipe_validator.py').read()); print('PASS')"`
  - Files: `plugins/chapterwise/scripts/recipe_manager.py`, `plugins/chapterwise/scripts/codex_validator.py`, `plugins/chapterwise/scripts/recipe_validator.py`

- [x] **Task 7:** Build `scripts/format_detector.py`
  - Test: `echo '{"path":"README.md"}' | python3 plugins/chapterwise/scripts/format_detector.py | python3 -c "import sys,json; d=json.load(sys.stdin); print('PASS' if d['format']=='markdown' else 'FAIL')"`
  - Files: `plugins/chapterwise/scripts/format_detector.py`

- [x] **Task 8:** Create `schemas/recipe.schema.yaml`
  - Test: `python3 -c "import yaml; yaml.safe_load(open('plugins/chapterwise/schemas/recipe.schema.yaml')); print('PASS')"`
  - Files: `plugins/chapterwise/schemas/recipe.schema.yaml`

- [x] **Task 9:** Create empty template and pattern directories
  - Test: `ls -d plugins/chapterwise/templates/ plugins/chapterwise/patterns/common/ && echo PASS`
  - Files: directories + `__init__.py` markers

- [x] **Task 10:** Verify existing module_loader.py works from new location
  - Test: `cd plugins/chapterwise && CLAUDE_PLUGIN_ROOT=. python3 scripts/module_loader.py list 2>/dev/null | python3 -c "import sys,json; d=json.load(sys.stdin); print('PASS' if len(d)>0 else 'FAIL')"`
  - Files: May need path fixes in `module_loader.py`

- [x] **CHECKPOINT Phase 1:** Scaffold verification + code review
  - Test: `ls plugins/chapterwise/.claude-plugin/plugin.json plugins/chapterwise/commands/format.md plugins/chapterwise/modules/summary.md plugins/chapterwise/scripts/recipe_manager.py plugins/chapterwise/scripts/format_detector.py plugins/chapterwise/scripts/codex_validator.py plugins/chapterwise/scripts/recipe_validator.py plugins/chapterwise/schemas/recipe.schema.yaml && echo "ALL SCAFFOLD TESTS PASS"`
  - Review: Run `superpowers:requesting-code-review` for all Phase 1 files
  - **Gate:** Do NOT proceed to Phase 2 until tests pass AND review is clean

### Phase 2: Import Recipe — The First Real Deliverable (`2026-02-27-phase-2-import.md`)

- [x] **Task 11:** Build `patterns/common/chapter_detector.py`
  - Test: `echo '{"text":"Chapter 1: Hello World\nSome text.\nChapter 2: Goodbye\nMore text."}' | python3 plugins/chapterwise/patterns/common/chapter_detector.py | python3 -c "import sys,json; d=json.load(sys.stdin); print('PASS' if len(d.get('chapters',[]))>=2 else 'FAIL')"`
  - Files: `plugins/chapterwise/patterns/common/chapter_detector.py`

- [x] **Task 12:** Build `patterns/common/codex_writer.py`
  - Test: `echo '{"output_dir":"/tmp/test-codex","format":"markdown","chapters":[{"title":"Ch 1","content":"Hello","word_count":1}],"metadata":{"title":"Test"}}' | python3 plugins/chapterwise/patterns/common/codex_writer.py && ls /tmp/test-codex/index.codex.yaml && echo PASS`
  - Files: `plugins/chapterwise/patterns/common/codex_writer.py`

- [x] **Task 13:** Build `patterns/common/structure_analyzer.py`
  - Test: `echo '{"text":"Part I\nChapter 1\nText\nChapter 2\nText\nPart II\nChapter 3\nText"}' | python3 plugins/chapterwise/patterns/common/structure_analyzer.py | python3 -c "import sys,json; d=json.load(sys.stdin); print('PASS' if d.get('chapter_count',0)>=2 else 'FAIL')"`
  - Files: `plugins/chapterwise/patterns/common/structure_analyzer.py`

- [x] **Task 14:** Build `patterns/common/frontmatter_builder.py`
  - Test: `echo '{"title":"Chapter 1","word_count":3200,"tags":["adventure"]}' | python3 plugins/chapterwise/patterns/common/frontmatter_builder.py | grep -q "^---" && echo PASS`
  - Files: `plugins/chapterwise/patterns/common/frontmatter_builder.py`

- [x] **Task 15:** Build `patterns/plaintext_converter.py` (simplest converter)
  - Test: `echo "Chapter 1: Hello\nSome text here.\nChapter 2: World\nMore text." > /tmp/test-novel.txt && echo '{"source":"/tmp/test-novel.txt","output_dir":"/tmp/test-import/"}' | python3 plugins/chapterwise/patterns/plaintext_converter.py && ls /tmp/test-import/index.codex.yaml && echo PASS`
  - Files: `plugins/chapterwise/patterns/plaintext_converter.py`

- [x] **Task 16:** Write `commands/import.md` — the main import skill
  - Test: `grep -q "triggers:" plugins/chapterwise/commands/import.md && grep -q "allowed-tools:" plugins/chapterwise/commands/import.md && grep -q "codex_validator.py" plugins/chapterwise/commands/import.md && grep -q "recipe_validator.py" plugins/chapterwise/commands/import.md && ! grep -qi "order up\|bon appetit\|chef.s kiss" plugins/chapterwise/commands/import.md && echo PASS`
  - Files: `plugins/chapterwise/commands/import.md`
  - **READ FIRST:** `import-recipe/01-AGENT-WORKFLOW.md`, `03-INTERVIEW-AND-PREFERENCES.md`, `LANGUAGE-GUIDE.md`

- [x] **Task 17:** Write `commands/import-scrivener.md` (alias)
  - Test: `grep -q "triggers:" plugins/chapterwise/commands/import-scrivener.md && echo PASS`
  - Files: `plugins/chapterwise/commands/import-scrivener.md`

- [x] **Task 18:** Build `scripts/run_recipe.py`
  - Test: `python3 -c "import ast; ast.parse(open('plugins/chapterwise/scripts/run_recipe.py').read()); print('PASS')"`
  - Files: `plugins/chapterwise/scripts/run_recipe.py`

- [x] **CHECKPOINT Phase 2:** Import recipe verification + code review
  - Test: `echo "Chapter 1: The Start\nFirst chapter text.\n\nChapter 2: The Middle\nSecond chapter text.\n\nChapter 3: The End\nThird chapter text." > /tmp/test-full-import.txt && echo '{"source":"/tmp/test-full-import.txt","output_dir":"/tmp/test-full-output/"}' | python3 plugins/chapterwise/patterns/plaintext_converter.py && ls /tmp/test-full-output/index.codex.yaml && python3 -c "import yaml; d=yaml.safe_load(open('/tmp/test-full-output/index.codex.yaml')); print('PASS' if 'children' in d else 'FAIL')"`
  - Review: Run `superpowers:requesting-code-review` for all Phase 2 files
  - **Gate:** Do NOT proceed to Phase 3 until tests pass AND review is clean

### Phase 3: Parallel Recipe Build [PARALLEL] (`2026-02-27-phase-3-parallel.md`)

**Dispatch these 3 agents simultaneously. Each works in a worktree.**

- [x] **Task 19 [PARALLEL-A]:** Analysis Recipe — Write `commands/analysis.md`
  - Agent: Task(subagent_type="general-purpose", isolation="worktree")
  - Test: `grep -q "triggers:" plugins/chapterwise/commands/analysis.md && grep -q "courses" plugins/chapterwise/commands/analysis.md && echo PASS`
  - Files: `plugins/chapterwise/commands/analysis.md`
  - **READ:** `analysis-recipe/00-OVERVIEW.md`, `01-ANALYSIS-RECIPE.md`, `LANGUAGE-GUIDE.md`, `build-plans/AGENT-2-ANALYSIS.md`

- [x] **Task 20 [PARALLEL-A]:** Analysis — Update `scripts/module_loader.py` with courses + recommend
  - Test: `cd plugins/chapterwise && echo '{}' | CLAUDE_PLUGIN_ROOT=. python3 scripts/module_loader.py courses 2>/dev/null | python3 -c "import sys,json; d=json.load(sys.stdin); print('PASS' if 'courses' in d else 'FAIL')"`
  - Files: `plugins/chapterwise/scripts/module_loader.py`

- [x] **Task 21 [PARALLEL-B]:** Atlas Recipe — Write `commands/atlas.md`
  - Agent: Task(subagent_type="general-purpose", isolation="worktree")
  - Test: `grep -q "triggers:" plugins/chapterwise/commands/atlas.md && grep -q "\-\-update" plugins/chapterwise/commands/atlas.md && grep -q "Pass 0\|Pass 1\|Pass 2\|Pass 3" plugins/chapterwise/commands/atlas.md && echo PASS`
  - Files: `plugins/chapterwise/commands/atlas.md`
  - **READ:** `atlas-recipe/00-OVERVIEW.md`, `01-ATLAS-RECIPE.md`, `02-UPDATE-ATLAS.md`, `03-ATLAS-SECTIONS.md`, `LANGUAGE-GUIDE.md`, `build-plans/AGENT-3-ATLAS.md`

- [x] **Task 22 [PARALLEL-C]:** Reader Recipe — Write `commands/reader.md`
  - Agent: Task(subagent_type="general-purpose", isolation="worktree")
  - Test: `grep -q "triggers:" plugins/chapterwise/commands/reader.md && grep -q "atlas" plugins/chapterwise/commands/reader.md && echo PASS`
  - Files: `plugins/chapterwise/commands/reader.md`
  - **READ:** `reader-recipe/00-OVERVIEW.md`, `01-READER-RECIPE.md`, `02-READER-ARCHITECTURE.md`, `LANGUAGE-GUIDE.md`, `build-plans/AGENT-4-READER.md`

- [x] **Task 23 [PARALLEL-C]:** Reader — Build `templates/minimal-reader/`
  - Test: `ls plugins/chapterwise/templates/minimal-reader/index.html plugins/chapterwise/templates/minimal-reader/style.css plugins/chapterwise/templates/minimal-reader/reader.js && echo PASS`
  - Files: `templates/minimal-reader/index.html`, `style.css`, `reader.js`

- [x] **Task 24 [PARALLEL-C]:** Reader — Build `templates/academic-reader/`
  - Test: `ls plugins/chapterwise/templates/academic-reader/index.html plugins/chapterwise/templates/academic-reader/style.css plugins/chapterwise/templates/academic-reader/reader.js && echo PASS`
  - Files: `templates/academic-reader/index.html`, `style.css`, `reader.js`

- [x] **CHECKPOINT Phase 3:** Merge worktrees + verify all recipe commands exist
  - Test: `ls plugins/chapterwise/commands/analysis.md plugins/chapterwise/commands/atlas.md plugins/chapterwise/commands/reader.md plugins/chapterwise/templates/minimal-reader/index.html && echo "ALL RECIPE COMMANDS EXIST"`
  - Review: Run `superpowers:requesting-code-review` for all Phase 3 files
  - **Gate:** Do NOT proceed to Phase 4 until all worktrees merged AND review clean

### Phase 4: Remaining Import Patterns (`2026-02-27-phase-4-patterns.md`)

- [x] **Task 25:** Build `patterns/pdf_converter.py`
  - Test: `python3 -c "import ast; ast.parse(open('plugins/chapterwise/patterns/pdf_converter.py').read()); print('PASS')"`
  - Files: `plugins/chapterwise/patterns/pdf_converter.py`

- [x] **Task 26:** Build `patterns/docx_converter.py`
  - Test: `python3 -c "import ast; ast.parse(open('plugins/chapterwise/patterns/docx_converter.py').read()); print('PASS')"`
  - Files: `plugins/chapterwise/patterns/docx_converter.py`

- [x] **Task 27:** Build `patterns/scrivener_converter.py` (adapt from existing)
  - Test: `python3 -c "import ast; ast.parse(open('plugins/chapterwise/patterns/scrivener_converter.py').read()); print('PASS')"`
  - Files: `plugins/chapterwise/patterns/scrivener_converter.py`

- [x] **Task 28:** Build `patterns/ulysses_converter.py`
  - Test: `python3 -c "import ast; ast.parse(open('plugins/chapterwise/patterns/ulysses_converter.py').read()); print('PASS')"`
  - Files: `plugins/chapterwise/patterns/ulysses_converter.py`

- [x] **Task 29:** Build `patterns/markdown_folder.py`
  - Test: `python3 -c "import ast; ast.parse(open('plugins/chapterwise/patterns/markdown_folder.py').read()); print('PASS')"`
  - Files: `plugins/chapterwise/patterns/markdown_folder.py`

- [x] **Task 30:** Build `patterns/html_converter.py`
  - Test: `python3 -c "import ast; ast.parse(open('plugins/chapterwise/patterns/html_converter.py').read()); print('PASS')"`
  - Files: `plugins/chapterwise/patterns/html_converter.py`

- [x] **CHECKPOINT Phase 4:** All patterns compile + code review
  - Test: `for f in plugins/chapterwise/patterns/*.py; do python3 -c "import ast; ast.parse(open('$f').read())" || echo "FAIL: $f"; done && echo "ALL PATTERNS VALID"`
  - Review: Run `superpowers:requesting-code-review` for all Phase 4 files
  - **Gate:** Do NOT proceed to Phase 5 until tests pass AND review clean

### Phase 5: Cross-Cutting Commands (`2026-02-27-phase-5-cross-cutting.md`)

- [x] **Task 31:** Write `commands/status.md`
  - Test: `grep -q "triggers:" plugins/chapterwise/commands/status.md && grep -q "recipe_manager" plugins/chapterwise/commands/status.md && echo PASS`
  - Files: `plugins/chapterwise/commands/status.md`
  - **READ:** `LANGUAGE-GUIDE.md` (Status Command section), `00-OVERVIEW.md`

- [x] **Task 32:** Write `commands/pipeline.md`
  - Test: `grep -q "triggers:" plugins/chapterwise/commands/pipeline.md && grep -q "Step 1\|Step 2\|Step 3\|Step 4" plugins/chapterwise/commands/pipeline.md && echo PASS`
  - Files: `plugins/chapterwise/commands/pipeline.md`
  - **READ:** `LANGUAGE-GUIDE.md` (Pipeline Command section), `00-OVERVIEW.md`

- [x] **CHECKPOINT Phase 5:** Cross-cutting commands + code review
  - Test: `ls plugins/chapterwise/commands/status.md plugins/chapterwise/commands/pipeline.md && echo PASS`
  - Review: Run `superpowers:requesting-code-review` for Phase 5 files
  - **Gate:** Do NOT proceed to Phase 6 until tests pass AND review clean

### Phase 6: Migration + Stubs (`2026-02-27-phase-6-migration.md`)

- [x] **Task 33:** Create deprecation stubs for `chapterwise-codex`
  - Test: `grep -q "deprecated" plugins/chapterwise-codex/.claude-plugin/plugin.json && grep -q "chapterwise-codex:format" plugins/chapterwise-codex/commands/format.md && ! grep -q "^  - format$" plugins/chapterwise-codex/commands/format.md && grep -q "moved" plugins/chapterwise-codex/commands/format.md && echo PASS`
  - Files: `chapterwise-codex/.claude-plugin/plugin.json`, all `commands/*.md`

- [x] **Task 34:** Create deprecation stub for `chapterwise-analysis`
  - Test: `grep -q "deprecated" plugins/chapterwise-analysis/.claude-plugin/plugin.json && grep -q "chapterwise-analysis:analysis" plugins/chapterwise-analysis/commands/analysis.md && ! grep -q "^  - analysis$" plugins/chapterwise-analysis/commands/analysis.md && grep -q "moved" plugins/chapterwise-analysis/commands/analysis.md && echo PASS`
  - Files: `chapterwise-analysis/.claude-plugin/plugin.json`, `commands/analysis.md`

- [x] **Task 35:** Remove old `chapterwise/commands/import.md` (replaced by recipe version)
  - Test: `grep -q "recipe\|Recipe\|pattern\|Pattern\|Scan\|scan" plugins/chapterwise/commands/import.md && echo PASS`
  - Files: Verify `commands/import.md` is the NEW recipe version, not the old folder wizard

- [x] **CHECKPOINT Phase 6:** Migration stubs + old commands redirected
  - Test: `grep -q "deprecated" plugins/chapterwise-codex/.claude-plugin/plugin.json && grep -q "deprecated" plugins/chapterwise-analysis/.claude-plugin/plugin.json && echo "MIGRATION COMPLETE"`
  - Review: Run `superpowers:requesting-code-review` for Phase 6 files
  - **Gate:** Do NOT proceed to Phase 7 until review clean

### Phase 7: Final Verification (`2026-02-27-phase-7-verification.md`)

- [x] **Task 36:** Language Guide compliance scan — all commands
  - Test: `! (grep -rli "order up\|bon appetit\|chef.s kiss\|ready to serve" plugins/chapterwise/commands/ 2>/dev/null | grep -q .) && ! (grep -rni '\brecipe\b' plugins/chapterwise/commands/*.md | grep -vi "recipe_manager\|recipe.yaml\|recipe.schema\|import-recipe\|analysis-recipe\|atlas-recipe\|reader-recipe\|recipe_path\|recipe_dir" | grep -q .) && echo "NO LEAKS"`
  - Files: All `commands/*.md`

- [x] **Task 37:** Trigger deduplication check
  - Test: `DUPES=$(grep -h "^  - " plugins/chapterwise/commands/*.md 2>/dev/null | sort | uniq -d | wc -l | tr -d ' '); COLLISIONS=$(comm -12 <(grep -h "^  - " plugins/chapterwise-codex/commands/*.md plugins/chapterwise-analysis/commands/*.md 2>/dev/null | sort) <(grep -h "^  - " plugins/chapterwise/commands/*.md 2>/dev/null | sort) | wc -l | tr -d ' '); [ "$DUPES" = "0" ] && [ "$COLLISIONS" = "0" ] && echo "NO DUPLICATE OR COLLIDING TRIGGERS" || echo "TRIGGER ISSUES FOUND"`
  - Files: All `commands/*.md`

- [x] **Task 38:** Full file inventory — verify all expected files exist
  - Test: `ls plugins/chapterwise/.claude-plugin/plugin.json plugins/chapterwise/commands/import.md plugins/chapterwise/commands/analysis.md plugins/chapterwise/commands/atlas.md plugins/chapterwise/commands/reader.md plugins/chapterwise/commands/status.md plugins/chapterwise/commands/pipeline.md plugins/chapterwise/commands/format.md plugins/chapterwise/commands/insert.md plugins/chapterwise/modules/summary.md plugins/chapterwise/scripts/recipe_manager.py plugins/chapterwise/scripts/format_detector.py plugins/chapterwise/scripts/run_recipe.py plugins/chapterwise/scripts/codex_validator.py plugins/chapterwise/scripts/recipe_validator.py plugins/chapterwise/patterns/plaintext_converter.py plugins/chapterwise/patterns/common/chapter_detector.py plugins/chapterwise/templates/minimal-reader/index.html plugins/chapterwise/schemas/recipe.schema.yaml && echo "ALL FILES PRESENT"`
  - Files: Full inventory

- [ ] **FINAL CHECKPOINT:** Full verification + final code review
  - Test: Run all Phase 1-7 test commands sequentially
  - Review: Run `superpowers:requesting-code-review` for ALL changed files across all phases
  - **Gate:** ALL tests must pass AND review must be 100% clean

- [ ] **Task 39:** Output completion promise
  - When ALL tasks AND ALL checkpoints pass: `<promise>ALL CHAPTERWISE RECIPE SYSTEM TASKS COMPLETE</promise>`

---

## Execution Notes

- **Working directory:** `/Users/phong/Projects/chapterwise-plugins/`
- **Branch:** Stay on current branch — NEVER switch branches
- **Commit after each phase** (not each task) with descriptive messages
- **Phase 3 is PARALLEL** — dispatch 3 worktree agents simultaneously
  - Agent A: Analysis (Tasks 19-20)
  - Agent B: Atlas (Task 21)
  - Agent C: Reader (Tasks 22-24)
- **Design docs location:** `.claude/plans/recipe-system/` — agents MUST read relevant docs before writing
- **Language rules:** EVERY command file must follow `LANGUAGE-GUIDE.md`
- **Script interface:** All Python scripts use stdin JSON → stdout JSON convention
- **Self-validation requirement:** Each recipe command must include a validate/heal step and call the appropriate validators before reporting success
- **Phase dependencies:**
  - Phase 2 depends on Phase 1 (scaffold must exist)
  - Phase 3 depends on Phase 2 (import must work, shared scripts tested)
  - Phase 4 depends on Phase 2 (pattern convention established by plaintext_converter)
  - Phase 5 depends on Phase 3 (needs all recipe commands to exist for status/pipeline)
  - Phase 6 depends on Phase 1 (old plugins must still exist to stub)
  - Phase 7 depends on ALL previous phases
