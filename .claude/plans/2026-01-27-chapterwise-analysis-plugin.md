# Chapterwise Analysis Plugin Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Create a Claude Code plugin that runs literary analysis on `.codex.yaml` files using the same analysis modules as ChapterWise, outputting results to sibling `.analysis.codex.yaml` files.

**Architecture:** Plugin with `/analyze` command supporting both interactive picker and direct module invocation. Analysis runs inline for single files, spawns subagents for batch operations. Results stored in sibling files with staleness detection via sourceHash and bounded history (configurable depth).

**Tech Stack:** Claude Code plugin (markdown commands + Python scripts), Codex V1.2 format (YAML)

---

## Plugin Structure

```
plugins/chapterwise-analysis/
├── .claude-plugin/
│   └── plugin.json              # name: "analyze"
├── commands/
│   ├── analyze.md               # Main /analyze command
│   └── analyze-list.md          # /analyze list command
├── modules/                     # Built-in analysis modules (v1.0: 5 modules)
│   ├── _output-format.md        # Shared Codex V1.2 output template
│   ├── summary.md
│   ├── characters.md
│   ├── plot-holes.md
│   ├── story-beats.md
│   └── critical-review.md
└── scripts/
    ├── analysis_writer.py       # Writes/updates .analysis.codex.yaml files
    ├── module_loader.py         # Discovers built-in + custom modules
    └── staleness_checker.py     # Computes sourceHash, checks freshness
```

**Extensibility paths (discovered at runtime):**
- `~/.claude/analyze/modules/*.md` - User global custom modules
- `./.chapterwise/analysis-modules/*.md` - Project-specific modules

---

## Configuration Cascade

Priority (later overrides earlier):
1. Built-in defaults
2. Global config: `~/.claude/analyze/config.yaml`
3. Project config: `./.chapterwise/analysis.yaml`
4. Command flags

```yaml
# ~/.claude/analyze/config.yaml (global)
# ./.chapterwise/analysis.yaml (project)

# History management
historyDepth: 3              # Keep last N analysis results per module

# Default behavior
skipIfFresh: true            # Skip if sourceHash matches (use --force to override)
defaultModules:              # Modules to run with /analyze --all
  - summary
  - characters

# Model preference (optional)
model: claude-sonnet-4       # Model to record in analysis metadata

# Custom module paths (additional to standard locations)
customModulePaths: []        # Extra directories to search for modules

# Output preferences
verboseOutput: false         # Show full analysis in console after completion
autoCommit: false            # Git commit analysis files automatically
```

**Note:** No per-module overrides in v1.0 - global settings only for simplicity.

---

## Command Interface

```bash
# Discovery & Help
/analyze                              # Interactive picker (multi-select)
/analyze list                         # Print all available modules
/analyze help plot-holes              # Module details

# Direct invocation
/analyze summary                      # Single module
/analyze summary characters           # Multiple modules

# Targeting
/analyze summary mybook.codex.yaml    # Specific file
/analyze summary --node chapter-3     # Specific node by ID
/analyze summary --glob "ch/*.codex.yaml"  # Multiple files
/analyze summary --all                # All .codex.yaml in project

# Behavior
/analyze summary --force              # Re-run even if fresh
/analyze summary --history-depth 5    # Override history retention
/analyze summary --dry-run            # Preview what would run
```

---

## Interactive Picker Flow (Category-First)

When `/analyze` is called with no arguments, use AskUserQuestion with category-first approach (scales to 30+ modules):

```
Step 1: "Which category of analysis?"
  ○ Narrative Structure (summary, story-beats)
  ○ Characters (characters)
  ○ Quality Assessment (plot-holes, critical-review)
  ○ All modules

Step 2 (if not "All"): "Which module(s)?" [multiSelect: true]
  ○ summary - Chapter summaries
  ○ story-beats - Key narrative moments

Step 3: "Which file to analyze?"
  [If .codex.yaml files found in cwd, show up to 4]
  ○ chapter-1.codex.yaml
  ○ chapter-2.codex.yaml
  ○ manuscript.codex.yaml
  ○ Other (specify path)
```

---

## File Auto-Detection

When user runs `/analyze summary` without a file path:

1. Look for `.codex.yaml` files in current directory
2. If exactly 1 found → use it automatically
3. If 2-4 found → show picker via AskUserQuestion
4. If >4 found → show first 3 + "Other (specify path)"
5. If 0 found → show helpful error:

```
No .codex.yaml files found in current directory.

Try:
  /analyze summary path/to/file.codex.yaml
  /analyze summary --glob "**/*.codex.yaml"
```

---

## Node Extraction (`--node`)

When user runs `/analyze summary --node chapter-3 book.codex.yaml`:

1. Read the full `.codex.yaml` file
2. Search recursively for node with matching ID or name:
   - Priority 1: Exact `id` match (UUID or slug)
   - Priority 2: Exact `name` match (case-insensitive)
   - Priority 3: Partial `name` match (contains)
3. Extract that node + its children as content to analyze
4. Record target node in output:

```yaml
# In .analysis.codex.yaml
children:
  - name: summary
    targetNode: "chapter-3"
    targetNodeName: "Chapter 3: The Beginning"
    history:
      - ...
```

5. If no match found: Error with list of available node IDs/names

---

## Output Format

Sibling file: `manuscript.codex.yaml` → `manuscript.analysis.codex.yaml`

```yaml
metadata:
  formatVersion: "1.2"
  documentVersion: "1.0.0"

id: "analysis-root-uuid"
type: analysis-collection
sourceFile: "./manuscript.codex.yaml"
sourceHash: "a1b2c3d4e5f6"  # SHA-256 first 16 chars of source content

children:
  - id: "module-summary-uuid"
    type: analysis-module
    name: summary
    history:
      - id: "run-uuid-1"
        timestamp: "2026-01-27T10:30:00Z"
        sourceHash: "a1b2c3d4e5f6"
        model: "claude-sonnet-4"
        body: |
          ## Summary
          [Analysis content in markdown...]
        children:
          - name: "Key Events"
            content: "..."
      - id: "run-uuid-2"
        timestamp: "2026-01-26T15:00:00Z"
        sourceHash: "older-hash"
        # ... older analysis (up to historyDepth)
```

---

## Tasks

