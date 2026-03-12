# Phase 2-4: Integration, Migration, Final QA

**Agent:** Managing Agent (runs after all 4 recipe agents complete)

---

## Phase 2: Integration Testing

### Step 1: Merge all worktrees

Each recipe agent worked in a worktree. Merge them into the unified plugin:

```
Agent 1 (Import)   → commands/import.md, patterns/*, etc.
Agent 2 (Analysis) → commands/analysis.md, scripts updates
Agent 3 (Atlas)    → commands/atlas.md
Agent 4 (Reader)   → commands/reader.md, templates/*
```

Resolve any conflicts (unlikely — each agent touches different files).

### Step 2: Cross-recipe flow test

Run the full chain end-to-end:

```
1. Create a test manuscript (5 chapters, ~5000 words total)
2. /import test-manuscript.txt
   → Verify: codex project created, recipe saved
3. /analysis --plan
   → Verify: genre detected, modules recommended
4. /analysis
   → Verify: results in .analysis.json, recipe saved
5. /atlas
   → Verify: atlas created, registered in index, recipe saved
6. /atlas --update
   → Modify a chapter, run update, verify incremental
7. /reader
   → Verify: HTML reader builds, opens in browser
8. /reader (on atlas project)
   → Verify: atlas-specific components render
```

### Step 3: Recipe discovery test

```bash
echo '{"project_path": "./test-project"}' | python3 scripts/recipe_manager.py list
```

Verify output includes all four recipe types with correct metadata.

### Step 4: Script interface compatibility

Verify all commands call scripts with consistent JSON-in/JSON-out protocol:
- `format_detector.py` — called by import
- `recipe_manager.py` — called by all four commands
- `module_loader.py` — called by analysis and atlas
- `staleness_checker.py` — called by analysis and atlas
- `analysis_writer.py` — called by analysis

### Step 5: Language Guide compliance

```bash
# Check for "recipe" leaking to user-facing messages
grep -r "recipe" commands/*.md | grep -v "^#" | grep -v "recipe_manager" | grep -v "recipe.yaml"

# Check for theatrical lines
grep -rEi "order up|bon appetit|chef.s kiss|ready to serve" commands/*.md

# Check for cooking verbs without data nouns
grep -rE "\"(Cutting|Seasoning|Cooking|Simmering|Extracting|Synthesizing)\.\.\." commands/*.md
```

### Step 6: Trigger deduplication

Verify no two commands share the same trigger. The merged plugin has many commands — check:
```bash
grep -h "^  - " commands/*.md | sort | uniq -d
```

Any duplicates must be resolved (usually by removing the less-specific one).

### Step 7: Self-validation pipeline test

Verify the validation pipeline works end-to-end:

```bash
# 1. Run codex_validator on import output
echo '{"path": "./test-project/", "fix": false}' | python3 scripts/codex_validator.py
# → Should return {"valid": true, ...}

# 2. Run recipe_validator on each recipe
for TYPE in import-recipe analysis-recipe atlas-recipe reader-recipe; do
  echo "{\"recipe_path\": \"./test-project/.chapterwise/$TYPE/\"}" | python3 scripts/recipe_validator.py
done
# → All should return {"valid": true, ...}

# 3. Deliberately corrupt and verify self-healing
# Remove a word_count from a chapter file, run validator with fix=true
echo '{"path": "./test-project/", "fix": true}' | python3 scripts/codex_validator.py
# → Should report fix_applied for the missing word_count

# 4. Cross-recipe consistency
# Verify chapter counts match between import, analysis, and atlas recipes
```

### Step 8: Post-execution hook test

Verify that each command's validation step runs automatically after execution:

1. Run `/import test.txt` → verify `codex_validator.py` was called (check for validation messages in output)
2. Run `/analysis summary test.md` → verify `.analysis.json` has valid `sourceHash`
3. Run `/atlas` → verify atlas files pass codex validation
4. Run `/reader` → verify HTML output has no broken links

The validation should be **invisible when everything passes** and **brief when it fixes things**. Never verbose unless there are unfixable problems.

---

## Phase 3: Migration

### Step 1: Create stub files for old plugins

#### `chapterwise-codex/.claude-plugin/plugin.json`
```json
{
  "name": "chapterwise-codex",
  "description": "DEPRECATED — All commands have moved to the 'chapterwise' plugin. Please switch to 'chapterwise' for the latest features.",
  "version": "2.0.0",
  "deprecated": true
}
```

#### `chapterwise-codex/commands/format.md` (and all other commands)
```markdown
---
description: "This command has moved to the chapterwise plugin"
triggers:
  - chapterwise-codex:format
---

This command has moved to the `chapterwise` plugin. Use `/format` instead.
```

Create this stub for every command in `chapterwise-codex/commands/`.

