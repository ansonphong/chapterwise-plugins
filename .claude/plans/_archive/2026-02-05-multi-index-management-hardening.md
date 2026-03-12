# Multi-Index Management (#26) Hardening Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Harden the Multi-Index Management system against path traversal, symlink following, unbounded recursion, and incorrect path matching.

**Architecture:** Five targeted fixes across two files: `indexParser.ts` (path traversal + symlink + depth limit in `resolveSubIndexIncludes`) and `multiIndexManager.ts` (path traversal in `collectCoveredPaths`/`calculateOrphans` + path-boundary-aware matching in `isClaimedBySubIndex`).

**Tech Stack:** TypeScript, Node.js `path`/`fs`, VS Code Extension API

---

### Task 1: Add workspace containment and symlink checks to `resolveSubIndexIncludes`

**Files:**
- Modify: `src/indexParser.ts:297-404` (`resolveSubIndexIncludes`)
- Modify: `src/indexParser.ts:414-434` (`parseIndexFileWithIncludes`)

This is the highest-priority fix. The function resolves include paths with `path.resolve()` but has NO workspace containment check, NO symlink check, and NO depth limit. Three vulnerabilities in one function.

**Step 1: Add `workspaceRoot` and `depth` parameters to `resolveSubIndexIncludes`**

Add `workspaceRoot: string` and `depth: number = 0` parameters, add a `MAX_SUB_INDEX_DEPTH` constant, and thread them through. Replace lines 297-404:

```typescript
const MAX_SUB_INDEX_DEPTH = 8;

export function resolveSubIndexIncludes(
  children: any[],
  parentDir: string,
  workspaceRoot: string,
  parsedIndexes: Set<string> = new Set(),
  depth: number = 0
): IndexChildNode[] {
  // Depth limit to prevent stack overflow from deep non-circular chains
  if (depth >= MAX_SUB_INDEX_DEPTH) {
    console.warn(`[IndexParser] Max sub-index depth ${MAX_SUB_INDEX_DEPTH} reached, stopping resolution`);
    return [];
  }

  const resolved: IndexChildNode[] = [];

  for (const child of children) {
    if (isIncludeDirective(child)) {
      const includePath = child.include;

      if (isSubIndexInclude(includePath)) {
        // Load and merge sub-index
        const subIndexPath = path.resolve(parentDir, includePath);
        const normalizedPath = path.normalize(subIndexPath);

        // Security check: ensure resolved path is within workspace
        const relative = path.relative(workspaceRoot, normalizedPath);
        if (relative.startsWith('..') || path.isAbsolute(relative)) {
          console.warn(`[IndexParser] Sub-index path escapes workspace: ${includePath}`);
          continue;
        }

        // Circular reference check
        if (parsedIndexes.has(normalizedPath)) {
          console.warn(`[IndexParser] Circular sub-index reference detected: ${subIndexPath}`);
          continue;
        }

        // Symlink check: skip symlinks to prevent reading outside workspace
        try {
          const stat = fs.lstatSync(subIndexPath);
          if (stat.isSymbolicLink()) {
            console.warn(`[IndexParser] Skipping symlink sub-index: ${subIndexPath}`);
            continue;
          }
        } catch {
          // File doesn't exist - fall through to existsSync check below
        }

        if (fs.existsSync(subIndexPath)) {
          // Add to parsed set before parsing (prevent infinite recursion)
          parsedIndexes.add(normalizedPath);
          try {
            const subContent = fs.readFileSync(subIndexPath, 'utf-8');
            let subData: any;

            if (subIndexPath.endsWith('.json')) {
              subData = JSON.parse(subContent);
            } else {
              subData = YAML.parse(subContent);
            }

            if (subData && typeof subData === 'object') {
              // Get directory name for correct path computation
              const dirName = path.basename(path.dirname(subIndexPath));

              // Merge sub-index as a node
              const subNode: IndexChildNode = {
                id: subData.id || dirName,
                type: subData.type || 'folder',
                name: subData.name || dirName,
                // IMPORTANT: Set _filename to directory name for correct path computation
                // This ensures paths like "book-1/chapters/..." instead of "Book One/chapters/..."
                _filename: dirName,
                _subindex_path: subIndexPath, // Renamed from _included_from for web app parity
              };

              // Copy optional fields
              if (subData.summary) {subNode.title = subData.summary;}
              if (subData.emoji) {subNode.emoji = subData.emoji;}
              if (subData.scrivener_label) {
                subNode.attributes = [{ key: 'scrivener_label', value: subData.scrivener_label }];
              }

              // Recursively resolve sub-index children
              if (subData.children && Array.isArray(subData.children)) {
                subNode.children = resolveSubIndexIncludes(
                  subData.children,
                  path.dirname(subIndexPath),
                  workspaceRoot,
                  parsedIndexes,
                  depth + 1
                );
              }

              resolved.push(subNode);
            }
          } catch (error) {
            console.error(`[IndexParser] Failed to load sub-index ${subIndexPath}:`, error);
          }
        } else {
          console.warn(`[IndexParser] Sub-index not found: ${subIndexPath}`);
        }
      } else {
        // Regular file include (e.g., ./chapter-01.md)
        const resolvedIncludePath = path.resolve(parentDir, includePath);
        const normalizedIncludePath = path.normalize(resolvedIncludePath);

        // Security check: ensure resolved path is within workspace
        const relative = path.relative(workspaceRoot, normalizedIncludePath);
        if (relative.startsWith('..') || path.isAbsolute(relative)) {
          console.warn(`[IndexParser] Include path escapes workspace: ${includePath}`);
          continue;
        }

        // Convert to a basic node with include path as filename
        const fileName = path.basename(includePath);
        const ext = path.extname(fileName);
        const baseName = path.basename(fileName, ext);

        resolved.push({
          id: `file-${baseName}`,
          type: 'document', // Will be refined by content parsing
          name: baseName.replace(/-/g, ' ').replace(/\b\w/g, c => c.toUpperCase()),
          _filename: fileName,
          _subindex_path: normalizedIncludePath,
          _format: ext === '.md' ? 'markdown' : ext === '.yaml' ? 'yaml' : 'json',
        });
      }
    } else if (child && typeof child === 'object') {
      // Regular node - copy and recurse if has children
      const node: IndexChildNode = { ...child };

      if (child.children && Array.isArray(child.children)) {
        // Determine directory for nested children
        const childDir = child._filename
          ? path.join(parentDir, path.dirname(child._filename))
          : parentDir;
        node.children = resolveSubIndexIncludes(child.children, childDir, workspaceRoot, parsedIndexes, depth + 1);
      }

      resolved.push(node);
    }
  }

  return resolved;
}
```