### Task 1: Plugin Scaffold

**Files:**
- Create: `plugins/chapterwise-analysis/.claude-plugin/plugin.json`
- Create: `plugins/chapterwise-analysis/commands/analyze.md` (stub)

**Step 1: Create plugin.json**

```json
{
  "name": "chapterwise-analysis",
  "description": "AI-powered literary analysis for Codex files (ChapterWise Analysis)",
  "version": "1.0.0",
  "homepage": "https://github.com/ansonphong/chapterwise-claude-plugins",
  "repository": "https://github.com/ansonphong/chapterwise-claude-plugins",
  "license": "MIT"
}
```

**Step 2: Create stub analysis.md command**

```markdown
---
description: Run AI analysis on Codex files (ChapterWise Analysis)
allowed-tools: Read, Grep, Glob, Bash, Write, Edit, AskUserQuestion, Task
triggers:
  # Primary (branded - discoverable via /chapterwise)
  - chapterwise:analysis
  - chapterwise:analysis summary
  - chapterwise:analysis characters
  - chapterwise:analysis plot-holes
  - chapterwise:analysis story-beats
  - chapterwise:analysis critical-review
  - chapterwise:analysis list
  - chapterwise:analysis help
  # Shortcuts (power users)
  - analysis
  - analysis summary
  - analysis characters
  - analysis plot-holes
  - analysis story-beats
  - analysis critical-review
  - analysis list
  - analysis help
---

# ChapterWise Analysis Command (Stub)

This command will be implemented in subsequent tasks.
```

**Step 3: Verify plugin loads**

Run: `claude /analyze` in the plugins directory
Expected: Command recognized (even if stub)

**Step 4: Commit**

```bash
git add plugins/chapterwise-analysis/
git commit -m "feat(analyze): scaffold plugin structure"
```

---

### Task 2: Module Loader Script

**Files:**
- Create: `plugins/chapterwise-analysis/scripts/module_loader.py`

**Step 1: Write module_loader.py**

```python
#!/usr/bin/env python3
"""
Discovers and loads analysis modules from:
1. Built-in: ${CLAUDE_PLUGIN_ROOT}/modules/
2. User global: ~/.claude/analyze/modules/
3. Project: ./.chapterwise/analysis-modules/
"""
import os
import yaml
from pathlib import Path
from typing import Dict, List, Optional

def parse_module_frontmatter(filepath: Path) -> Optional[Dict]:
    """Parse YAML frontmatter from a module markdown file."""
    content = filepath.read_text()
    if not content.startswith('---'):
        return None

    parts = content.split('---', 2)
    if len(parts) < 3:
        return None

    try:
        metadata = yaml.safe_load(parts[1])
        metadata['_filepath'] = str(filepath)
        metadata['_content'] = parts[2].strip()
        return metadata
    except yaml.YAMLError:
        return None

def discover_modules(plugin_root: str = None) -> Dict[str, Dict]:
    """
    Discover all available modules from all paths.
    Later paths override earlier (project > user > built-in).
    """
    modules = {}

    search_paths = []

    # 1. Built-in modules
    if plugin_root:
        search_paths.append(Path(plugin_root) / 'modules')

    # 2. User global modules
    user_modules = Path.home() / '.claude' / 'analyze' / 'modules'
    if user_modules.exists():
        search_paths.append(user_modules)

    # 3. Project modules
    project_modules = Path.cwd() / '.chapterwise' / 'analysis-modules'
    if project_modules.exists():
        search_paths.append(project_modules)

    for search_path in search_paths:
        if not search_path.exists():
            continue
        for md_file in search_path.glob('*.md'):
            if md_file.name.startswith('_'):
                continue  # Skip partials like _output-format.md

            metadata = parse_module_frontmatter(md_file)
            if metadata and 'name' in metadata:
                modules[metadata['name']] = metadata

    return modules

def list_modules(plugin_root: str = None) -> List[Dict]:
    """Return list of modules sorted by category then name."""
    modules = discover_modules(plugin_root)
    module_list = list(modules.values())

    return sorted(module_list, key=lambda m: (
        m.get('category', 'Other'),
        m.get('name', '')
    ))

def get_module(name: str, plugin_root: str = None) -> Optional[Dict]:
    """Get a specific module by name."""
    modules = discover_modules(plugin_root)
    return modules.get(name)

if __name__ == '__main__':
    import sys
    import json

    plugin_root = os.environ.get('CLAUDE_PLUGIN_ROOT', '.')

    if len(sys.argv) > 1:
        if sys.argv[1] == 'list':
            modules = list_modules(plugin_root)
            print(json.dumps(modules, indent=2))
        elif sys.argv[1] == 'get' and len(sys.argv) > 2:
            module = get_module(sys.argv[2], plugin_root)
            if module:
                print(json.dumps(module, indent=2))
            else:
                print(f"Module '{sys.argv[2]}' not found", file=sys.stderr)
                sys.exit(1)
    else:
        print("Usage: module_loader.py list | get <name>")
```

**Step 2: Test the loader**

Run: `python3 plugins/chapterwise-analysis/scripts/module_loader.py list`
Expected: Empty list `[]` (no modules yet)

**Step 3: Commit**

```bash
git add plugins/chapterwise-analysis/scripts/module_loader.py
git commit -m "feat(analyze): add module discovery system"
```

---

### Task 3: Staleness Checker Script

**Files:**
- Create: `plugins/chapterwise-analysis/scripts/staleness_checker.py`

**Step 1: Write staleness_checker.py**