#### `chapterwise-analysis/.claude-plugin/plugin.json`
```json
{
  "name": "chapterwise-analysis",
  "description": "DEPRECATED — All commands have moved to the 'chapterwise' plugin. Please switch to 'chapterwise' for the latest features.",
  "version": "2.0.0",
  "deprecated": true
}
```

#### `chapterwise-analysis/commands/analysis.md`
```markdown
---
description: "This command has moved to the chapterwise plugin"
triggers:
  - chapterwise-analysis:analysis
---

This command has moved to the `chapterwise` plugin. Use `/analysis` instead.
```

### Step 2: Keep old plugins in repo

Don't delete old plugin directories — they may be referenced by users who haven't updated. The stubs redirect gracefully.

### Step 3: Update old `chapterwise/commands/import.md`

The original `chapterwise/commands/import.md` (the old simple folder import) is now superseded by the recipe-based import. Since we're merging into this plugin, the new `import.md` from Agent 1 replaces it directly.

---

## Phase 4: Final QA

### Step 1: Full end-to-end test with real content

Use a real manuscript (or realistic test content with multiple chapters, characters, and themes):

1. Import from PDF
2. Run full analysis
3. Build atlas
4. Update atlas after manuscript change
5. Build reader for both manuscript and atlas
6. Verify all recipes saved and discoverable

### Step 2: Existing command regression

Verify ALL existing commands still work:

| Command | Test |
|---------|------|
| `/format file.codex.yaml` | Formats a codex file |
| `/format-folder ./project` | Batch formats |
| `/explode file.codex.yaml` | Splits into files |
| `/implode ./folder` | Merges files |
| `/convert-to-codex file.md` | Markdown → codex |
| `/convert-to-markdown file.codex.yaml` | Codex → markdown |
| `/lite` | Creates codex lite file |
| `/generate-tags file.codex.yaml` | Auto-tags |
| `/update-word-count file.codex.yaml` | Updates word count |
| `/insert` | Inserts content |
| `/diagram` | Creates diagrams |
| `/spreadsheet` | Creates spreadsheet |

### Step 3: Full validation sweep

Run validators across the entire test project to verify everything is clean:

```bash
# Validate all codex files
echo '{"path": "./test-project/", "fix": false}' | python3 scripts/codex_validator.py

# Validate all recipes
echo '{"project_path": "./test-project/"}' | python3 scripts/recipe_manager.py list | \
  python3 -c "import json,sys; recipes=json.load(sys.stdin); print(f'{len(recipes)} recipes found')"

# Cross-recipe consistency check
echo '{"recipe_path": "./test-project/.chapterwise/import-recipe/"}' | python3 scripts/recipe_validator.py
echo '{"recipe_path": "./test-project/.chapterwise/analysis-recipe/"}' | python3 scripts/recipe_validator.py
echo '{"recipe_path": "./test-project/.chapterwise/atlas-recipe/"}' | python3 scripts/recipe_validator.py
```

All validators must return `{"valid": true}`. Any failures block the release.

### Step 4: Clean up

- Remove any temporary/test files
- Verify no duplicate files between old and new plugin directories
- Update `plugin.json` version if needed
- Final commit

### Step 4: Commit and tag

```
feat: ChapterWise Plugin v2.0.0 — unified plugin with recipe system

Merged chapterwise, chapterwise-codex, and chapterwise-analysis into one plugin.
Added four recipe commands: import, analysis (enhanced), atlas, reader.

New features:
- /import: Import any manuscript (PDF, DOCX, Scrivener, Ulysses, etc.)
- /atlas: Build comprehensive story atlas (characters, timeline, themes)
- /atlas --update: Incremental atlas updates
- /reader: Build custom HTML reading experience
- /analysis: Enhanced with courses, genre-aware selection, recipes
- All recipes save to .chapterwise/ for fast re-runs

All existing commands preserved and working.
```

Tag: `v2.0.0`

---

## Success Criteria

The recipe system is DONE when:

1. A writer can install ONE plugin and get everything
2. `/import novel.pdf` creates a full codex project with recipe saved
3. `/analysis` intelligently selects modules based on genre
4. `/atlas` builds a multi-section reference atlas
5. `/atlas --update` incrementally updates after manuscript changes
6. `/reader` builds a browsable HTML reader
7. All existing commands (`/format`, `/explode`, `/analysis summary`, etc.) still work
8. All recipes save to `.chapterwise/` and are reusable
9. Progress messaging follows the Language Guide
10. No "recipe" leaked to user-facing text
11. All recipe outputs pass `codex_validator.py` with zero issues
12. All recipe.yaml files pass `recipe_validator.py` with zero issues
13. Cross-recipe consistency verified (chapter counts, hashes match)
14. Self-healing demonstrated: deliberately corrupted output is auto-repaired
