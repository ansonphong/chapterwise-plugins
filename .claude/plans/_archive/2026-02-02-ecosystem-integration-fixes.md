# ChapterWise Ecosystem Integration Fixes Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Fix all critical integration issues between chapterwise-app, chapterwise-codex (VS Code), and chapterwise-claude-plugins to ensure seamless cross-repository compatibility.

**Architecture:** Each repository has its own fixes but they must align on: (1) Codex V1.2 format version support, (2) field naming conventions (targetId, snake_case module IDs), (3) attribute array access patterns, and (4) schema validation. Fixes are ordered by dependency - plugins first, then app, then VS Code extension.

**Tech Stack:** Python 3.8+ (app, plugins), TypeScript 5.4 (VS Code), JSON Schema draft-2020-12, pytest, jsonschema library

---

## Repository Paths

- **chapterwise-app:** `/Users/phong/Projects/chapterwise-app`
- **chapterwise-codex:** `/Users/phong/Projects/chapterwise-codex`
- **chapterwise-claude-plugins:** `/Users/phong/Projects/chapterwise-claude-plugins`

---

## Task 1: Fix App Field Access for sourceHash (CRITICAL)

**Files:**
- Modify: `/Users/phong/Projects/chapterwise-app/app/services/analysis_file_service.py:300-330`
- Test: `/Users/phong/Projects/chapterwise-app/tests/test_analysis_file_service.py`

**Step 1: Create helper function to extract attribute value**

Add this function near the top of the file (after imports, around line 30):

```python
def _get_attribute_value(node: Dict[str, Any], key: str) -> Optional[str]:
    """Extract value from node's attributes array by key.

    Attributes are stored as: [{"key": "sourceHash", "value": "abc123"}, ...]
    """
    for attr in node.get('attributes', []):
        if attr.get('key') == key:
            return attr.get('value')
    return None
```

**Step 2: Fix is_analysis_stale function**

Find the `is_analysis_stale` function (around line 300) and update to use the helper:

```python
def is_analysis_stale(source_path: str, module_name: str) -> bool:
    """Check if analysis for a module is stale (source has changed)."""
    latest = get_latest_module_analysis(source_path, module_name)

    if latest is None:
        return True  # No analysis exists

    # Extract sourceHash from attributes array (NOT top-level)
    analysis_hash = _get_attribute_value(latest, 'sourceHash')

    if not analysis_hash:
        logger.warning(f"No sourceHash in analysis entry for {module_name}")
        return True

    current_hash = compute_file_hash(source_path)
    return analysis_hash != current_hash
```

**Step 3: Run existing tests to verify no regression**

```bash
cd /Users/phong/Projects/chapterwise-app
pytest tests/test_analysis_file_service.py -v
```

