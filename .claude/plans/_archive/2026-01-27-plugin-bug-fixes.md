# ChapterWise Plugin Bug Fixes Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Fix critical bugs in the ChapterWise Codex plugin to achieve 100% production readiness.

**Architecture:** Surgical edits to 8 Python scripts - fixing format version inconsistencies, import path bugs, and adding missing shebangs. No architectural changes, just targeted bug fixes.

**Tech Stack:** Python 3, YAML, Claude Code plugin system

---

## Issue Summary

| # | Issue | File | Lines | Severity |
|---|-------|------|-------|----------|
| 1 | Recovery creates "1.0" instead of "1.2" | `auto_fixer.py` | 1008, 1081 | CRITICAL |
| 2 | Docstring says "1.0" instead of "1.2" | `auto_fixer.py` | 128 | LOW |
| 3 | Import path references wrong directory | `explode_codex.py` | 44-67 | CRITICAL |
| 4 | References non-existent file_manager.py | `implode_codex.py` | 57 | LOW (has fallback) |
| 5 | Missing shebang | `auto_fixer.py` | 1 | MEDIUM |
| 6 | Missing shebang | `convert_format.py` | 1 | MEDIUM |
| 7 | Missing shebang | `index_generator.py` | 1 | MEDIUM |
| 8 | Missing shebang | `lite_helper.py` | 1 | MEDIUM |
| 9 | Missing shebang | `tag_generator.py` | 1 | MEDIUM |
| 10 | Missing shebang | `word_count.py` | 1 | MEDIUM |

---

## Task 1: Fix Format Version in auto_fixer.py Recovery Functions

**Files:**
- Modify: `plugins/chapterwise-codex/scripts/auto_fixer.py:1008`
- Modify: `plugins/chapterwise-codex/scripts/auto_fixer.py:1081`
- Modify: `plugins/chapterwise-codex/scripts/auto_fixer.py:128`

**Step 1: Fix line 1008 - JSON recovery function**

Change:
```python
                    "formatVersion": "1.0",
```
To:
```python
                    "formatVersion": "1.2",
```

Also update line 1017 message from "V1.0" to "V1.2":
```python
            self.fixes_applied.append("Created minimal valid V1.2 codex structure from corrupted file")
```

**Step 2: Fix line 1081 - YAML recovery function**

Change:
```python
                    "formatVersion": "1.0",
```
To:
```python
                    "formatVersion": "1.2",
```

Also update line 1090 message from "V1.0" to "V1.2":
```python
            self.fixes_applied.append("Created minimal valid V1.2 codex structure from corrupted YAML file")
```

**Step 3: Fix line 128 - Docstring**

Change:
```python
        - metadata.formatVersion must be "1.0"
```
To:
```python
        - metadata.formatVersion must be "1.2"
```

**Step 4: Verify changes**

Run:
```bash
grep -n 'formatVersion.*1\.' plugins/chapterwise-codex/scripts/auto_fixer.py
```
Expected: Lines 148, 150, 152, 1008, 1081 should all show "1.2"

**Step 5: Commit**

```bash
git add plugins/chapterwise-codex/scripts/auto_fixer.py
git commit -m "fix(auto_fixer): use formatVersion 1.2 in recovery functions

Previously recovery functions created files with formatVersion 1.0,
which is outdated. Now uses 1.2 to match current spec."
```

---

## Task 2: Fix Import Path in explode_codex.py

**Files:**
- Modify: `plugins/chapterwise-codex/scripts/explode_codex.py:44-67`

**Step 1: Replace the broken import block**

Find this block (lines 44-67):
```python
# Setup path for plugin execution - import from format skill
script_dir = Path(__file__).resolve().parent
plugin_root = script_dir.parent.parent
format_skill_dir = plugin_root / "skills" / "format"

# Add format skill directory to path for auto_fixer import
if str(format_skill_dir) not in sys.path:
    sys.path.insert(0, str(format_skill_dir))

# Import auto-fixer for post-processing
try:
    from auto_fixer import CodexAutoFixer
except ImportError:
    # Fallback: try importing via importlib
    import importlib.util
    auto_fixer_path = format_skill_dir / 'auto_fixer.py'
    if auto_fixer_path.exists():
        spec = importlib.util.spec_from_file_location("auto_fixer", auto_fixer_path)
        auto_fixer_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(auto_fixer_module)
        CodexAutoFixer = auto_fixer_module.CodexAutoFixer
    else:
        # Ultimate fallback - no auto-fixing available
        CodexAutoFixer = None
```

