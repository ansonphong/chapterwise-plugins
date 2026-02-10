# File Organizer (#30) Hardening Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Harden the File Organizer system against path traversal, symlink following, and broken slug generation for non-hyphen separators.

**Architecture:** Three targeted fixes to `src/fileOrganizer.ts`: (1) add workspace containment check after generating the full path, (2) fix `slugifyName` to preserve separator characters and escape them in regex, (3) add symlink detection before mkdir/write operations. All changes are in a single file.

**Tech Stack:** TypeScript, Node.js `path`/`fs`, VS Code Extension API

---

### Task 1: Add workspace containment check to `createNodeFile`

**Files:**
- Modify: `src/fileOrganizer.ts:46-87`

The function generates a file path from `parentPath` (unvalidated) and then creates directories + writes a file. There is no check that the resulting path stays within the workspace.

**Step 1: Add workspace containment check after computing fullPath**

Replace lines 46-87 of `createNodeFile`:

```typescript
    try {
      // Generate file path based on strategy
      const filePath = this.generateFilePath(
        workspaceRoot,
        parentPath,
        nodeData,
        settings
      );

      const fullPath = path.normalize(path.join(workspaceRoot, filePath));

      // Security check: ensure generated path stays within workspace
      const relative = path.relative(workspaceRoot, fullPath);
      if (relative.startsWith('..') || path.isAbsolute(relative)) {
        return {
          success: false,
          message: `Generated path escapes workspace: ${filePath}`
        };
      }

      // Check if file already exists
      if (fs.existsSync(fullPath)) {
        return {
          success: false,
          message: `File already exists: ${path.basename(filePath)}`
        };
      }

      // Symlink check: verify parent directory isn't a symlink
      const dir = path.dirname(fullPath);
      if (fs.existsSync(dir)) {
        try {
          const dirStat = fs.lstatSync(dir);
          if (dirStat.isSymbolicLink()) {
            return {
              success: false,
              message: `Parent directory is a symlink: ${path.basename(dir)}`
            };
          }
        } catch {
          // lstat failed - proceed with caution
        }
      }

      // Create directory if needed
      if (!fs.existsSync(dir)) {
        fs.mkdirSync(dir, { recursive: true });
      }

      // Create file with initial content
      const content = this.generateInitialContent(nodeData, settings);
      fs.writeFileSync(fullPath, content, 'utf-8');

      return {
        success: true,
        filePath: filePath,
        fileUri: vscode.Uri.file(fullPath),
        message: `Created ${path.basename(filePath)}`
      };
    } catch (error) {
      return {
        success: false,
        message: `Failed to create file: ${error}`
      };
    }
```

This adds:
1. `path.normalize()` on fullPath to resolve `..` segments before the check
2. Workspace containment via `path.relative()` + `startsWith('..')` + `path.isAbsolute()`
3. Symlink detection on parent directory via `lstatSync().isSymbolicLink()`

**Step 2: Compile and verify**

Run: `cd /Users/phong/Projects/chapterwise-codex && npx tsc --noEmit`
Expected: No new errors

**Step 3: Commit**

```bash
cd /Users/phong/Projects/chapterwise-codex && git add src/fileOrganizer.ts
git commit -m "fix(file-organizer): add workspace containment and symlink checks to createNodeFile"
```

---

### Task 2: Fix `slugifyName` to handle all valid separators correctly

**Files:**
- Modify: `src/fileOrganizer.ts:248-271` (`slugifyName`)

Two compounding bugs: (1) line 260 strips all non-`[a-zA-Z0-9-]` characters, which removes the separator itself when it's `.`, `_`, or ` `. (2) Lines 263, 267 interpolate the separator into `RegExp` without escaping, so `.` becomes a wildcard matching any character, destroying the entire slug.

**Step 1: Fix slugifyName to preserve and escape the separator**

Replace lines 248-271:

```typescript
  private slugifyName(name: string, namingSettings: NavigatorSettings['naming']): string {
    let slug = name;
    const sep = namingSettings.separator;

    // Escape separator for use in regex
    const escapedSep = sep.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');

    // Convert to lowercase unless preserving case
    if (!namingSettings.preserveCase) {
      slug = slug.toLowerCase();
    }

    // Replace spaces and underscores with separator
    slug = slug.replace(/[\s_]+/g, sep);

    // Remove special characters (keep alphanumeric, hyphens, and the separator)
    const allowedCharsPattern = new RegExp(`[^a-zA-Z0-9\\-${escapedSep}]`, 'g');
    slug = slug.replace(allowedCharsPattern, '');

    // Remove leading/trailing separators
    const trimPattern = new RegExp(`^${escapedSep}+|${escapedSep}+$`, 'g');
    slug = slug.replace(trimPattern, '');

    // Collapse multiple separators
    const collapsePattern = new RegExp(`${escapedSep}+`, 'g');
    slug = slug.replace(collapsePattern, sep);

    return slug || 'untitled';
  }
```

Changes:
1. Escape the separator before using in `RegExp` (fixes `.` wildcard issue)
2. Include the separator in the allowed character class on the "remove special characters" line (fixes stripping of `.`, `_`, ` `)

**Step 2: Also fix `getNextAvailableNumber` regex at line 339**

The prefix is interpolated into a regex without escaping. Replace lines 338-339:

```typescript
      // Extract numbers from filenames (escape prefix for regex safety)
      const escapedPrefix = prefix.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
      const pattern = new RegExp(`^${escapedPrefix}-(\\d+)`, 'i');
```

**Step 3: Compile and verify**

Run: `cd /Users/phong/Projects/chapterwise-codex && npx tsc --noEmit`
Expected: No new errors

**Step 4: Commit**

```bash
cd /Users/phong/Projects/chapterwise-codex && git add src/fileOrganizer.ts
git commit -m "fix(file-organizer): fix slugifyName for non-hyphen separators and escape regex interpolation"
```

---

### Task 3: Update META-DEV-PROMPT.md and push

**Files:**
- Modify: `/Users/phong/Projects/chapterwise-app/dev/META-DEV-PROMPT.md:280`

**Step 1: Mark system #30 as complete**

Update the row for system 30 to show completed status with commit hash and date.

**Step 2: Push chapterwise-codex changes**

```bash
cd /Users/phong/Projects/chapterwise-codex && git push
```

**Step 3: Commit and push META-DEV-PROMPT.md**

```bash
cd /Users/phong/Projects/chapterwise-app && git add dev/META-DEV-PROMPT.md && git commit -m "docs: mark File Organizer (#30) hardened" && git push
```
