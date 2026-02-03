---
description: Run AI analysis on Codex files
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

Run AI-powered literary analysis on Codex files. Results are saved to sibling `.analysis.json` files (proper Codex V1.2 format, JSON for fast parsing).

## Usage

```bash
/chapterwise:analysis                 # Interactive module picker
/chapterwise:analysis <module> [file] # Direct analysis
/chapterwise:analysis list            # Show available modules
/chapterwise:analysis help <module>   # Module details

# Shortcuts
/analysis                             # Interactive module picker
/analysis summary mybook.codex.yaml   # Direct analysis
```

## Command Routing

When this command is invoked, determine the action based on the arguments:

### Route: `/analysis` (no arguments) - Interactive Picker

1. **Discover available modules:**
   ```bash
   CLAUDE_PLUGIN_ROOT=${CLAUDE_PLUGIN_ROOT} python3 ${CLAUDE_PLUGIN_ROOT}/scripts/module_loader.py list
   ```

2. **Present category-first picker** using AskUserQuestion:
   - First question: "Which category?" with options: Narrative Structure, Characters, Quality Assessment
   - Second question: Multi-select modules from that category
   - Third question: Target file (if not obvious from context)

3. **Run selected module(s)** on target file(s)

### Route: `/analysis list` - Show Available Modules

Print formatted list of all available modules grouped by category:

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

Use the module_loader.py script to get module data, then format nicely.

### Route: `/analysis help <module>` - Module Details

Show detailed information about a specific module including its description, applicable types, and output format.

### Route: `/analysis <module> [file]` - Direct Analysis

Execute analysis with the specified module:

1. **Resolve target file:**
   - If file provided: Use that file
   - If no file: Look for `.codex.yaml` files in current context
   - If multiple found: Ask user to choose

2. **Check staleness** (unless `--force` flag):
   ```bash
   python3 ${CLAUDE_PLUGIN_ROOT}/scripts/staleness_checker.py <file> <module>
   ```
   - If `isStale: false`: Show existing analysis summary and ask if user wants to re-run
   - If `isStale: true`: Proceed with analysis

3. **Read source content:**
   - Read the target `.codex.yaml` file
   - If `--node <id>` specified: Extract only that node's content
   - Extract the `body` field and any relevant text content

4. **Load module prompt:**
   - Get module from: `${CLAUDE_PLUGIN_ROOT}/modules/<module>.md`
   - Parse the content after frontmatter (the `_content` field from module_loader)

5. **Run analysis:**
   - Construct prompt combining module instructions + source content
   - For single file: Run inline in current conversation
   - For multiple files (`--all`, `--glob`): Spawn Task agents in parallel

6. **Parse and validate response:**
   - Ensure response is valid JSON matching the expected format
   - If parse fails: Retry once with explicit format reminder

7. **Save results:**
   ```bash
   echo '<analysis_json>' | python3 ${CLAUDE_PLUGIN_ROOT}/scripts/analysis_writer.py <file> <module> -
   ```

8. **Report results:**
   - Show summary of analysis findings
   - Note where results were saved
   - Show path to `.analysis.codex.yaml` file

## Analysis Prompt Template

When running analysis, construct the prompt as:

```
[Module system prompt from .md file]

---

## Content to Analyze

<source_content>
[Full content of the source file or node]
</source_content>

---

## Instructions

Analyze the content above according to the module guidelines.

CRITICAL: Return ONLY a valid JSON object. No markdown code blocks, no explanation text.
The JSON must match the exact structure specified in the Output Format section above.
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

## Batch Analysis with Subagents

When `--all` or `--glob` is specified:

1. Find all matching `.codex.yaml` files using Glob tool
2. Check staleness for each file/module combination
3. Filter to only stale files (unless `--force`)
4. For each file, spawn a Task agent:
   ```
   Task(
     subagent_type="general-purpose",
     prompt="Run /analysis <module> on <file> and save results. Report the summary when done.",
     run_in_background=true
   )
   ```
5. Collect and summarize results from all agents

## Error Handling

- **Module not found:** List available modules with `/analysis list`
- **File not found:** Show error, suggest using Glob to find files
- **JSON parse fails:** Retry once with explicit format reminder
- **Write fails:** Show error, output JSON to console as fallback
- **No .codex.yaml files:** Inform user no valid targets found

## Examples

```bash
# Analyze a specific file
/analysis summary manuscript.codex.yaml

# Run multiple modules
/analysis summary characters manuscript.codex.yaml

# Analyze all codex files in project
/analysis summary --all

# Force re-analysis even if fresh
/analysis summary --force manuscript.codex.yaml

# Dry run to see what would be analyzed
/analysis summary --dry-run --all
```
