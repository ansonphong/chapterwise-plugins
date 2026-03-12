# Index Generation (#23) Hardening Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Harden the Index Generation system against path traversal, symlink following, and unsafe parsing.

**Architecture:** Three targeted fixes to `indexGenerator.ts`: (1) apply workspace containment check to the absolute include path branch, (2) add symlink detection to all three directory-walking functions, (3) replace `YAML.parse()` with `JSON.parse()` for `.index.codex.json` files. All changes are in a single file.

**Tech Stack:** TypeScript, Node.js `path`/`fs`, VS Code Extension API

---

### Task 1: Fix path traversal bypass in `resolveIncludePath` absolute path branch

**Files:**
- Modify: `src/indexGenerator.ts:526-550`

**Step 1: Apply workspace containment to the absolute path branch**

The absolute path branch at line 532-533 returns directly without the security check at lines 544-546. An include like `/../../../etc/passwd` escapes the workspace. Move the security check to cover BOTH branches.

Replace lines 526-550:

```typescript
function resolveIncludePath(
  includePath: string,
  parentFilePath: string,
  workspaceRoot: string
): string {
  let resolved: string;

  if (includePath.startsWith('/')) {
    // Absolute path: resolve from workspace root
    resolved = path.join(workspaceRoot, includePath.substring(1));
  } else {
    // Relative path: resolve from parent file's directory
    const parentDir = path.dirname(parentFilePath);
    resolved = path.resolve(parentDir, includePath);
  }

  // Normalize to remove .. and . segments
  const normalized = path.normalize(resolved);

  // Security check: ensure resolved path is within workspace (covers BOTH branches)
  const relative = path.relative(workspaceRoot, normalized);
  if (relative.startsWith('..') || path.isAbsolute(relative)) {
    throw new Error(`Include path escapes workspace root: ${includePath}`);
  }

  return normalized;
}
```

**Step 2: Compile and verify**

Run: `cd /Users/phong/Projects/chapterwise-codex && npm run compile`
Expected: No new errors

**Step 3: Commit**

```bash
git add src/indexGenerator.ts
git commit -m "fix(index-gen): apply workspace containment to absolute include paths"
```

---

### Task 2: Add symlink detection to all directory-walking functions

**Files:**
- Modify: `src/indexGenerator.ts:238-259` (`walkDir`)
- Modify: `src/indexGenerator.ts:1185-1202` (`generatePerFolderIndex` entry loop)
- Modify: `src/indexGenerator.ts:1336-1352` (`collectSubfolders`)

**Step 1: Add symlink skip to `walkDir` in `scanWorkspace`**

At line 241, before the exclude check, add a symlink guard. Replace the for-loop body (lines 241-257):

```typescript
        for (const entry of entries) {
      // Skip symlinks to prevent scanning outside workspace
      if (entry.isSymbolicLink()) {
        log(`[scanWorkspace] Skipping symlink: ${entry.name}`);
        continue;
      }

      const fullPath = path.join(dir, entry.name);
      const relativePath = path.relative(root, fullPath);

      // Check exclude patterns first
      if (shouldExclude(relativePath, patterns.exclude)) {
            continue;
          }

          if (entry.isDirectory()) {
        walkDir(fullPath);
          } else if (entry.isFile()) {
        // Check include patterns
        if (shouldInclude(entry.name, patterns.include)) {
              files.push(fullPath);
            }
          }
        }
```

**Step 2: Add symlink skip to `collectSubfolders`**

At line 1343, add symlink guard before the directory check. Replace the for-loop body (lines 1343-1347):

```typescript
      for (const entry of entries) {
        // Skip symlinks to prevent traversal outside workspace
        if (entry.isSymbolicLink()) {
          log(`[IndexGenerator] Skipping symlink during folder collection: ${entry.name}`);
          continue;
        }
        if (entry.isDirectory() && !entry.name.startsWith('.')) {
          const subfolder = path.join(folderPath, entry.name);
          collectSubfolders(subfolder);
      }
    }
```

**Step 3: Add symlink skip to `generatePerFolderIndex`**

At line 1185, inside the for-loop, after the hidden-file skip, add a symlink guard. Insert after line 1188:

```typescript
    // Skip symlinks to prevent traversal outside workspace
    if (entry.isSymbolicLink()) {
      log(`[IndexGenerator] Skipping symlink in folder index: ${entry.name}`);
      continue;
    }
```

**Step 4: Compile and verify**

Run: `cd /Users/phong/Projects/chapterwise-codex && npm run compile`
Expected: No new errors

**Step 5: Commit**

```bash
git add src/indexGenerator.ts
git commit -m "fix(index-gen): add symlink detection to all directory-walking functions"
```

---

### Task 3: Replace YAML.parse with JSON.parse for .index.codex.json files

**Files:**
- Modify: `src/indexGenerator.ts:455` (in `mergePerFolderIndexes`)
- Modify: `src/indexGenerator.ts:1229` (in `generatePerFolderIndex`)

**Step 1: Fix `mergePerFolderIndexes` at line 455**

These are `.index.codex.json` files — generated JSON, not YAML. Replace `YAML.parse` with `JSON.parse`:

```typescript
        const indexData = JSON.parse(indexContent);
```

**Step 2: Fix `generatePerFolderIndex` at line 1229**

Same change:

```typescript
          const subIndexData = JSON.parse(subIndexContent);
```

**Step 3: Compile and verify**

Run: `cd /Users/phong/Projects/chapterwise-codex && npm run compile`
Expected: No new errors

**Step 4: Commit**

```bash
git add src/indexGenerator.ts
git commit -m "fix(index-gen): use JSON.parse for .index.codex.json files instead of YAML.parse"
```

---

### Task 4: Update META-DEV-PROMPT.md and push

**Files:**
- Modify: `/Users/phong/Projects/chapterwise-app/dev/META-DEV-PROMPT.md:275`

**Step 1: Mark system #23 as complete**

Update the row for system 23 to show completed status with commit hash and date.

**Step 2: Push chapterwise-codex changes**

```bash
cd /Users/phong/Projects/chapterwise-codex && git push
```

**Step 3: Commit and push META-DEV-PROMPT.md**

```bash
cd /Users/phong/Projects/chapterwise-app && git add dev/META-DEV-PROMPT.md && git commit -m "docs: mark Index Generation (#23) hardened" && git push
```