Replace with:
```python
# Setup path for plugin execution - import auto_fixer from same directory
script_dir = Path(__file__).resolve().parent

# Add scripts directory to path for auto_fixer import
if str(script_dir) not in sys.path:
    sys.path.insert(0, str(script_dir))

# Import auto-fixer for post-processing
try:
    from auto_fixer import CodexAutoFixer
except ImportError:
    # Fallback: try importing via importlib
    import importlib.util
    auto_fixer_path = script_dir / 'auto_fixer.py'
    if auto_fixer_path.exists():
        spec = importlib.util.spec_from_file_location("auto_fixer", auto_fixer_path)
        auto_fixer_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(auto_fixer_module)
        CodexAutoFixer = auto_fixer_module.CodexAutoFixer
    else:
        # Ultimate fallback - no auto-fixing available
        CodexAutoFixer = None
```

**Step 2: Verify the import works**

Run:
```bash
cd /Users/phong/Projects/chapterwise-claude-plugins/plugins/chapterwise-codex/scripts
python3 -c "from explode_codex import CodexExploder; print('Import OK')"
```
Expected: "Import OK" with no errors

**Step 3: Commit**

```bash
git add plugins/chapterwise-codex/scripts/explode_codex.py
git commit -m "fix(explode_codex): correct auto_fixer import path

auto_fixer.py is in the same scripts/ directory, not in skills/format/.
Fixed import path to look in current directory."
```

---

## Task 3: Clean Up implode_codex.py file_manager Reference

**Files:**
- Modify: `plugins/chapterwise-codex/scripts/implode_codex.py:54-77`

**Step 1: Simplify the import block**

Find this block (lines 54-77):
```python
# Import YAML dumper for consistent formatting
try:
    import importlib.util
    file_manager_path = Path(__file__).parent / 'file_manager.py'
    if file_manager_path.exists():
        spec_fm = importlib.util.spec_from_file_location("file_manager", file_manager_path)
        file_manager_module = importlib.util.module_from_spec(spec_fm)
        spec_fm.loader.exec_module(file_manager_module)
        get_yaml_dumper_with_pipe_format = file_manager_module.get_yaml_dumper_with_pipe_format
    else:
        raise ImportError("file_manager.py not found")
except Exception:
    # Fallback YAML dumper
    def get_yaml_dumper_with_pipe_format():
        class CustomDumper(yaml.SafeDumper):
            pass

        def str_representer(dumper, data):
            if isinstance(data, str) and (len(data) > 80 or '\n' in data):
                return dumper.represent_scalar('tag:yaml.org,2002:str', data, style='|')
            return dumper.represent_scalar('tag:yaml.org,2002:str', data)

        CustomDumper.add_representer(str, str_representer)
        return CustomDumper
```

Replace with (remove dead code, keep only the working fallback):
```python
# YAML dumper for consistent formatting (pipe syntax for long strings)
def get_yaml_dumper_with_pipe_format():
    """Create a custom YAML dumper that uses pipe syntax for long strings."""
    class CustomDumper(yaml.SafeDumper):
        pass

    def str_representer(dumper, data):
        if isinstance(data, str) and (len(data) > 80 or '\n' in data):
            return dumper.represent_scalar('tag:yaml.org,2002:str', data, style='|')
        return dumper.represent_scalar('tag:yaml.org,2002:str', data)

    CustomDumper.add_representer(str, str_representer)
    return CustomDumper
```

**Step 2: Verify it still works**

Run:
```bash
cd /Users/phong/Projects/chapterwise-claude-plugins/plugins/chapterwise-codex/scripts
python3 -c "from implode_codex import CodexImploder; print('Import OK')"
```
Expected: "Import OK" with no errors

**Step 3: Commit**

```bash
git add plugins/chapterwise-codex/scripts/implode_codex.py
git commit -m "refactor(implode_codex): remove dead file_manager.py reference

file_manager.py doesn't exist. Removed try/import block and kept
only the inline YAML dumper implementation that was already working."
```

---

## Task 4: Add Shebangs to 6 Python Scripts

