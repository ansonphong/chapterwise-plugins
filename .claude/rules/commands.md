# Rules: Writing Commands

Applies when creating or modifying files in `plugins/chapterwise/commands/`.

## Command File Structure

Every command file uses YAML frontmatter:

```yaml
---
description: "Short description for command list"
allowed-tools: Read, Grep, Glob, Bash, Write, Edit, AskUserQuestion
triggers:
  - command-name
  - chapterwise:command-name
argument-hint: "[args]"
---
```

## Conventions

- Triggers must not collide with existing commands — grep all command files for conflicts before adding
- Use `${CLAUDE_PLUGIN_ROOT}` for paths to plugin files (scripts, modules, references)
- Reference `${CLAUDE_PLUGIN_ROOT}/references/principles.md` and `${CLAUDE_PLUGIN_ROOT}/references/language-rules.md`
- Use AskUserQuestion tool for all user-facing decisions — never inline text prompts
- Use Task tool for parallel batch work (3+ modules or 10+ files)
- Include an Error Handling table for all failure cases
- Include a Language Rules table mapping phases to cooking verbs