```python
#!/usr/bin/env python3
"""
Computes sourceHash for staleness detection.
Checks if existing analysis is fresh or stale.
"""
import hashlib
import yaml
from pathlib import Path
from typing import Optional, Tuple

def compute_source_hash(content: str) -> str:
    """Compute SHA-256 hash, return first 16 chars."""
    return hashlib.sha256(content.encode('utf-8')).hexdigest()[:16]

def get_analysis_file_path(source_path: Path) -> Path:
    """Convert source.codex.yaml -> source.analysis.codex.yaml"""
    name = source_path.name
    if name.endswith('.codex.yaml'):
        new_name = name.replace('.codex.yaml', '.analysis.codex.yaml')
    elif name.endswith('.codex.json'):
        new_name = name.replace('.codex.json', '.analysis.codex.json')
    else:
        new_name = name + '.analysis.yaml'
    return source_path.parent / new_name

def get_current_source_hash(source_path: Path) -> Optional[str]:
    """Read source file and compute its hash."""
    if not source_path.exists():
        return None
    content = source_path.read_text()
    return compute_source_hash(content)

def get_analysis_source_hash(analysis_path: Path) -> Optional[str]:
    """Read sourceHash from existing analysis file."""
    if not analysis_path.exists():
        return None

    try:
        content = yaml.safe_load(analysis_path.read_text())
        return content.get('sourceHash')
    except (yaml.YAMLError, AttributeError):
        return None

def get_module_latest_hash(analysis_path: Path, module_name: str) -> Optional[str]:
    """Get the sourceHash from the latest run of a specific module."""
    if not analysis_path.exists():
        return None

    try:
        content = yaml.safe_load(analysis_path.read_text())
        for child in content.get('children', []):
            if child.get('name') == module_name:
                history = child.get('history', [])
                if history:
                    return history[0].get('sourceHash')
        return None
    except (yaml.YAMLError, AttributeError, TypeError):
        return None

def is_analysis_stale(source_path: Path, module_name: str = None) -> Tuple[bool, str, Optional[str]]:
    """
    Check if analysis is stale for a source file.

    Returns: (is_stale, current_hash, existing_hash)
    """
    analysis_path = get_analysis_file_path(source_path)
    current_hash = get_current_source_hash(source_path)

    if current_hash is None:
        return (True, None, None)

    if module_name:
        existing_hash = get_module_latest_hash(analysis_path, module_name)
    else:
        existing_hash = get_analysis_source_hash(analysis_path)

    is_stale = current_hash != existing_hash
    return (is_stale, current_hash, existing_hash)

if __name__ == '__main__':
    import sys
    import json

    if len(sys.argv) < 2:
        print("Usage: staleness_checker.py <source_file> [module_name]")
        sys.exit(1)

    source_path = Path(sys.argv[1])
    module_name = sys.argv[2] if len(sys.argv) > 2 else None

    is_stale, current, existing = is_analysis_stale(source_path, module_name)

    result = {
        'source': str(source_path),
        'module': module_name,
        'isStale': is_stale,
        'currentHash': current,
        'existingHash': existing,
        'analysisFile': str(get_analysis_file_path(source_path))
    }
    print(json.dumps(result, indent=2))
```

**Step 2: Test with a sample file**

Run: `python3 plugins/chapterwise-analysis/scripts/staleness_checker.py /path/to/any.codex.yaml`
Expected: JSON output showing `isStale: true` (no analysis exists)

**Step 3: Commit**

```bash
git add plugins/chapterwise-analysis/scripts/staleness_checker.py
git commit -m "feat(analyze): add staleness detection via sourceHash"
```

---

### Task 4: Analysis Writer Script

**Files:**
- Create: `plugins/chapterwise-analysis/scripts/analysis_writer.py`

**Step 1: Write analysis_writer.py**

```python
#!/usr/bin/env python3
"""
Writes analysis results to .analysis.codex.yaml files.
Handles history management with configurable depth.
"""
import uuid
import yaml
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional
from staleness_checker import get_analysis_file_path, compute_source_hash

DEFAULT_HISTORY_DEPTH = 3

def generate_uuid() -> str:
    """Generate a UUID v4 string."""
    return str(uuid.uuid4())

def create_analysis_file_structure(source_path: Path, source_hash: str) -> Dict:
    """Create initial structure for a new analysis file."""
    return {
        'metadata': {
            'formatVersion': '1.2',
            'documentVersion': '1.0.0',
        },
        'id': generate_uuid(),
        'type': 'analysis-collection',
        'sourceFile': f'./{source_path.name}',
        'sourceHash': source_hash,
        'children': []
    }

def create_analysis_entry(
    module_name: str,
    source_hash: str,
    model: str,
    body: str,
    children: list = None
) -> Dict:
    """Create a single analysis history entry."""
    return {
        'id': generate_uuid(),
        'timestamp': datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
        'sourceHash': source_hash,
        'model': model,
        'body': body,
        'children': children or []
    }

def add_analysis_result(
    source_path: Path,
    module_name: str,
    analysis_content: Dict[str, Any],
    model: str = 'claude-sonnet-4',
    history_depth: int = DEFAULT_HISTORY_DEPTH
) -> Path:
    """
    Add analysis result to the .analysis.codex.yaml file.
    Creates file if doesn't exist, prepends to module history.
    """
    analysis_path = get_analysis_file_path(source_path)
    source_content = source_path.read_text()
    source_hash = compute_source_hash(source_content)

    # Load or create analysis file
    if analysis_path.exists():
        data = yaml.safe_load(analysis_path.read_text()) or {}
    else:
        data = create_analysis_file_structure(source_path, source_hash)

    # Update root sourceHash
    data['sourceHash'] = source_hash

    # Find or create module entry
    module_entry = None
    for child in data.get('children', []):
        if child.get('name') == module_name:
            module_entry = child
            break

    if module_entry is None:
        module_entry = {
            'id': generate_uuid(),
            'type': 'analysis-module',
            'name': module_name,
            'history': []
        }
        data.setdefault('children', []).append(module_entry)

    # Create new analysis entry
    new_entry = create_analysis_entry(
        module_name=module_name,
        source_hash=source_hash,
        model=model,
        body=analysis_content.get('body', ''),
        children=analysis_content.get('children', [])
    )

    # Prepend to history and trim to depth
    history = module_entry.get('history', [])
    history.insert(0, new_entry)
    module_entry['history'] = history[:history_depth]

    # Write file
    analysis_path.write_text(yaml.dump(data, default_flow_style=False, allow_unicode=True, sort_keys=False))

    return analysis_path

if __name__ == '__main__':
    import sys
    import json

    if len(sys.argv) < 4:
        print("Usage: analysis_writer.py <source_file> <module_name> <analysis_json>")
        print("       analysis_writer.py <source_file> <module_name> - (reads from stdin)")
        sys.exit(1)

    source_path = Path(sys.argv[1])
    module_name = sys.argv[2]

    if sys.argv[3] == '-':
        analysis_json = sys.stdin.read()
    else:
        analysis_json = sys.argv[3]

    analysis_content = json.loads(analysis_json)

    output_path = add_analysis_result(source_path, module_name, analysis_content)
    print(f"Written to: {output_path}")
```