**Files:**
- Modify: `plugins/chapterwise-codex/scripts/auto_fixer.py:1`
- Modify: `plugins/chapterwise-codex/scripts/convert_format.py:1`
- Modify: `plugins/chapterwise-codex/scripts/index_generator.py:1`
- Modify: `plugins/chapterwise-codex/scripts/lite_helper.py:1`
- Modify: `plugins/chapterwise-codex/scripts/tag_generator.py:1`
- Modify: `plugins/chapterwise-codex/scripts/word_count.py:1`

**Step 1: Add shebang to auto_fixer.py**

The file currently starts with:
```python
"""
Auto-Fix Service for Codex V1.2 Integrity Issues
```

Change to:
```python
#!/usr/bin/env python3
"""
Auto-Fix Service for Codex V1.2 Integrity Issues
```

**Step 2: Add shebang to convert_format.py**

The file currently starts with:
```python
"""
```

Change to:
```python
#!/usr/bin/env python3
"""
```

**Step 3: Add shebang to index_generator.py**

Same pattern - add `#!/usr/bin/env python3` as first line.

**Step 4: Add shebang to lite_helper.py**

Same pattern - add `#!/usr/bin/env python3` as first line.

**Step 5: Add shebang to tag_generator.py**

Same pattern - add `#!/usr/bin/env python3` as first line.

**Step 6: Add shebang to word_count.py**

Same pattern - add `#!/usr/bin/env python3` as first line.

**Step 7: Verify all scripts have shebangs**

Run:
```bash
cd /Users/phong/Projects/chapterwise-claude-plugins/plugins/chapterwise-codex/scripts
for f in *.py; do echo "=== $f ==="; head -1 "$f"; done
```
Expected: All 8 files show `#!/usr/bin/env python3` as first line

**Step 8: Commit**

```bash
git add plugins/chapterwise-codex/scripts/auto_fixer.py \
        plugins/chapterwise-codex/scripts/convert_format.py \
        plugins/chapterwise-codex/scripts/index_generator.py \
        plugins/chapterwise-codex/scripts/lite_helper.py \
        plugins/chapterwise-codex/scripts/tag_generator.py \
        plugins/chapterwise-codex/scripts/word_count.py
git commit -m "chore(scripts): add shebangs to all Python scripts

Added #!/usr/bin/env python3 to 6 scripts that were missing it.
This enables direct execution without explicitly calling python3."
```

---

## Task 5: Final Verification and Push

**Step 1: Run full verification**

```bash
cd /Users/phong/Projects/chapterwise-claude-plugins

# Verify no more "1.0" format versions in recovery
grep -n 'formatVersion.*1\.0' plugins/chapterwise-codex/scripts/auto_fixer.py
# Expected: No output (or only in comments/accepted versions list)

# Verify no more skills/format path references
grep -rn 'skills/format' plugins/chapterwise-codex/scripts/
# Expected: No output

# Verify no more file_manager.py references
grep -rn 'file_manager' plugins/chapterwise-codex/scripts/
# Expected: No output

# Verify all shebangs
for f in plugins/chapterwise-codex/scripts/*.py; do head -1 "$f"; done | sort | uniq -c
# Expected: 8 #!/usr/bin/env python3

# Test imports
cd plugins/chapterwise-codex/scripts
python3 -c "
from auto_fixer import CodexAutoFixer
from explode_codex import CodexExploder
from implode_codex import CodexImploder
from convert_format import CodexConverter
from index_generator import IndexGenerator
from lite_helper import LiteHelper
from tag_generator import TagGenerator
from word_count import WordCounter
print('All imports OK')
"
```

**Step 2: Push all changes**

```bash
git push
```

**Step 3: Update plugin (if locally installed)**

```bash
# If using plugin locally, update it
claude /plugin update chapterwise-codex
```

---

## Verification Checklist

After all tasks complete:

- [ ] `auto_fixer.py` recovery functions use formatVersion "1.2"
- [ ] `auto_fixer.py` docstring says "1.2" not "1.0"
- [ ] `explode_codex.py` imports auto_fixer from same directory
- [ ] `implode_codex.py` has no file_manager.py reference
- [ ] All 8 scripts have `#!/usr/bin/env python3` shebang
- [ ] All script imports work without errors
- [ ] Changes pushed to remote
- [ ] Plugin updated (if installed)

---

## Rollback Plan

If issues arise, revert all commits:

```bash
git log --oneline -5  # Find commit before our changes
git revert HEAD~4..HEAD  # Revert last 4 commits
git push
```
