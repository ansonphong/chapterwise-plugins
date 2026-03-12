# Rules: Codex Format

Applies when creating or modifying codex output files (`.codex.yaml`, `.codex.md`, `.analysis.json`, `.research.json`).

## Codex V1.2 JSON Structure

```json
{
  "metadata": { "formatVersion": "1.2", "created": "ISO-8601", "updated": "ISO-8601" },
  "id": "unique-slug",
  "type": "chapter|analysis|research|atlas|...",
  "name": "Display Name",
  "summary": "One-line description",
  "body": "Markdown content",
  "attributes": [{ "key": "name", "value": "val", "dataType": "string" }],
  "tags": ["keyword"],
  "children": [],
  "relations": [{ "target": "other-id", "type": "references" }]
}
```

## Codex Lite (Markdown) Structure

```markdown
---
type: document
summary: "Brief description"
tags: tag1, tag2
status: draft
---

# Title

Content in standard Markdown...
```

## Validation

- Always run `codex_validator.py` after generating codex output
- Schema files live in `schemas/` (codex-v1.2.schema.json, analysis-v1.2.schema.json)
- Silent on success — only report auto-fixes and unfixable issues
