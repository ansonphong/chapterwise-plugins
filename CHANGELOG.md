# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-01-25

### Added

- Initial release as Claude Code plugin
- **format** skill - Convert content to Chapterwise Codex V1.2 format
  - Auto-fixer for common integrity issues
  - UUID generation and validation
  - Timecode auto-calculation
  - YAML/JSON recovery
- **explode** skill - Extract children into separate files
  - Type-based filtering
  - Custom output patterns
  - Auto-fix on extracted files
- **implode** skill - Merge included files back into parent
  - Recursive include resolution
  - Source file cleanup
  - Empty folder deletion
- **index** skill - Generate project index files
  - Auto-discovery of content
  - Pattern-based include/exclude
  - Display configuration
- **lite** skill - Codex Lite (Markdown with frontmatter)
  - Frontmatter validation
  - Word count calculation
  - Title extraction from H1

### Notes

- Packaged from project-scoped skills at `.claude/skills/chapterwise-codex:*`
- Compatible with Claude Code 1.0.33+
- Requires Python 3.8+ for helper scripts