**Step 2: Test with mock data**

Run:
```bash
echo '{"body": "Test analysis content", "children": []}' | python3 plugins/chapterwise-analysis/scripts/analysis_writer.py /path/to/test.codex.yaml summary -
```
Expected: Creates `test.analysis.codex.yaml` with summary module entry

**Step 3: Commit**

```bash
git add plugins/chapterwise-analysis/scripts/analysis_writer.py
git commit -m "feat(analyze): add analysis writer with history management"
```

---

### Task 5: Shared Output Format Template

**Files:**
- Create: `plugins/chapterwise-analysis/modules/_output-format.md`

**Step 1: Write _output-format.md**

```markdown
# Codex V1.2 Analysis Output Format

All analysis modules MUST output results in this exact format.

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
        {
          "key": "score",
          "name": "Score",
          "value": 8,
          "dataType": "int"
        }
      ]
    }
  ],
  "tags": ["analysis", "module-name"],
  "attributes": [
    {
      "key": "overall_score",
      "name": "Overall Score",
      "value": 7,
      "dataType": "int"
    }
  ]
}
```

## Rules

1. **body** - Main analysis in markdown with ## headers
2. **summary** - 1-2 sentence overview
3. **children** - Structured sub-sections (2-5 recommended)
4. **attributes** - Scored metrics with dataType
5. **tags** - Relevant keywords for searchability

## Markdown in body/content

- Use `##` for section headers
- Use `**bold**` for emphasis
- Use `- ` for bullet lists
- Use `> ` for quotes from source text
- Keep paragraphs concise
```

**Step 2: Commit**

```bash
git add plugins/chapterwise-analysis/modules/_output-format.md
git commit -m "docs(analyze): add shared output format template"
```

---

### Task 6: Summary Module

**Files:**
- Create: `plugins/chapterwise-analysis/modules/summary.md`

**Step 1: Write summary.md**

Reference the prompt structure from `/Users/phong/Projects/chapterwise-app/app/analysis/modules/summary.py` and adapt for Claude Code.

```markdown
---
name: summary
displayName: Chapter Summary
description: Generates concise summaries highlighting key events, character interactions, and story developments
category: Narrative Structure
icon: ph ph-sparkle
applicableTypes: []
---

# Summary Analysis Module

You are an expert literary analyst specializing in Chapter Summaries.

## Your Task

Analyze the provided content and generate a comprehensive summary covering:

1. **Key Events** - Major plot points and developments
2. **Character Interactions** - Important character moments and relationships
3. **Story Progression** - How this content advances the narrative
4. **Revelations** - Any new information or discoveries revealed

## Output Format

Return your analysis as a JSON object with this structure:

```json
{
  "body": "## Summary\n\n[Detailed summary with markdown formatting covering all key events, character interactions, and story progression]\n\n### Key Events\n- [List major plot points]\n- [Describe critical developments]\n\n### Character Interactions\n- [Highlight important character moments]",
  "summary": "[Brief 1-2 sentence overview of the content's main events and developments]",
  "children": [
    {
      "name": "Revelations",
      "summary": "Major revelations and plot developments",
      "content": "## Revelations\n\n[Detailed analysis of major revelations that change the story direction]",
      "attributes": [
        {"key": "impact_level", "name": "Impact Level", "value": 7, "dataType": "int"}
      ]
    },
    {
      "name": "Character Development",
      "summary": "Character growth and evolution",
      "content": "## Character Development\n\n[Analysis of character growth and major points of character movement]",
      "attributes": [
        {"key": "characters_involved", "name": "Characters Involved", "value": 3, "dataType": "int"}
      ]
    }
  ],
  "tags": ["summary", "chapter-analysis", "plot", "character-development"],
  "attributes": [
    {"key": "word_count_estimate", "name": "Word Count Estimate", "value": 2500, "dataType": "int"}
  ]
}
```

## Guidelines

- Analyze the ACTUAL text provided - do NOT use placeholder values
- Write detailed, specific analysis referencing the source content
- Rate scores 1-10 based on your analysis
- Use markdown formatting: ## Headers, **bold**, *italic*, - lists
- Include specific examples and quotes from the text
- Focus on what happens, who does it, and why it matters
```

**Step 2: Commit**

```bash
git add plugins/chapterwise-analysis/modules/summary.md
git commit -m "feat(analyze): add summary analysis module"
```

---

### Task 7: Characters Module

**Files:**
- Create: `plugins/chapterwise-analysis/modules/characters.md`

**Step 1: Write characters.md**

```markdown
---
name: characters
displayName: Character Analysis
description: Identifies characters, analyzes their roles, motivations, and development
category: Characters
icon: ph ph-users
applicableTypes: []
---

# Character Analysis Module

You are an expert literary analyst specializing in Character Analysis.

## Your Task

Analyze the provided content and identify all characters, examining:

1. **Character Identification** - Who appears in this content
2. **Roles & Functions** - Each character's narrative role
3. **Motivations** - What drives each character
4. **Relationships** - How characters interact with each other
5. **Development** - How characters change or grow

## Output Format

Return your analysis as a JSON object with this structure:

```json
{
  "body": "## Character Analysis\n\n[Overview of characters in this content, their significance, and dynamics]\n\n### Main Characters\n[Analysis of protagonists and key figures]\n\n### Supporting Characters\n[Analysis of secondary characters]",
  "summary": "[Brief overview of key characters and their roles in this content]",
  "children": [
    {
      "name": "[Character Name]",
      "summary": "[One-line character description]",
      "content": "## [Character Name]\n\n**Role:** [protagonist/antagonist/supporting/minor]\n\n**Motivation:** [What drives this character]\n\n**Key Actions:** [What they do in this content]\n\n**Relationships:** [How they relate to others]",
      "attributes": [
        {"key": "role", "name": "Role", "value": "protagonist", "dataType": "string"},
        {"key": "prominence", "name": "Prominence", "value": 9, "dataType": "int"}
      ]
    }
  ],
  "tags": ["characters", "character-analysis", "relationships"],
  "attributes": [
    {"key": "character_count", "name": "Character Count", "value": 5, "dataType": "int"},
    {"key": "pov_character", "name": "POV Character", "value": "Character Name", "dataType": "string"}
  ]
}
```