**Step 2: Update `parseIndexFileWithIncludes` to pass `workspaceRoot`**

Add `workspaceRoot` parameter and thread it through. Replace lines 414-434:

```typescript
export function parseIndexFileWithIncludes(
  content: string,
  indexDir: string,
  workspaceRoot: string,
  indexPath?: string
): IndexDocument | null {
  const doc = parseIndexFile(content);
  if (!doc) {return null;}

  // Initialize parsed indexes set with current index
  const parsedIndexes = new Set<string>();
  if (indexPath) {
    parsedIndexes.add(path.normalize(indexPath));
  }

  // Resolve any include directives in children
  if (doc.children && Array.isArray(doc.children)) {
    doc.children = resolveSubIndexIncludes(doc.children, indexDir, workspaceRoot, parsedIndexes);
  }

  return doc;
}
```

**Note:** `parseIndexFileWithIncludes` is currently exported but not imported by any other source file. The signature change is safe. If future callers exist, they will get a compile error guiding them to provide `workspaceRoot`.

**Step 3: Compile and verify**

Run: `cd /Users/phong/Projects/chapterwise-codex && npx tsc --noEmit`
Expected: No new errors (pre-existing errors on `extension.ts` lines 152, 159 are OK)

**Step 4: Commit**

```bash
cd /Users/phong/Projects/chapterwise-codex && git add src/indexParser.ts
git commit -m "fix(index-parser): add workspace containment, symlink checks, and depth limit to resolveSubIndexIncludes"
```

---

### Task 2: Add workspace containment to `collectCoveredPaths` and `calculateOrphans`

**Files:**
- Modify: `src/multiIndexManager.ts:104-126` (`collectCoveredPaths`)
- Modify: `src/multiIndexManager.ts:131-164` (`calculateOrphans`)

Both functions resolve `child.include` paths with `path.resolve()` without checking workspace boundaries.

**Step 1: Add workspace containment to `collectCoveredPaths`**

Replace lines 104-126:

```typescript
  /**
   * Recursively collect paths covered by an index
   */
  private collectCoveredPaths(
    children: IndexChildNode[],
    baseDir: string,
    coveredPaths: Set<string>
  ): void {
    if (!children) return;

    for (const child of children) {
      if (child.include) {
        const includePath = path.resolve(baseDir, child.include);
        const normalized = path.normalize(includePath);

        // Security check: only add paths within workspace
        if (this.workspaceRoot) {
          const relative = path.relative(this.workspaceRoot, normalized);
          if (relative.startsWith('..') || path.isAbsolute(relative)) {
            console.warn(`[MultiIndexManager] Include path escapes workspace: ${child.include}`);
            continue;
          }
        }

        coveredPaths.add(normalized);
      }

      if (child.children) {
        this.collectCoveredPaths(child.children, baseDir, coveredPaths);
      }
    }
  }
```

**Step 2: Add workspace containment to `calculateOrphans`**

Replace lines 131-164:

```typescript
  /**
   * Calculate orphan files (not covered by any sub-index)
   */
  private calculateOrphans(): void {
    if (!this.workspaceRoot) return;

    // Find the master index (at workspace root)
    const masterIndexPath = path.join(this.workspaceRoot, 'index.codex.yaml');
    const masterIndex = this.discoveredIndexes.get(masterIndexPath);

    if (!masterIndex) {
      this.masterOrphans = [];
      return;
    }

    // Get all children from master index
    const masterChildren = masterIndex.document.children || [];

    // Filter to only orphans
    this.masterOrphans = masterChildren
      .filter(child => {
        // Skip sub-index includes
        if (child.include?.endsWith('index.codex.yaml')) {
          return false;
        }

        // Check if any sub-index claims this path
        if (!child.include) return true; // Inline children are orphans

        const childPath = path.resolve(this.workspaceRoot!, child.include);
        const normalized = path.normalize(childPath);

        // Security check: skip paths outside workspace
        const relative = path.relative(this.workspaceRoot!, normalized);
        if (relative.startsWith('..') || path.isAbsolute(relative)) {
          console.warn(`[MultiIndexManager] Orphan path escapes workspace: ${child.include}`);
          return false;
        }

        return !this.isClaimedBySubIndex(normalized);
      })
      .map(child => child.include || child.name);
  }
```

**Step 3: Compile and verify**

Run: `cd /Users/phong/Projects/chapterwise-codex && npx tsc --noEmit`
Expected: No new errors

**Step 4: Commit**

```bash
cd /Users/phong/Projects/chapterwise-codex && git add src/multiIndexManager.ts
git commit -m "fix(multi-index): add workspace containment to collectCoveredPaths and calculateOrphans"
```

---

### Task 3: Fix path-boundary-aware matching in `isClaimedBySubIndex`

**Files:**
- Modify: `src/multiIndexManager.ts:169-183` (`isClaimedBySubIndex`)

The current `filePath.startsWith(coveredPath)` is not path-boundary aware. `/workspace/book1` incorrectly matches `/workspace/book1-appendix`.

**Step 1: Replace string prefix match with `path.relative()` check**

Replace lines 169-183:

```typescript
  /**
   * Check if a path is claimed by any sub-index
   */
  private isClaimedBySubIndex(filePath: string): boolean {
    for (const [indexPath, index] of this.discoveredIndexes) {
      // Skip the master index itself
      if (indexPath === path.join(this.workspaceRoot!, 'index.codex.yaml')) {
        continue;
      }

      for (const coveredPath of index.coveredPaths) {
        // Use path.relative for path-boundary-aware comparison
        // A file is "under" a covered path if relative doesn't start with '..'
        const relative = path.relative(coveredPath, filePath);
        if (!relative.startsWith('..') && !path.isAbsolute(relative)) {
          return true;
        }
      }
    }
    return false;
  }
```

**Step 2: Compile and verify**

Run: `cd /Users/phong/Projects/chapterwise-codex && npx tsc --noEmit`
Expected: No new errors

**Step 3: Commit**

```bash
cd /Users/phong/Projects/chapterwise-codex && git add src/multiIndexManager.ts
git commit -m "fix(multi-index): use path-boundary-aware matching in isClaimedBySubIndex"
```

---

### Task 4: Update META-DEV-PROMPT.md and push

**Files:**
- Modify: `/Users/phong/Projects/chapterwise-app/dev/META-DEV-PROMPT.md:277`

**Step 1: Mark system #26 as complete**

Update the row for system 26 to show completed status with commit hash and date.

**Step 2: Push chapterwise-codex changes**

```bash
cd /Users/phong/Projects/chapterwise-codex && git push
```

**Step 3: Commit and push META-DEV-PROMPT.md**

```bash
cd /Users/phong/Projects/chapterwise-app && git add dev/META-DEV-PROMPT.md && git commit -m "docs: mark Multi-Index Management (#26) hardened" && git push
```