Expected: All existing tests pass (or create the test file if it doesn't exist)

**Step 4: Commit**

```bash
cd /Users/phong/Projects/chapterwise-app
git add app/services/analysis_file_service.py
git commit -m "fix(analysis): extract sourceHash from attributes array, not top-level

CRITICAL FIX: sourceHash is stored in the attributes array per Codex V1.2 spec,
but code was reading from top-level. This caused is_analysis_stale() to always
return True, forcing unnecessary re-analysis.

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>"
```

---

## Task 2: Fix App Field Access for model and timestamp

**Files:**
- Modify: `/Users/phong/Projects/chapterwise-app/app/utils/analysis_renderer.py:115-130`

**Step 1: Update render_fallback_html to use attribute extraction**

Find the `render_fallback_html` function and update metadata extraction:

```python
def render_fallback_html(entry: Dict[str, Any]) -> str:
    """Render analysis entry as HTML fallback."""

    # Helper to get attribute value
    def get_attr(key: str) -> Optional[str]:
        for attr in entry.get('attributes', []):
            if attr.get('key') == key:
                return attr.get('value')
        return None

    # Extract from attributes array (Codex V1.2 format)
    model = get_attr('model') or 'unknown'
    timestamp = get_attr('timestamp') or entry.get('metadata', {}).get('created', '')
    status = entry.get('status', 'unknown')
    body = entry.get('body', '')

    # ... rest of rendering logic
```

**Step 2: Commit**

```bash
cd /Users/phong/Projects/chapterwise-app
git add app/utils/analysis_renderer.py
git commit -m "fix(renderer): extract model/timestamp from attributes array

Per Codex V1.2 spec, these fields are in the attributes array, not top-level.

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>"
```

---

## Task 3: Add Schema Validation to Plugins' analysis_writer.py

**Files:**
- Modify: `/Users/phong/Projects/chapterwise-claude-plugins/plugins/chapterwise-analysis/scripts/analysis_writer.py:1-30`
- Modify: `/Users/phong/Projects/chapterwise-claude-plugins/plugins/chapterwise-analysis/scripts/analysis_writer.py:190-200`

**Step 1: Add schema validation imports and loader**

Add at the top of the file (after existing imports):

```python
import jsonschema
from pathlib import Path

# Load schema for validation
SCHEMA_DIR = Path(__file__).parent.parent.parent.parent / 'schemas'

def _load_analysis_schema() -> dict:
    """Load the analysis JSON schema."""
    schema_path = SCHEMA_DIR / 'analysis-v1.2.schema.json'
    if schema_path.exists():
        with open(schema_path, 'r') as f:
            return json.load(f)
    return None  # Schema not available, skip validation

def _validate_analysis(data: dict) -> tuple[bool, list[str]]:
    """Validate analysis data against schema."""
    schema = _load_analysis_schema()
    if schema is None:
        return True, []  # No schema, skip validation

    validator = jsonschema.Draft202012Validator(schema)
    errors = list(validator.iter_errors(data))

    if not errors:
        return True, []

    error_msgs = [f"{'.'.join(str(p) for p in e.absolute_path)}: {e.message}"
                  for e in errors[:5]]  # Limit to 5 errors
    return False, error_msgs
```

**Step 2: Add validation before writing**

In the `add_analysis_result` function, before the file write (around line 192):

```python
    # Validate before writing
    is_valid, errors = _validate_analysis(data)
    if not is_valid:
        print(f"Warning: Analysis validation issues: {errors}", file=sys.stderr)
        # Continue anyway - validation is advisory

    # Ensure parent directory exists
    analysis_path.parent.mkdir(parents=True, exist_ok=True)

    # Write file as JSON
    with open(analysis_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
```

**Step 3: Test the validation**

```bash
cd /Users/phong/Projects/chapterwise-claude-plugins
python3 -c "
from plugins.chapterwise_analysis.scripts.analysis_writer import _validate_analysis
test_data = {
    'metadata': {'formatVersion': '1.2'},
    'id': 'test-analysis',
    'type': 'analysis',
    'attributes': [{'key': 'sourceFile', 'value': 'test.yaml'}],
    'children': []
}
is_valid, errors = _validate_analysis(test_data)
print(f'Valid: {is_valid}, Errors: {errors}')
"
```

Expected: `Valid: True, Errors: []`

**Step 4: Commit**

```bash
cd /Users/phong/Projects/chapterwise-claude-plugins
git add plugins/chapterwise-analysis/scripts/analysis_writer.py
git commit -m "feat(analysis): add schema validation before writing analysis files

Validates analysis output against analysis-v1.2.schema.json before writing.
Validation is advisory (warns but doesn't block) to maintain compatibility.

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>"
```

---

## Task 4: Update _output-format.md to Reference Full Schema

**Files:**
- Modify: `/Users/phong/Projects/chapterwise-claude-plugins/plugins/chapterwise-analysis/modules/_output-format.md`

**Step 1: Rewrite _output-format.md with complete schema reference**

```markdown
# Codex V1.2 Analysis Output Format

All analysis modules MUST output results matching this exact format.
For the authoritative schema, see: `schemas/analysis-v1.2.schema.json`

## Required JSON Structure

```json
{
  "body": "## Module Name\n\nMain analysis content in markdown...",
  "summary": "One-line summary of findings",
  "children": [
    {
      "name": "Section Name",
      "summary": "Section summary",
      "content": "## Section\n\nDetailed content...",
      "attributes": [
        {"key": "score", "name": "Score", "value": 8, "dataType": "int"}
      ]
    }
  ],
  "tags": ["analysis", "module-name"],
  "attributes": [
    {"key": "overall_score", "name": "Overall Score", "value": 7, "dataType": "int"}
  ]
}
```

## How Your Output Becomes an Analysis Entry

The `analysis_writer.py` script wraps your output in the full Codex V1.2 structure:

```json
{
  "metadata": {"formatVersion": "1.2", "created": "...", "updated": "..."},
  "id": "{basename}-analysis",
  "type": "analysis",
  "attributes": [
    {"key": "sourceFile", "value": "source.codex.yaml"},
    {"key": "sourceHash", "value": "16-char-sha256-hash"}
  ],
  "children": [
    {
      "id": "module_name",
      "type": "analysis-module",
      "name": "Module Display Name",
      "children": [
        {
          "id": "entry-YYYYMMDDTHHMMSSz",
          "type": "analysis-entry",
          "status": "published",
          "attributes": [
            {"key": "model", "value": "claude-sonnet-4"},
            {"key": "sourceHash", "value": "16-char-hash"},
            {"key": "analysisStatus", "value": "current"},
            {"key": "timestamp", "value": "ISO-8601"}
          ],
          "body": "YOUR body FIELD",
          "summary": "YOUR summary FIELD",
          "children": "YOUR children ARRAY",
          "tags": "YOUR tags ARRAY"
        }
      ]
    }
  ]
}
```

## Rules

1. **body** - Main analysis in markdown with ## headers (REQUIRED)
2. **summary** - 1-2 sentence overview (REQUIRED)
3. **children** - Structured sub-sections (2-5 recommended)
4. **attributes** - Scored metrics with dataType hint
5. **tags** - Relevant keywords for searchability

## Important Notes

- Module IDs MUST use snake_case: `plot_holes`, NOT `plot-holes`
- Attribute keys MUST use snake_case: `word_count`, NOT `wordCount`
- All scores should be integers 1-10
- Use markdown formatting: `## Headers`, `**bold**`, `- lists`, `> quotes`
```

**Step 2: Commit**

```bash
cd /Users/phong/Projects/chapterwise-claude-plugins
git add plugins/chapterwise-analysis/modules/_output-format.md
git commit -m "docs(analysis): update _output-format.md with full schema reference

Now documents:
- Complete analysis file structure
- How module output becomes analysis entry
- snake_case requirements for module IDs and attribute keys
- Reference to authoritative schema file

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>"
```

---

## Task 5: Fix VS Code Extension V1.2 Support (CRITICAL)

**Files:**
- Modify: `/Users/phong/Projects/chapterwise-codex/src/autoFixer.ts:290-300`

**Step 1: Update auto-fixer to accept V1.2**

Find the format version handling code (around line 290-296) and update:

```typescript
// BEFORE (broken):
} else if (metadata.formatVersion !== '1.0' && metadata.formatVersion !== '1.1') {
  const oldVersion = metadata.formatVersion;
  metadata.formatVersion = '1.1';
  this.fixesApplied.push(`Updated metadata.formatVersion from '${oldVersion}' to '1.1'`);
}