## Guidelines

- Create a child entry for each significant character
- Rate prominence 1-10 (10 = central to this content)
- Note first appearances of new characters
- Track relationship dynamics
- Identify the POV character if applicable
```

**Step 2: Commit**

```bash
git add plugins/chapterwise-analysis/modules/characters.md
git commit -m "feat(analyze): add characters analysis module"
```

---

### Task 8: Plot Holes Module

**Files:**
- Create: `plugins/chapterwise-analysis/modules/plot-holes.md`

**Step 1: Write plot-holes.md**

```markdown
---
name: plot-holes
displayName: Plot Hole Detection
description: Analyzes narrative logic to identify inconsistencies, gaps, and continuity issues
category: Quality Assessment
icon: ph ph-magnifying-glass
applicableTypes: [novel, short_story, screenplay, theatrical_play]
---

# Plot Hole Detection Module

You are an expert literary analyst specializing in narrative consistency and plot analysis.

## Your Task

Analyze the provided content for:

1. **Logical Gaps** - Events that lack proper explanation or foundation
2. **Character Inconsistencies** - Actions contradicting established behavior
3. **Timeline Issues** - Temporal inconsistencies or impossible timing
4. **Continuity Errors** - Details that change without explanation
5. **Unresolved Threads** - Important elements left hanging

## Output Format

Return your analysis as a JSON object with this structure:

```json
{
  "body": "## Plot Hole Detection\n\n[Overview of narrative consistency in this content]\n\n### Issues Found\n[List and explain each issue]\n\n### Strengths\n[Note areas of strong consistency]",
  "summary": "[Brief assessment of narrative consistency - issues found or clean]",
  "children": [
    {
      "name": "Logical Gaps",
      "summary": "Events lacking proper foundation",
      "content": "## Logical Gaps\n\n[Analysis of any events that happen without proper cause or explanation]",
      "attributes": [
        {"key": "issue_count", "name": "Issues Found", "value": 0, "dataType": "int"},
        {"key": "severity", "name": "Severity", "value": "none", "dataType": "string"}
      ]
    },
    {
      "name": "Character Consistency",
      "summary": "Character behavior alignment",
      "content": "## Character Consistency\n\n[Analysis of whether character actions match their established personality]",
      "attributes": [
        {"key": "issue_count", "name": "Issues Found", "value": 0, "dataType": "int"}
      ]
    },
    {
      "name": "Timeline & Continuity",
      "summary": "Temporal and detail consistency",
      "content": "## Timeline & Continuity\n\n[Analysis of temporal logic and detail consistency]",
      "attributes": [
        {"key": "issue_count", "name": "Issues Found", "value": 0, "dataType": "int"}
      ]
    }
  ],
  "tags": ["plot-holes", "consistency", "quality-assessment"],
  "attributes": [
    {"key": "consistency_score", "name": "Consistency Score", "value": 8, "dataType": "int"},
    {"key": "total_issues", "name": "Total Issues", "value": 2, "dataType": "int"}
  ]
}
```

## Guidelines

- Be thorough but fair - focus on genuine issues
- Distinguish between intentional mysteries and actual plot holes
- Note severity: minor (nitpick), moderate (noticeable), major (breaks immersion)
- If no issues found, explicitly note the strong consistency
- Reference specific text when identifying issues
```

**Step 2: Commit**

```bash
git add plugins/chapterwise-analysis/modules/plot-holes.md
git commit -m "feat(analyze): add plot-holes analysis module"
```

---

### Task 9: Story Beats Module

**Files:**
- Create: `plugins/chapterwise-analysis/modules/story-beats.md`

**Step 1: Write story-beats.md**

```markdown
---
name: story-beats
displayName: Story Beats
description: Identifies key narrative moments, turning points, and structural beats
category: Narrative Structure
icon: ph ph-heartbeat
applicableTypes: []
---

# Story Beats Module

You are an expert literary analyst specializing in narrative structure and story beats.

## Your Task

Analyze the provided content and identify:

1. **Opening Beat** - How the content begins, what hooks the reader
2. **Key Moments** - Significant events that move the story
3. **Turning Points** - Moments where direction or stakes change
4. **Emotional Beats** - Moments designed for emotional impact
5. **Closing Beat** - How the content ends, what it sets up

## Output Format

Return your analysis as a JSON object with this structure:

```json
{
  "body": "## Story Beats\n\n[Overview of narrative rhythm and pacing]\n\n### Beat Sequence\n1. [First major beat]\n2. [Second major beat]\n...",
  "summary": "[Brief description of the narrative arc in this content]",
  "children": [
    {
      "name": "Beat: [Beat Name]",
      "summary": "[What happens in this beat]",
      "content": "## [Beat Name]\n\n**Type:** [opening/inciting/rising/climax/falling/resolution]\n\n**What Happens:** [Description]\n\n**Significance:** [Why this matters]\n\n**Emotional Tone:** [The feeling this creates]",
      "attributes": [
        {"key": "beat_type", "name": "Beat Type", "value": "rising", "dataType": "string"},
        {"key": "intensity", "name": "Intensity", "value": 7, "dataType": "int"},
        {"key": "position", "name": "Position", "value": 1, "dataType": "int"}
      ]
    }
  ],
  "tags": ["story-beats", "structure", "pacing", "narrative"],
  "attributes": [
    {"key": "beat_count", "name": "Beat Count", "value": 5, "dataType": "int"},
    {"key": "pacing_assessment", "name": "Pacing", "value": "well-paced", "dataType": "string"}
  ]
}
```

## Guidelines

- Identify 3-7 key beats depending on content length
- Order children by their position in the narrative
- Rate intensity 1-10 (emotional/dramatic weight)
- Note the pacing: rushed, well-paced, slow, uneven
- Connect beats to larger story arc when possible
```

**Step 2: Commit**

```bash
git add plugins/chapterwise-analysis/modules/story-beats.md
git commit -m "feat(analyze): add story-beats analysis module"
```

---

### Task 10: Critical Review Module

**Files:**
- Create: `plugins/chapterwise-analysis/modules/critical-review.md`

**Step 1: Write critical-review.md**

```markdown
---
name: critical-review
displayName: Critical Review
description: Provides overall quality assessment with strengths, weaknesses, and suggestions
category: Quality Assessment
icon: ph ph-star
applicableTypes: []
---

