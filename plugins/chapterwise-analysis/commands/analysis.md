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

# Analysis Command (Stub)

This command will be fully implemented in subsequent tasks.

Run AI-powered literary analysis on Codex files. Results are saved to sibling `.analysis.codex.yaml` files.

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