// AFTER (fixed):
} else if (!['1.0', '1.1', '1.2', 'lite'].includes(metadata.formatVersion)) {
  const oldVersion = metadata.formatVersion;
  metadata.formatVersion = '1.2';  // Default to latest, not 1.1
  this.fixesApplied.push(`Updated metadata.formatVersion from '${oldVersion}' to '1.2'`);
}
// Note: V1.2 is now accepted without modification
```

**Step 2: Build and test**

```bash
cd /Users/phong/Projects/chapterwise-codex
npm run compile
```

Expected: Build succeeds with no TypeScript errors

**Step 3: Commit**

```bash
cd /Users/phong/Projects/chapterwise-codex
git add src/autoFixer.ts
git commit -m "fix(auto-fixer): accept formatVersion 1.2 without downgrading

CRITICAL FIX: Previously, V1.2 files were silently downgraded to V1.1.
Now accepts 1.0, 1.1, 1.2, and lite. Unknown versions default to 1.2.

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>"
```

---

## Task 6: Fix VS Code Extension Relation Field Name (CRITICAL)

**Files:**
- Modify: `/Users/phong/Projects/chapterwise-codex/src/codexModel.ts:70-74`
- Modify: `/Users/phong/Projects/chapterwise-codex/src/autoFixer.ts:420-430` (if needed)

**Step 1: Update CodexRelation interface**

Find the CodexRelation interface (around line 70) and update:

```typescript
// BEFORE:
export interface CodexRelation {
  type: string;
  target: string;
  description?: string;
}

