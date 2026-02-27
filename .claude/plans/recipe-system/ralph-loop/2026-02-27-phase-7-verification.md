# Phase 7: Final Verification — Tasks 36-39

> **Reference:** `build-plans/PHASE-2-4-INTEGRATION.md` (Phase 4: Final QA), `LANGUAGE-GUIDE.md`

Final quality assurance pass across the entire unified plugin. No new code — just validation, cleanup, and the completion promise.

---

## Task 36: Language Guide compliance scan — all commands

**Files:**
- Scan: All `plugins/chapterwise/commands/*.md`

### Step 36.1: Check for banned phrases

No theatrical cooking language in any command file:

```bash
# Check for banned phrases across all commands
BANNED=$(grep -rli "order up\|bon appetit\|chef.s kiss\|ready to serve\|kitchen\|plating\|garnish" plugins/chapterwise/commands/ 2>/dev/null)
if [ -n "$BANNED" ]; then
  echo "FAIL — banned phrases in: $BANNED"
else
  echo "PASS — no banned phrases"
fi
```

### Step 36.2: Check that "recipe" doesn't leak to user-facing text

The word "recipe" should only appear in script references (recipe_manager.py, recipe.yaml, etc.), never as user-facing language:

```bash
# Find "recipe" in commands that isn't a file/script reference
grep -rn '"recipe"' plugins/chapterwise/commands/*.md | grep -v "recipe_manager\|recipe.yaml\|recipe.schema\|import-recipe\|analysis-recipe\|atlas-recipe\|reader-recipe\|recipe_path\|recipe_dir" | head -10
# If output is empty: PASS
# If output has lines: those need fixing
```

### Step 36.3: Fix any violations found

If violations are found in Steps 36.1 or 36.2, fix them inline and re-run the checks.

### Step 36.4: Verify

```bash
! (grep -rli "order up\|bon appetit\|chef.s kiss\|ready to serve" plugins/chapterwise/commands/ 2>/dev/null | grep -q .) && \
! (grep -rni '\brecipe\b' plugins/chapterwise/commands/*.md | grep -vi "recipe_manager\|recipe.yaml\|recipe.schema\|import-recipe\|analysis-recipe\|atlas-recipe\|reader-recipe\|recipe_path\|recipe_dir" | grep -q .) && \
echo PASS
```

---

## Task 37: Trigger deduplication check

**Files:**
- Scan: All `plugins/chapterwise/commands/*.md`

### Step 37.1: Extract all triggers and check for duplicates

```bash
# Extract all trigger lines from all command files
grep -h "^  - " plugins/chapterwise/commands/*.md | sort | uniq -d
```

If any duplicates are found, they need to be resolved — each trigger should route to exactly one command.

### Step 37.2: Common duplicates to watch for

- `import` — should only be in `import.md`
- `analysis` — should only be in `analysis.md` (not in the deprecated chapterwise-analysis stub)
- `atlas` — should only be in `atlas.md`
- `reader` — should only be in `reader.md`
- `format` — could conflict between `format.md` (codex formatting) and import format detection

### Step 37.3: Fix duplicates

If found, disambiguate by:
1. Making triggers more specific (e.g., "format codex" vs "detect format")
2. Removing redundant triggers from alias commands

### Step 37.4: Verify

```bash
DUPES=$(grep -h "^  - " plugins/chapterwise/commands/*.md 2>/dev/null | sort | uniq -d | wc -l | tr -d ' ')
if [ "$DUPES" = "0" ]; then
  echo "PASS — no duplicate triggers"
else
  echo "FAIL — $DUPES duplicate triggers found"
fi

# Also verify no trigger collisions with deprecated stubs
STUB_TRIGGERS=$(grep -h "^  - " plugins/chapterwise-codex/commands/*.md plugins/chapterwise-analysis/commands/*.md 2>/dev/null | sort)
UNIFIED_TRIGGERS=$(grep -h "^  - " plugins/chapterwise/commands/*.md 2>/dev/null | sort)
COLLISIONS=$(comm -12 <(echo "$STUB_TRIGGERS") <(echo "$UNIFIED_TRIGGERS"))
if [ -n "$COLLISIONS" ]; then
  echo "FAIL — trigger collisions between stubs and unified plugin: $COLLISIONS"
else
  echo "PASS — no trigger collisions"
fi
```

---

## Task 38: Full file inventory — verify all expected files exist

**Files:**
- Scan: Entire `plugins/chapterwise/` directory

### Step 38.1: Check core infrastructure

```bash
ls plugins/chapterwise/.claude-plugin/plugin.json && echo "plugin.json: OK"
```

### Step 38.2: Check all recipe commands

```bash
for cmd in import import-scrivener analysis atlas reader status pipeline; do
  if [ -f "plugins/chapterwise/commands/$cmd.md" ]; then
    echo "$cmd.md: OK"
  else
    echo "$cmd.md: MISSING"
  fi
done
```

### Step 38.3: Check existing commands (carried over)

```bash
for cmd in format explode implode convert-to-codex convert-to-markdown lite generate-tags update-word-count diagram spreadsheet insert format-folder format-regen-ids; do
  if [ -f "plugins/chapterwise/commands/$cmd.md" ]; then
    echo "$cmd.md: OK"
  else
    echo "$cmd.md: MISSING (may be optional)"
  fi
done
```

### Step 38.4: Check scripts

```bash
for script in recipe_manager format_detector run_recipe codex_validator recipe_validator module_loader staleness_checker analysis_writer word_count; do
  if [ -f "plugins/chapterwise/scripts/${script}.py" ]; then
    echo "${script}.py: OK"
  else
    echo "${script}.py: MISSING"
  fi
done
```

