#!/usr/bin/env python3
"""
Codex Imploder Service - Merge Included Files Back Into Parent

This service resolves include directives in a codex file, reading the referenced
files and merging their content back into the parent document. This is the
inverse of the Explode operation.

This enables:
- Consolidating modular files back into a single document
- Creating self-contained codex files for distribution
- Simplifying structure when modularity is no longer needed
- Archiving projects with all content inline

Command-line usage:
    python implode_codex.py <input_file> [options]

Examples:
    # Merge all includes back into parent
    python implode_codex.py story.codex.yaml

    # Merge and delete source files
    python implode_codex.py story.codex.yaml --delete-sources

    # Preview what would be merged
    python implode_codex.py story.codex.yaml --dry-run

    # Recursive merge (resolve nested includes)
    python implode_codex.py story.codex.yaml --recursive

    # Delete empty folders after removing source files
    python implode_codex.py story.codex.yaml --delete-sources --delete-empty-folders
"""

import os
import sys
import yaml
import json
import re
import argparse
import logging
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple, Set

# Setup path for standalone execution
if __name__ == '__main__':
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

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

logger = logging.getLogger(__name__)


def is_codex_file(file_path: str) -> bool:
    """Check if a file is a valid codex file based on extension."""
    path = Path(file_path)
    name_lower = path.name.lower()
    return (
        name_lower.endswith('.codex.yaml') or
        name_lower.endswith('.codex.yml') or
        name_lower.endswith('.codex.json') or
        name_lower.endswith('.codex')
    )