// AFTER:
export interface CodexRelation {
  targetId: string;          // Changed from 'target' to match schema
  type?: string;             // Relation type (ally, enemy, parent, etc.)
  kind?: string;             // Alternative to type
  strength?: number;         // 0-1 confidence
  reciprocal?: boolean;      // Bidirectional flag
  description?: string;
}
```

**Step 2: Update any code that references `relation.target`**

Search for `relation.target` and update to `relation.targetId`:

```bash
cd /Users/phong/Projects/chapterwise-codex
grep -rn "relation.target" src/
```

Update each occurrence.

**Step 3: Build and test**

```bash
cd /Users/phong/Projects/chapterwise-codex
npm run compile
```

Expected: Build succeeds (may need to fix additional references)

**Step 4: Commit**

```bash
cd /Users/phong/Projects/chapterwise-codex
git add src/codexModel.ts src/autoFixer.ts
git commit -m "fix(relations): use targetId field name to match schema

CRITICAL FIX: Extension used 'target' but schema specifies 'targetId'.
Also added missing fields: kind, strength, reciprocal.

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>"
```

---

## Task 7: Fix Plugins Format Version Comments

**Files:**
- Modify: `/Users/phong/Projects/chapterwise-claude-plugins/plugins/chapterwise-codex/scripts/auto_fixer.py:50-55`
- Modify: `/Users/phong/Projects/chapterwise-claude-plugins/plugins/chapterwise-codex/scripts/auto_fixer.py:125-130`

**Step 1: Update docstrings to say V1.2, not V1.0**

```python
# Line ~51: Change docstring
"""
Automatically fix common integrity issues in Codex V1.2 content.
"""

# Line ~125: Change method docstring
def _ensure_v1_metadata(self, data: dict) -> None:
    """Ensure V1.2 metadata section exists with required fields."""
```

**Step 2: Commit**

```bash
cd /Users/phong/Projects/chapterwise-claude-plugins
git add plugins/chapterwise-codex/scripts/auto_fixer.py
git commit -m "docs(auto-fixer): update comments to reference V1.2, not V1.0

The code already uses V1.2 everywhere, but comments were outdated.

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>"
```

---

## Task 8: Fix Plugins explode_codex.py Format Version

**Files:**
- Modify: `/Users/phong/Projects/chapterwise-claude-plugins/plugins/chapterwise-codex/scripts/explode_codex.py:366`

**Step 1: Create extracted files with V1.2, not V1.0**

Find line 366 (or search for `'formatVersion': '1.0'`) and update:

```python
# BEFORE:
'metadata': {
    'formatVersion': '1.0',
    ...
}

# AFTER:
'metadata': {
    'formatVersion': '1.2',
    ...
}
```

**Step 2: Also update the V1.0 check if present**

Search for `_is_v1_format` and update or remove the V1.0-specific check.

**Step 3: Commit**

```bash
cd /Users/phong/Projects/chapterwise-claude-plugins
git add plugins/chapterwise-codex/scripts/explode_codex.py
git commit -m "fix(explode): create extracted files with formatVersion 1.2