# Critical Review Module

You are an expert literary critic providing constructive, balanced feedback.

## Your Task

Analyze the provided content and provide:

1. **Overall Assessment** - General quality and effectiveness
2. **Strengths** - What works well and why
3. **Weaknesses** - Areas that could be improved
4. **Craft Elements** - Assessment of prose, dialogue, description
5. **Recommendations** - Specific, actionable suggestions

## Output Format

Return your analysis as a JSON object with this structure:

```json
{
  "body": "## Critical Review\n\n[Overall assessment of the content's quality and effectiveness]\n\n### Verdict\n[2-3 sentence summary of the review]",
  "summary": "[One-line quality assessment]",
  "children": [
    {
      "name": "Strengths",
      "summary": "What works well",
      "content": "## Strengths\n\n[Detailed analysis of what the content does well, with specific examples]",
      "attributes": [
        {"key": "count", "name": "Strengths Identified", "value": 3, "dataType": "int"}
      ]
    },
    {
      "name": "Areas for Improvement",
      "summary": "What could be better",
      "content": "## Areas for Improvement\n\n[Constructive critique with specific examples and reasoning]",
      "attributes": [
        {"key": "count", "name": "Issues Identified", "value": 2, "dataType": "int"}
      ]
    },
    {
      "name": "Craft Assessment",
      "summary": "Technical writing quality",
      "content": "## Craft Assessment\n\n**Prose:** [Assessment of sentence-level writing]\n\n**Dialogue:** [Assessment of character speech]\n\n**Description:** [Assessment of scene-setting and imagery]\n\n**Voice:** [Assessment of narrative voice]",
      "attributes": [
        {"key": "prose_score", "name": "Prose", "value": 7, "dataType": "int"},
        {"key": "dialogue_score", "name": "Dialogue", "value": 8, "dataType": "int"},
        {"key": "description_score", "name": "Description", "value": 6, "dataType": "int"}
      ]
    },
    {
      "name": "Recommendations",
      "summary": "Actionable suggestions",
      "content": "## Recommendations\n\n1. [Specific, actionable suggestion]\n2. [Another suggestion]\n3. [Third suggestion]",
      "attributes": [
        {"key": "priority", "name": "Top Priority", "value": "Focus on X", "dataType": "string"}
      ]
    }
  ],
  "tags": ["critical-review", "quality", "feedback", "craft"],
  "attributes": [
    {"key": "overall_score", "name": "Overall Score", "value": 7, "dataType": "int"},
    {"key": "recommendation", "name": "Recommendation", "value": "Solid draft, needs polish", "dataType": "string"}
  ]
}
```

## Guidelines

- Be constructive - critique should help, not discourage
- Balance strengths and weaknesses fairly
- Provide specific examples from the text
- Make recommendations actionable and specific
- Score 1-10 where 5 is competent, 7 is good, 9+ is exceptional
- Consider the apparent intent and genre of the content
```

**Step 2: Commit**

```bash
git add plugins/chapterwise-analysis/modules/critical-review.md
git commit -m "feat(analyze): add critical-review analysis module"
```

---

### Task 11: Main Analysis Command

**Files:**
- Modify: `plugins/chapterwise-analysis/commands/analysis.md`

**Step 1: Write the full analysis.md command**

```markdown
---
description: Run AI analysis on Codex files (ChapterWise Analysis)
allowed-tools: Read, Grep, Glob, Bash, Write, Edit, AskUserQuestion, Task
triggers:
  # Primary (branded - discoverable via /chapterwise)
  - chapterwise:analysis
  - chapterwise:analysis summary
  - chapterwise:analysis characters
  - chapterwise:analysis plot-holes
  - chapterwise:analysis story-beats
  - chapterwise:analysis critical-review
  - chapterwise:analysis list
  - chapterwise:analysis help
  # Shortcuts (power users)
  - analysis
  - analysis summary
  - analysis characters
  - analysis plot-holes
  - analysis story-beats
  - analysis critical-review
  - analysis list
  - analysis help
---

# ChapterWise Analysis Command

Run AI-powered literary analysis on Codex files. Results are saved to sibling `.analysis.codex.yaml` files.

## Usage

```bash
# Branded (discoverable - type /chapterwise to see all)
/chapterwise:analysis                 # Interactive module picker
/chapterwise:analysis summary         # Direct analysis
/chapterwise:analysis list            # Show available modules

# Shortcuts (power users)
/analysis                             # Interactive module picker
/analysis <module> [file]             # Direct analysis
/analysis list                        # Show available modules
/analysis help <module>               # Module details
```

## Command Routing

When this command is invoked, determine the action:

### `/analyze` (no arguments)
Show interactive module picker using AskUserQuestion:

1. First, discover available modules by running:
   ```bash
   python3 ${CLAUDE_PLUGIN_ROOT}/scripts/module_loader.py list
   ```

2. Group modules by category and present picker:
   - Use AskUserQuestion with multiSelect: true
   - Group by category (max 4 options per question, so may need category-first)
   - After selection, ask for target file if not obvious from context

3. Run selected module(s) on target file(s)

### `/analyze list`
Print formatted list of all available modules:

```
Analysis Modules

  Narrative Structure
  ├─ summary        Chapter summaries with key events
  └─ story-beats    Key moments and turning points

  Characters
  └─ characters     Character identification and analysis

  Quality Assessment
  ├─ plot-holes     Inconsistencies and narrative gaps
  └─ critical-review Overall quality feedback
```

### `/analyze help <module>`
Show detailed information about a specific module.

### `/analyze <module> [file]`
Direct analysis execution:

1. **Check staleness** (unless --force):
   ```bash
   python3 ${CLAUDE_PLUGIN_ROOT}/scripts/staleness_checker.py <file> <module>
   ```
   If `isStale: false`, show existing analysis and ask if user wants to re-run.

2. **Read source content**:
   - Read the target `.codex.yaml` file
   - If `--node <id>` specified, extract that node's content