### Step 38.5: Check patterns

```bash
for pattern in plaintext_converter pdf_converter docx_converter scrivener_converter ulysses_converter markdown_folder html_converter; do
  if [ -f "plugins/chapterwise/patterns/${pattern}.py" ]; then
    echo "${pattern}.py: OK"
  else
    echo "${pattern}.py: MISSING"
  fi
done

# Common utilities
for util in chapter_detector codex_writer structure_analyzer frontmatter_builder; do
  if [ -f "plugins/chapterwise/patterns/common/${util}.py" ]; then
    echo "common/${util}.py: OK"
  else
    echo "common/${util}.py: MISSING"
  fi
done
```

### Step 38.5b: Behavioral validation — script interfaces

Verify all scripts accept stdin JSON and return valid JSON:

```bash
# Test recipe_manager.py
echo '{"project_path":"/tmp/test-bv"}' | python3 plugins/chapterwise/scripts/recipe_manager.py list | python3 -c "import json,sys; json.load(sys.stdin); print('recipe_manager: PASS')"

# Test format_detector.py
echo '{"path":"/tmp/nonexistent.txt"}' | python3 plugins/chapterwise/scripts/format_detector.py | python3 -c "import json,sys; d=json.load(sys.stdin); assert 'format' in d; print('format_detector: PASS')"

# Test codex_validator.py
echo '{"path":"/tmp/test-bv/","fix":false}' | python3 plugins/chapterwise/scripts/codex_validator.py | python3 -c "import json,sys; d=json.load(sys.stdin); assert 'valid' in d; print('codex_validator: PASS')"

# Test recipe_validator.py
echo '{"recipe_path":"/tmp/test-bv/.chapterwise/import-recipe/"}' | python3 plugins/chapterwise/scripts/recipe_validator.py | python3 -c "import json,sys; d=json.load(sys.stdin); assert 'valid' in d; print('recipe_validator: PASS')"

# Test run_recipe.py syntax (interface contract file exists and is parseable)
python3 -c "import ast; ast.parse(open('plugins/chapterwise/scripts/run_recipe.py').read()); print('run_recipe: PASS')"
```

### Step 38.6: Check templates

```bash
for template in minimal-reader academic-reader; do
  if [ -f "plugins/chapterwise/templates/${template}/index.html" ]; then
    echo "${template}/: OK"
  else
    echo "${template}/: MISSING"
  fi
done
```

### Step 38.7: Check schemas

```bash
ls plugins/chapterwise/schemas/recipe.schema.yaml && echo "recipe.schema.yaml: OK"
```

### Step 38.8: Check modules

```bash
MODULE_COUNT=$(ls plugins/chapterwise/modules/*.md 2>/dev/null | wc -l | tr -d ' ')
echo "Modules: $MODULE_COUNT files"
if [ "$MODULE_COUNT" -ge 20 ]; then
  echo "PASS — sufficient modules"
else
  echo "FAIL — expected 20+ modules, found $MODULE_COUNT"
fi
```

### Step 38.9: Combined verification

```bash
ls plugins/chapterwise/.claude-plugin/plugin.json \
   plugins/chapterwise/commands/import.md \
   plugins/chapterwise/commands/analysis.md \
   plugins/chapterwise/commands/atlas.md \
   plugins/chapterwise/commands/reader.md \
   plugins/chapterwise/commands/status.md \
   plugins/chapterwise/commands/pipeline.md \
   plugins/chapterwise/commands/format.md \
   plugins/chapterwise/commands/insert.md \
   plugins/chapterwise/modules/summary.md \
   plugins/chapterwise/scripts/recipe_manager.py \
   plugins/chapterwise/scripts/format_detector.py \
   plugins/chapterwise/patterns/plaintext_converter.py \
   plugins/chapterwise/patterns/common/chapter_detector.py \
   plugins/chapterwise/templates/minimal-reader/index.html \
   plugins/chapterwise/schemas/recipe.schema.yaml \
   && echo "ALL FILES PRESENT"
```

---

## Task 39: Output completion promise

### Step 39.1: Final summary

List what was built:
- 1 unified plugin (chapterwise v2.0.0)
- 6 recipe + cross-cutting commands (import, analysis, atlas, reader, status, pipeline)
- 13+ carried-over commands (format, explode, implode, etc.)
- 31+ analysis modules
- 7 import pattern converters + 4 common utilities
- 2 reader templates (minimal, academic)
- 5 shared recipe scripts (recipe_manager, format_detector, run_recipe, codex_validator, recipe_validator)
- 1 schema (recipe.schema.yaml)
- 2 deprecated plugin stubs

### Step 39.2: Output promise

When ALL tasks AND ALL checkpoints pass:

```
<promise>ALL CHAPTERWISE RECIPE SYSTEM TASKS COMPLETE</promise>
```

---

## Final Commit

```bash
cd /Users/phong/Projects/chapterwise-plugins
git add -A
git commit -m "feat: ChapterWise unified plugin v2.0.0 — complete recipe system

Four recipe commands: /import, /analysis, /atlas, /reader
Two cross-cutting: /status, /pipeline
13 carried-over codex commands
31 analysis modules
7 format converters + 4 common pattern utilities
2 reader templates (minimal, academic)
Recipe system: .chapterwise/ folders with YAML manifests

Old plugins (chapterwise-codex, chapterwise-analysis) deprecated with stubs."

git tag -a v2.0.0 -m "ChapterWise unified plugin — recipe system"
```