class CodexImploder:
    """
    Service to merge included files back into a parent codex file.
    This is the inverse of the Explode operation.
    """

    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.merged_files: List[str] = []
        self.deleted_files: List[str] = []
        self.deleted_folders: List[str] = []
        self.errors: List[str] = []

    def implode(
        self,
        input_path: str,
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Merge included files back into a codex file.

        Args:
            input_path: Path to the input codex file
            options: Additional options:
                - dry_run: bool - Preview without making changes
                - delete_sources: bool - Delete included files after merge
                - delete_empty_folders: bool - Delete folders that become empty
                - recursive: bool - Resolve nested includes
                - backup: bool - Create backup of original file (default: True)
                - verbose: bool - Detailed logging

        Returns:
            Dict with implode results:
                - success: bool
                - merged_count: int
                - merged_files: List[str]
                - deleted_files: List[str]
                - deleted_folders: List[str]
                - errors: List[str]
        """
        options = options or {}
        dry_run = options.get('dry_run', False)
        delete_sources = options.get('delete_sources', False)
        delete_empty_folders = options.get('delete_empty_folders', False)
        recursive = options.get('recursive', False)
        backup = options.get('backup', True)
        verbose = options.get('verbose', False)

        # Reset state
        self.merged_files = []
        self.deleted_files = []
        self.deleted_folders = []
        self.errors = []

        # Configure logging
        if verbose:
            self.logger.setLevel(logging.DEBUG)

        try:
            # Read input file
            input_path_obj = Path(input_path).resolve()
            if not input_path_obj.exists():
                raise FileNotFoundError(f"Input file not found: {input_path}")

            self.logger.info(f"Reading codex file: {input_path_obj}")

            with open(input_path_obj, 'r', encoding='utf-8') as f:
                if input_path_obj.suffix.lower() in ['.json']:
                    codex_data = json.load(f)
                else:
                    codex_data = yaml.safe_load(f)

            # Validate structure
            if not codex_data or not isinstance(codex_data, dict):
                raise ValueError("Invalid codex file structure")

            # Check for children
            if 'children' not in codex_data or not isinstance(codex_data['children'], list):
                raise ValueError("No 'children' array found in codex file")

            parent_dir = input_path_obj.parent

            # Count includes
            include_count = self._count_includes(codex_data['children'])
            self.logger.info(f"Found {include_count} include directives in codex file")

            if include_count == 0:
                self.logger.warning("No include directives found - nothing to merge")
                return {
                    'success': True,
                    'merged_count': 0,
                    'merged_files': [],
                    'deleted_files': [],
                    'deleted_folders': [],
                    'errors': ['No include directives found - nothing to merge']
                }

            # Resolve all includes
            resolved_children = self._resolve_includes(
                codex_data['children'],
                parent_dir,
                recursive
            )

            if dry_run:
                # In dry run, just report what would happen
                self.logger.info(f"[DRY RUN] Would merge {len(self.merged_files)} includes")
                return {
                    'success': True,
                    'merged_count': len(self.merged_files),
                    'merged_files': self.merged_files,
                    'deleted_files': self.merged_files if delete_sources else [],
                    'deleted_folders': [],
                    'errors': self.errors
                }

            # Update the parent file
            codex_data['children'] = resolved_children

            # Update metadata
            if 'metadata' not in codex_data:
                codex_data['metadata'] = {}

            codex_data['metadata']['updated'] = datetime.utcnow().isoformat() + 'Z'

            # Remove exploded metadata since we're imploding
            if 'exploded' in codex_data['metadata']:
                del codex_data['metadata']['exploded']

            # Add imploded metadata
            codex_data['metadata']['imploded'] = {
                'timestamp': datetime.utcnow().isoformat() + 'Z',
                'merged_count': len(self.merged_files)
            }

            # Create backup
            if backup:
                backup_path = input_path_obj.with_suffix(input_path_obj.suffix + '.backup')
                self.logger.info(f"Creating backup: {backup_path}")
                shutil.copy2(input_path_obj, backup_path)

            # Write updated parent file
            output_format = 'json' if input_path_obj.suffix.lower() == '.json' else 'yaml'
            self._write_codex_file(input_path_obj, codex_data, output_format)
            self.logger.info(f"✓ Updated parent file with {len(self.merged_files)} merged nodes")

            # Delete source files if requested
            if delete_sources and self.merged_files:
                self._delete_source_files(delete_empty_folders)

            return {
                'success': True,
                'merged_count': len(self.merged_files),
                'merged_files': self.merged_files,
                'deleted_files': self.deleted_files,
                'deleted_folders': self.deleted_folders,
                'errors': self.errors
            }

        except Exception as e:
            self.logger.error(f"Implode failed: {e}", exc_info=True)
            return {
                'success': False,
                'merged_count': 0,
                'merged_files': [],
                'deleted_files': [],
                'deleted_folders': [],
                'errors': [str(e)] + self.errors
            }

    def _count_includes(self, children: List[Any]) -> int:
        """Count include directives in children array."""
        count = 0
        for child in children:
            if isinstance(child, dict) and 'include' in child and isinstance(child['include'], str):
                count += 1
        return count

    def _resolve_includes(
        self,
        children: List[Any],
        parent_dir: Path,
        recursive: bool
    ) -> List[Dict[str, Any]]:
        """Resolve all include directives in children array."""
        resolved: List[Dict[str, Any]] = []

        for child in children:
            if isinstance(child, dict) and 'include' in child and isinstance(child['include'], str):
                # This is an include directive
                include_path = child['include']

                try:
                    resolved_content = self._resolve_include(include_path, parent_dir, recursive)
                    if resolved_content:
                        resolved.append(resolved_content)
                    else:
                        # Keep the include directive if resolution failed
                        resolved.append(child)
                except Exception as e:
                    self.errors.append(f"Failed to resolve include \"{include_path}\": {e}")
                    # Keep the original include directive on failure
                    resolved.append(child)
            else:
                # Regular child - keep as-is, but check for nested includes if recursive
                if recursive and isinstance(child, dict) and 'children' in child and isinstance(child['children'], list):
                    nested_resolved = self._resolve_includes(
                        child['children'],
                        parent_dir,
                        recursive
                    )
                    resolved.append({**child, 'children': nested_resolved})
                else:
                    resolved.append(child)

        return resolved

    def _resolve_include(
        self,
        include_path: str,
        parent_dir: Path,
        recursive: bool
    ) -> Optional[Dict[str, Any]]:
        """Resolve a single include directive."""
        # Resolve the path relative to parent directory
        # Include paths typically start with / which means relative to parent dir
        if include_path.startswith('/'):
            full_path = parent_dir / include_path.lstrip('/')
        else:
            full_path = (parent_dir / include_path).resolve()

        full_path = full_path.resolve()

        # Validate file exists
        if not full_path.exists():
            self.errors.append(f"Include file not found: {full_path}")
            return None

        # Validate it's a codex file
        if not is_codex_file(str(full_path)):
            self.errors.append(f"Include is not a valid codex file: {full_path}")
            return None

        # Read and parse the file
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                if full_path.suffix.lower() == '.json':
                    included_data = json.load(f)
                else:
                    included_data = yaml.safe_load(f)
        except Exception as e:
            self.errors.append(f"Failed to parse include file \"{full_path}\": {e}")
            return None

        # Track merged file
        self.merged_files.append(str(full_path))
        self.logger.info(f"  ✓ Resolved include: {include_path} -> {full_path}")

        # Extract the entity data, removing metadata specific to standalone files
        entity_data = self._extract_entity_data(included_data)

        # Handle recursive includes if the included file has children with includes
        if recursive and 'children' in entity_data and isinstance(entity_data['children'], list):
            included_dir = full_path.parent
            entity_data['children'] = self._resolve_includes(
                entity_data['children'],
                included_dir,
                recursive
            )

        return entity_data

    def _extract_entity_data(self, included_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract entity data from included file, removing standalone metadata."""
        entity_data: Dict[str, Any] = {}

        # Copy all fields except metadata (which is for standalone use only)
        for key, value in included_data.items():
            if key == 'metadata':
                # Skip metadata from included file
                continue
            entity_data[key] = value

        return entity_data

    def _delete_source_files(self, delete_empty_folders: bool) -> None:
        """Delete source files after successful merge."""
        folders_to_check: Set[str] = set()

        for file_path in self.merged_files:
            try:
                path = Path(file_path)
                if path.exists():
                    path.unlink()
                    self.deleted_files.append(file_path)
                    self.logger.info(f"  ✓ Deleted: {file_path}")

                    # Track parent folder for potential cleanup
                    folders_to_check.add(str(path.parent))
            except Exception as e:
                self.errors.append(f"Failed to delete file \"{file_path}\": {e}")

        # Delete empty folders if requested
        if delete_empty_folders:
            # Sort by depth (deepest first) to handle nested empty folders
            sorted_folders = sorted(
                folders_to_check,
                key=lambda p: len(Path(p).parts),
                reverse=True
            )

            for folder in sorted_folders:
                try:
                    folder_path = Path(folder)
                    if folder_path.exists() and folder_path.is_dir():
                        contents = list(folder_path.iterdir())
                        if len(contents) == 0:
                            folder_path.rmdir()
                            self.deleted_folders.append(folder)
                            self.logger.info(f"  ✓ Deleted empty folder: {folder}")
                except Exception as e:
                    # Ignore errors when checking/deleting folders
                    self.logger.debug(f"Could not delete folder \"{folder}\": {e}")

    def _write_codex_file(self, path: Path, data: Dict[str, Any], format: str) -> None:
        """Write codex data to file with proper formatting."""
        with open(path, 'w', encoding='utf-8') as f:
            if format == 'yaml':
                yaml.dump(
                    data,
                    f,
                    Dumper=get_yaml_dumper_with_pipe_format(),
                    default_flow_style=False,
                    allow_unicode=True,
                    sort_keys=False,
                    width=120
                )
            else:
                json.dump(data, f, indent=2, ensure_ascii=False)

    @staticmethod
    def get_include_count(file_path: str) -> int:
        """Get count of include directives from a codex file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            is_json = content.strip().startswith('{')
            data = json.loads(content) if is_json else yaml.safe_load(content)

            if not data or not isinstance(data.get('children'), list):
                return 0

            count = 0
            for child in data['children']:
                if isinstance(child, dict) and 'include' in child:
                    count += 1

            return count
        except Exception:
            return 0

    @staticmethod
    def get_include_paths(file_path: str) -> List[str]:
        """Get list of include paths from a codex file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            is_json = content.strip().startswith('{')
            data = json.loads(content) if is_json else yaml.safe_load(content)

            if not data or not isinstance(data.get('children'), list):
                return []

            paths: List[str] = []
            for child in data['children']:
                if isinstance(child, dict) and 'include' in child and isinstance(child['include'], str):
                    paths.append(child['include'])

            return paths
        except Exception:
            return []


# ============================================================================
# Command-Line Interface
# ============================================================================

def main():
    """Main entry point for command-line usage."""
    parser = argparse.ArgumentParser(
        description='Merge included files back into a parent codex document',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Merge all includes back into parent
  python implode_codex.py story.codex.yaml

  # Preview what would be merged (no changes made)
  python implode_codex.py story.codex.yaml --dry-run

  # Merge and delete source files
  python implode_codex.py story.codex.yaml --delete-sources

  # Also delete empty folders
  python implode_codex.py story.codex.yaml --delete-sources --delete-empty-folders

  # Recursive merge (resolve nested includes)
  python implode_codex.py story.codex.yaml --recursive

  # Combine options
  python implode_codex.py story.codex.yaml --recursive --delete-sources -v
        """
    )

    parser.add_argument(
        'input_file',
        help='Path to input codex file'
    )

    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Preview what would be merged without making changes'
    )

    parser.add_argument(
        '--delete-sources',
        action='store_true',
        help='Delete included files after merging them'
    )

    parser.add_argument(
        '--delete-empty-folders',
        action='store_true',
        help='Delete folders that become empty after deleting source files'
    )

    parser.add_argument(
        '--recursive',
        action='store_true',
        help='Resolve nested includes (includes within included files)'
    )

    parser.add_argument(
        '--no-backup',
        action='store_true',
        help='Do not create backup of original file'
    )

    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Detailed logging'
    )

    args = parser.parse_args()

    # Setup logging
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format='%(levelname)s: %(message)s'
    )

    # Build options
    options = {
        'dry_run': args.dry_run,
        'delete_sources': args.delete_sources,
        'delete_empty_folders': args.delete_empty_folders,
        'recursive': args.recursive,
        'backup': not args.no_backup,
        'verbose': args.verbose
    }

    # Show initial info
    print("=" * 60)
    print("Codex Imploder - Merge Included Files")
    print("=" * 60)

    if args.dry_run:
        print("[DRY RUN MODE - No files will be modified]")

    print(f"\nInput: {args.input_file}")

    # Get include info
    include_count = CodexImploder.get_include_count(args.input_file)
    include_paths = CodexImploder.get_include_paths(args.input_file)

    print(f"Includes found: {include_count}")
    if args.verbose and include_paths:
        for i, path in enumerate(include_paths, 1):
            print(f"  {i}. {path}")

    print(f"\nOptions:")
    print(f"  Recursive: {args.recursive}")
    print(f"  Delete sources: {args.delete_sources}")
    print(f"  Delete empty folders: {args.delete_empty_folders}")
    print(f"  Backup: {not args.no_backup}")
    print()

    # Run imploder
    imploder = CodexImploder()
    result = imploder.implode(args.input_file, options)

    # Print results
    print("\n" + "=" * 60)
    if result['success']:
        if args.dry_run:
            print(f"[DRY RUN] Would merge {result['merged_count']} includes")
        else:
            print(f"Implode complete!")
            print(f"   Merged: {result['merged_count']} includes")

        if result['merged_files']:
            print(f"\n{'Would merge' if args.dry_run else 'Merged'} files:")
            for file_path in result['merged_files']:
                print(f"   - {file_path}")

        if result['deleted_files']:
            print(f"\nDeleted files:")
            for file_path in result['deleted_files']:
                print(f"   - {file_path}")

        if result['deleted_folders']:
            print(f"\nDeleted empty folders:")
            for folder in result['deleted_folders']:
                print(f"   - {folder}")

        if result['errors']:
            print(f"\nWarnings ({len(result['errors'])}):")
            for error in result['errors']:
                print(f"   - {error}")
    else:
        print(f"Implode failed!")
        if result['errors']:
            print(f"\nErrors:")
            for error in result['errors']:
                print(f"   - {error}")
        sys.exit(1)

    print("=" * 60)


if __name__ == '__main__':
    main()