3. **Load module prompt**:
   - Get module from: `${CLAUDE_PLUGIN_ROOT}/modules/<module>.md`
   - Parse the prompt content after frontmatter

4. **Run analysis**:
   - For single file: Run inline in current conversation
   - For multiple files (--all, --glob): Spawn Task agents in parallel

5. **Save results**:
   ```bash
   echo '<analysis_json>' | python3 ${CLAUDE_PLUGIN_ROOT}/scripts/analysis_writer.py <file> <module> -
   ```

6. **Report results**:
   - Show summary of analysis
   - Note where results were saved
   - Flag if any staleness detected

## Execution Flow for Single File Analysis

```
1. Parse command arguments
2. Validate target file exists and is .codex.yaml
3. Check staleness (skip if fresh unless --force)
4. Read source file content
5. Load module prompt
6. Run analysis (Claude processes content with module prompt)
7. Parse response as JSON
8. Write to .analysis.codex.yaml via analysis_writer.py
9. Report completion
```

## Execution Flow for Batch Analysis

When `--all` or `--glob` specified:

```
1. Find all matching .codex.yaml files
2. Check staleness for each
3. Filter to stale files (unless --force)
4. For each file, spawn a Task agent with:
   - subagent_type: "general-purpose"
   - prompt: "Analyze <file> with <module> module, save results"
5. Collect results
6. Report summary
```

## Flags

| Flag | Description |
|------|-------------|
| `--force` | Re-run even if existing analysis is fresh |
| `--node <id>` | Analyze specific node within file |
| `--all` | Analyze all .codex.yaml files in project |
| `--glob "<pattern>"` | Analyze files matching glob pattern |
| `--history-depth <n>` | Override history retention (default: 3) |
| `--dry-run` | Show what would be analyzed without running |

## Analysis Prompt Template

When running analysis, construct the prompt as:

```
[Module system prompt from .md file]

## Content to Analyze

[Source file content or node content]

## Instructions

Analyze this content according to the module guidelines above.
Return your analysis as a JSON object matching the specified output format.
```

## Error Handling

- If module not found: List available modules
- If file not found: Show error, suggest glob patterns
- If JSON parse fails: Retry once with explicit format reminder
- If write fails: Show error, output JSON to console as fallback
```

**Step 2: Commit**

```bash
git add plugins/chapterwise-analysis/commands/analyze.md
git commit -m "feat(analyze): implement main analyze command"
```

---

### Task 12: Subagent Orchestration

**Files:**
- Modify: `plugins/chapterwise-analysis/commands/analyze.md`

**Purpose:** Leverage Claude Code's Task system for parallel processing of batch analysis.

**Step 1: Add subagent orchestration logic to analyze.md**

Add this section to the command:

```markdown
## Subagent Orchestration

Use Claude Code's Task tool for parallel execution when processing multiple targets.

### When to spawn subagents:

| Scenario | Execution |
|----------|-----------|
| Single file, single module | Inline (current conversation) |
| Single file, multiple modules | Spawn 1 Task per module (parallel) |
| Multiple files (`--all`, `--glob`) | Spawn 1 Task per file (parallel) |
| Large file with many nodes | Spawn 1 Task per node (parallel) |

### Task structure for batch analysis:

When `/analyze summary characters --all` is invoked:

1. Find all `.codex.yaml` files
2. Check staleness for each
3. For each stale file, spawn a Task:

```javascript
Task({
  subagent_type: "general-purpose",
  description: "Analyze chapter-1.codex.yaml",
  prompt: `
    You are running analysis for the chapterwise-analysis plugin.

    1. Read file: ${filePath}
    2. Run these modules: ${modules.join(', ')}
    3. For each module:
       - Load prompt from: ${CLAUDE_PLUGIN_ROOT}/modules/${module}.md
       - Analyze the content
       - Save via: python3 ${CLAUDE_PLUGIN_ROOT}/scripts/analysis_writer.py
    4. Report completion status
  `
})
```

4. Wait for all Tasks to complete
5. Aggregate results and report summary

### Parallel execution example:

```
/analyze summary characters plot-holes --all

Main thread:
├─ Find 5 .codex.yaml files
├─ Spawn 5 Tasks in parallel:
│   ├─ Task 1: "Analyze chapter-1.codex.yaml with 3 modules"
│   ├─ Task 2: "Analyze chapter-2.codex.yaml with 3 modules"
│   ├─ Task 3: "Analyze chapter-3.codex.yaml with 3 modules"
│   ├─ Task 4: "Analyze chapter-4.codex.yaml with 3 modules"
│   └─ Task 5: "Analyze chapter-5.codex.yaml with 3 modules"
├─ Collect results
└─ Report: "Analyzed 5 files with 3 modules each (15 total)"
```
```

**Step 2: Commit**

```bash
git add plugins/chapterwise-analysis/commands/analyze.md
git commit -m "feat(analyze): add subagent orchestration for batch processing"
```

---

### Task 13: Custom Module Template

**Files:**
- Create: `plugins/chapterwise-analysis/modules/_template.md`

**Step 1: Create template file**

```markdown
---
name: my-analysis              # Required: unique identifier (kebab-case)
displayName: My Custom Analysis # Required: shown in picker
description: Brief description of what this module analyzes
category: Custom               # Groups in picker (use existing or create new)
icon: ph ph-lightbulb          # Phosphor icon class (see phosphoricons.com)
applicableTypes: []            # Empty = all types, or [novel, screenplay, etc.]
---

# [Module Name] Analysis

You are an expert analyst specializing in [your domain].

## Your Task

Analyze the provided content for:
1. [First thing to analyze]
2. [Second thing to analyze]
3. [Third thing to analyze]

## Output Format

Return your analysis as a JSON object with this structure:

```json
{
  "body": "## [Module Name]\n\n[Main analysis in markdown - be detailed and specific]",
  "summary": "[One-line summary of your findings]",
  "children": [
    {
      "name": "[Section Name]",
      "summary": "[Section summary]",
      "content": "## [Section]\n\n[Detailed analysis for this section]",
      "attributes": [
        {"key": "score", "name": "Score", "value": 7, "dataType": "int"}
      ]
    }
  ],
  "tags": ["my-analysis", "relevant-tag"],
  "attributes": [
    {"key": "overall_score", "name": "Overall Score", "value": 7, "dataType": "int"}
  ]
}
```