Was creating V1.0 files then immediately auto-fixing to V1.2.
Now creates V1.2 directly for consistency.

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>"
```

---

## Task 9: Remove/Fix Web App Code in Plugins auto_fixer.py

**Files:**
- Modify: `/Users/phong/Projects/chapterwise-claude-plugins/plugins/chapterwise-codex/scripts/auto_fixer.py:846-891`

**Step 1: Wrap or remove web app imports**

Find the web app specific code (around line 846-891) and either remove it or wrap in try/except:

```python
# Option A: Remove entirely if not needed for CLI
# Delete lines 846-891

# Option B: Wrap in try/except for CLI compatibility
def write_fixed_codex(self, ...):
    """Write fixed codex - works in both CLI and web app contexts."""
    try:
        # Try web app path first
        from app import db
        from app.services.codex_version_service import CodexVersionService
        # ... web app code
    except ImportError:
        # Fall back to simple file write for CLI
        with open(filepath, 'w', encoding='utf-8') as f:
            yaml.dump(data, f, default_flow_style=False, allow_unicode=True)
```

**Step 2: Test CLI mode**

```bash
cd /Users/phong/Projects/chapterwise-claude-plugins
python3 plugins/chapterwise-codex/scripts/auto_fixer.py --help
```

Expected: No ImportError, help message displays

**Step 3: Commit**

```bash
cd /Users/phong/Projects/chapterwise-claude-plugins
git add plugins/chapterwise-codex/scripts/auto_fixer.py
git commit -m "fix(auto-fixer): handle CLI mode without web app dependencies

Wrapped web app imports in try/except to allow CLI usage without
Flask app context.

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>"
```

---

## Task 10: Add Logging to Plugins analysis_writer.py

**Files:**
- Modify: `/Users/phong/Projects/chapterwise-claude-plugins/plugins/chapterwise-analysis/scripts/analysis_writer.py`

**Step 1: Add logging setup**

At the top of the file, after imports:

```python
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
```

**Step 2: Replace print statements with logger calls**

```python
# Replace: print(f"Written to: {output_path}")
# With:
logger.info(f"Written to: {output_path}")

# Replace: print(f"Warning: ...", file=sys.stderr)
# With:
logger.warning(f"Analysis validation issues: {errors}")
```

**Step 3: Commit**

```bash
cd /Users/phong/Projects/chapterwise-claude-plugins
git add plugins/chapterwise-analysis/scripts/analysis_writer.py
git commit -m "refactor(analysis-writer): use logging instead of print statements

Consistent with other scripts in the plugin.

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>"
```

---

## Task 11: Push All Changes

**Step 1: Push chapterwise-app changes**

```bash
cd /Users/phong/Projects/chapterwise-app
git push origin ANALYSIS-FILE-BASED
```

**Step 2: Push chapterwise-claude-plugins changes**

```bash
cd /Users/phong/Projects/chapterwise-claude-plugins
git push origin master
```

**Step 3: Push chapterwise-codex changes**

```bash
cd /Users/phong/Projects/chapterwise-codex
git push origin main
```

---

## Verification Checklist

After all tasks complete:

- [ ] App: `is_analysis_stale()` correctly reads sourceHash from attributes
- [ ] App: Renderer displays model and timestamp from attributes
- [ ] Plugins: analysis_writer validates against schema before writing
- [ ] Plugins: _output-format.md documents full schema structure
- [ ] Plugins: auto_fixer.py comments reference V1.2
- [ ] Plugins: explode_codex.py creates V1.2 files
- [ ] Plugins: auto_fixer.py works in CLI mode without web app
- [ ] Plugins: analysis_writer uses logging
- [ ] VS Code: Auto-fixer accepts V1.2 without downgrading
- [ ] VS Code: CodexRelation uses targetId field

---

## Integration Test

After all fixes, run this end-to-end test:

1. Create a test codex file in VS Code extension
2. Run `/analysis summary` on it via plugins
3. Open the `.analysis.json` in chapterwise-app
4. Verify:
   - Analysis displays correctly
   - Staleness detection works (shows "current" not "stale")
   - Model and timestamp display correctly
   - Re-opening in VS Code doesn't downgrade formatVersion