## Guidelines

- Analyze the ACTUAL text provided - never use placeholder values
- Be specific - reference the source content directly
- Use markdown formatting in body/content fields
- Score attributes 1-10 based on your analysis
- Include 2-5 children sections for detailed breakdowns
```

**Step 2: Commit**

```bash
git add plugins/chapterwise-analysis/modules/_template.md
git commit -m "docs(analyze): add custom module template for user extensions"
```

---

### Task 14: Update Marketplace.json

**Files:**
- Modify: `.claude-plugin/marketplace.json`

**Step 1: Add chapterwise-analysis plugin entry**

```json
{
  "name": "chapterwise-plugins",
  "owner": {
    "name": "Anson Phong",
    "email": "phong@phong.com"
  },
  "metadata": {
    "version": "1.0.0",
    "description": "ChapterWise plugins for Claude Code"
  },
  "plugins": [
    {
      "name": "codex",
      "description": "Skills for creating, validating, and managing Chapterwise Codex documents",
      "version": "1.0.0",
      "source": "./plugins/chapterwise-codex",
      "tags": ["codex", "yaml", "document-management", "storytelling"],
      "category": "productivity"
    },
    {
      "name": "chapterwise",
      "description": "Chapterwise functions for Claude Code",
      "version": "1.0.0",
      "source": "./plugins/chapterwise",
      "tags": ["codex", "manuscript", "notes", "insertion", "storytelling"],
      "category": "productivity"
    },
    {
      "name": "analyze",
      "description": "AI-powered literary analysis for Codex files",
      "version": "1.0.0",
      "source": "./plugins/chapterwise-analysis",
      "tags": ["analysis", "writing", "feedback", "storytelling", "ai"],
      "category": "productivity"
    }
  ]
}
```

**Step 2: Commit**

```bash
git add .claude-plugin/marketplace.json
git commit -m "feat: add chapterwise-analysis to marketplace, rename codex"
```

---

### Task 15: Update Plugin Namespaces

**Files:**
- Modify: `plugins/chapterwise-codex/.claude-plugin/plugin.json`
- Verify: All command triggers use short namespace

**Step 1: Rename chapterwise-codex to codex**

Update `plugins/chapterwise-codex/.claude-plugin/plugin.json`:
```json
{
  "name": "codex",
  ...
}
```

**Step 2: Verify all commands use `/codex` namespace**

Check all command files in `plugins/chapterwise-codex/commands/` have triggers like:
- `codex format` (not `chapterwise-codex format`)
- `codex explode`
- `codex implode`
- etc.

**Step 3: Commit**

```bash
git add plugins/chapterwise-codex/
git commit -m "refactor(codex): use short /codex namespace"
```

---

### Task 16: End-to-End Test

**Files:** None (testing only)

**Step 1: Test module discovery**

```bash
cd plugins/chapterwise-analysis
python3 scripts/module_loader.py list
```
Expected: JSON array with 5 modules

**Step 2: Test staleness checker**

```bash
python3 scripts/staleness_checker.py /path/to/sample.codex.yaml summary
```
Expected: JSON with `isStale: true`

**Step 3: Test analyze command**

```bash
claude /analyze list
```
Expected: Formatted module list

```bash
claude /analyze summary /path/to/sample.codex.yaml
```
Expected: Analysis runs, creates `.analysis.codex.yaml`

**Step 4: Test skip-if-fresh**

```bash
claude /analyze summary /path/to/sample.codex.yaml
```
Expected: Shows existing analysis, asks if re-run wanted

**Step 5: Test batch with subagents**

```bash
claude /analyze summary --all
```
Expected: Spawns parallel Tasks for each file

**Step 6: Final commit**

```bash
git add -A
git commit -m "test(analyze): verify end-to-end analysis flow"
```

---

## Verification Checklist

- [ ] `python3 scripts/module_loader.py list` returns 5 modules
- [ ] `python3 scripts/staleness_checker.py <file>` returns valid JSON
- [ ] `/analyze list` displays formatted module list
- [ ] `/analyze summary <file>` creates `.analysis.codex.yaml`
- [ ] `/analyze` (no args) shows category picker
- [ ] `/analyze summary` (no file) auto-detects .codex.yaml files
- [ ] `--node chapter-3` extracts and analyzes specific node
- [ ] Second run detects fresh analysis and prompts
- [ ] `--force` flag bypasses freshness check
- [ ] History limited to configured depth (default 3)
- [ ] Custom modules in `~/.claude/analyze/modules/` are discovered
- [ ] Custom modules in `.chapterwise/analysis-modules/` are discovered
- [ ] `/analyze summary --all` spawns parallel subagents
- [ ] marketplace.json lists all 3 plugins with correct namespaces
- [ ] `/codex format` works (short namespace)
- [ ] `/analyze summary` works (short namespace)

---

## Plugin Namespaces (Final)

**Primary namespace:** `/chapterwise:*` for all tools (branded, discoverable)
**Shortcuts:** Short aliases for power users

| Plugin | Primary (Branded) | Shortcut | Examples |
|--------|-------------------|----------|----------|
| chapterwise-analysis | `/chapterwise:analysis` | `/analysis` | `/chapterwise:analysis summary`, `/analysis summary` |
| chapterwise-codex | `/chapterwise:codex` | `/codex` | `/chapterwise:codex format`, `/codex format` |
| chapterwise | `/chapterwise` | - | `/chapterwise:insert` |

**Discoverability:** Type `/chapterwise` to see all ChapterWise tools:
```
/chapterwise:analysis
/chapterwise:codex
/chapterwise:insert
/chapterwise:notes
```

**Trigger configuration** (in each command's frontmatter):
```yaml
triggers:
  - chapterwise:analysis           # Primary (branded)
  - chapterwise:analysis summary   # With module
  - analysis                       # Shortcut
  - analysis summary               # Shortcut with module
```

---

## Future Enhancements (Post v1.0)

- Add remaining 25+ analysis modules from ChapterWise app
- Add `--background` flag for async batch processing
- Add `--json` flag to output results to stdout
- Per-module config overrides
- Consider `gum`/`fzf` integration for richer TUI
- GitHub Action for CI/CD analysis in PRs
