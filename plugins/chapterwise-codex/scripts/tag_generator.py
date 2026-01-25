"""
Tag Generator - Extract tags from body fields in Codex files

Auto-generate tags from content using text analysis.

Features:
- Unicode normalization and HTML/markdown cleanup
- Extended Latin tokenization with hyphen/apostrophe support
- Comprehensive stopword filtering + manuscript boilerplate
- Unigram and bigram extraction with heading boost
- Smart capitalization and redundancy avoidance

Usage:
    python tag_generator.py <file.codex.yaml> [options]

Examples:
    python tag_generator.py story.codex.yaml
    python tag_generator.py story.codex.yaml --count 15
    python tag_generator.py story.codex.yaml --min-count 5
    python tag_generator.py story.codex.yaml --dry-run
"""

import os
import sys
import re
import argparse
import logging
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional, Set

logger = logging.getLogger(__name__)


# Comprehensive stopwords set
STOPWORDS: Set[str] = {
    # Common English stopwords
    'the', 'and', 'for', 'that', 'with', 'this', 'from', 'have', 'not', 'are', 'was', 'were', 'but', 'you', 'your', 'his', 'her', 'their', 'its', 'our',
    'has', 'had', 'will', 'would', 'can', 'could', 'should', 'may', 'might', 'into', 'about', 'over', 'under', 'between', 'across', 'through', 'after', 'before',
    'then', 'than', 'because', 'while', 'where', 'when', 'what', 'which', 'who', 'whom', 'why', 'how', 'all', 'any', 'both', 'each', 'few', 'more', 'most', 'other',
    'some', 'such', 'no', 'nor', 'only', 'own', 'same', 'so', 'too', 'very', 'just', 'also', 'if', 'in', 'on', 'at', 'by', 'of', 'to', 'as', 'it', 'is', 'be', 'do', 'did',
    'does', 'done', 'an', 'a', 'or', 'he', 'she', 'they', 'them', 'we', 'i', 'me', 'my', 'mine', 'yours', 'theirs', 'ours', 'these', 'those', 'there', 'here',
    # Manuscript boilerplate
    'chapter', 'preface', 'acknowledgements', 'acknowledgments', 'introduction', 'editor', 'notes', 'bibliography', 'appendix', 'contents',
    # Additional common words
    'been', 'being', 'above', 'below', 'during', 'until', 'against', 'among', 'throughout', 'despite', 'towards', 'upon', 'whether',
    'however', 'therefore', 'thus', 'hence', 'although', 'though', 'even', 'still', 'yet', 'already', 'always', 'never', 'often', 'sometimes',
    'now', 'well', 'back', 'away', 'again', 'once', 'every', 'much', 'many', 'another', 'first', 'last', 'next', 'new', 'old', 'great', 'good',
    'high', 'long', 'little', 'own', 'right', 'left', 'part', 'place', 'case', 'week', 'work', 'world', 'area', 'home', 'hand', 'room', 'fact',
    'going', 'came', 'come', 'made', 'make', 'take', 'took', 'know', 'knew', 'think', 'thought', 'see', 'saw', 'want', 'give', 'gave', 'use', 'used',
    'find', 'found', 'tell', 'told', 'ask', 'asked', 'seem', 'seemed', 'feel', 'felt', 'try', 'tried', 'leave', 'left', 'call', 'called', 'need',
    'keep', 'kept', 'let', 'begin', 'began', 'seem', 'help', 'show', 'showed', 'hear', 'heard', 'play', 'run', 'ran', 'move', 'moved', 'live', 'lived',
    'believe', 'hold', 'held', 'bring', 'brought', 'happen', 'happened', 'write', 'wrote', 'provide', 'sit', 'sat', 'stand', 'stood', 'lose', 'lost',
    'pay', 'paid', 'meet', 'met', 'include', 'included', 'continue', 'continued', 'set', 'learn', 'learned', 'change', 'changed', 'lead', 'led',
    'understand', 'understood', 'watch', 'watched', 'follow', 'followed', 'stop', 'stopped', 'create', 'created', 'speak', 'spoke', 'read',
    'allow', 'allowed', 'add', 'added', 'spend', 'spent', 'grow', 'grew', 'open', 'opened', 'walk', 'walked', 'win', 'won', 'offer', 'offered',
    'remember', 'remembered', 'love', 'loved', 'consider', 'considered', 'appear', 'appeared', 'buy', 'bought', 'wait', 'waited', 'serve', 'served',
    'die', 'died', 'send', 'sent', 'expect', 'expected', 'build', 'built', 'stay', 'stayed', 'fall', 'fell', 'cut', 'reach', 'reached', 'kill', 'killed',
    'remain', 'remained', 'suggest', 'suggested', 'raise', 'raised', 'pass', 'passed', 'sell', 'sold', 'require', 'required', 'report', 'reported',
    'decide', 'decided', 'pull', 'pulled'
}


def is_codex_file(file_path: str) -> bool:
    """Check if file is a codex file."""
    lower = file_path.lower()
    return any(lower.endswith(ext) for ext in ['.codex.yaml', '.codex.yml', '.codex.json', '.codex'])


class TagGenerator:
    """Generate tags from codex body fields."""

    def __init__(self):
        self.entities_updated = 0
        self.total_tags_generated = 0
        self.files_modified: List[str] = []
        self.errors: List[str] = []
        self.processed_files: Set[str] = set()

    def _normalize_token(self, word: str) -> str:
        """Normalize a token (lowercase, trim, basic plural removal)."""
        # Strip leading/trailing punctuation
        w = re.sub(r"^[-'_]+|[-'_]+$", '', word)
        lw = w.lower()

        # Basic plural trim
        if len(lw) > 4 and lw.endswith('s') and not lw.endswith('ss'):
            lw = lw[:-1]
        if lw.endswith("'s"):
            lw = lw[:-2]

        return lw

    def _display_name(self, name: str) -> str:
        """Smart display name with proper capitalization."""
        if ' ' in name:
            # Title-case phrases
            return ' '.join(part.capitalize() for part in name.split(' '))
        return name.capitalize()

    def compute_tags_from_markdown(self, text: str, max_tags: int, min_count: int) -> List[Dict[str, Any]]:
        """
        Extract tags from markdown text.
        Handles markdown-specific cleanup and heading detection.
        """
        if not text:
            return []

        # Remove fenced code blocks and inline code
        text = re.sub(r'```[\s\S]*?```', ' ', text)
        text = re.sub(r'`[^`]*`', ' ', text)

        # Remove markdown images and links
        text = re.sub(r'!\[[^\]]*\]\([^)]*\)', ' ', text)
        text = re.sub(r'\[[^\]]*\]\([^)]*\)', ' ', text)

        # Split into lines to detect headings
        lines = text.split('\n')
        heading_parts = []
        body_parts = []

        for line in lines:
            stripped = line.strip()
            if stripped.startswith('#'):
                # Remove heading markers and collect for boosting
                clean = re.sub(r'^#+\s*', '', stripped)
                heading_parts.append(clean)
            else:
                body_parts.append(stripped)

        body_text = '\n'.join(body_parts)
        heading_boost_text = '\n'.join(heading_parts)

        return self.compute_tags(body_text, max_tags, min_count, heading_boost_text)

    def compute_tags(self, text: str, max_tags: int, min_count: int, heading_boost_text: str = '') -> List[Dict[str, Any]]:
        """
        Main tag extraction function.

        Returns list of dicts with 'name' and 'count' keys.
        """
        if not text:
            return []

        try:
            # Normalize Unicode punctuation (smart quotes, etc.)
            text = text.replace('\u2019', "'").replace('\u2018', "'")
            text = text.replace('\u201c', '"').replace('\u201d', '"')

            # Strip HTML tags and normalize whitespace
            text = re.sub(r'<[^>]+>', ' ', text)
            text = re.sub(r'\s+', ' ', text).strip()

            # Tokenization pattern (extended Latin letters, allow hyphen/apostrophe inside)
            token_pattern = re.compile(r"[A-Za-zÀ-ÖØ-öø-ÿ][A-Za-zÀ-ÖØ-öø-ÿ'\-]+")

            # Extract main body tokens
            body_tokens_raw = token_pattern.findall(text)
            body_tokens = [
                self._normalize_token(t)
                for t in body_tokens_raw
                if len(t) >= 3
            ]
            body_tokens = [
                t for t in body_tokens
                if re.search(r'[a-zA-ZÀ-ÖØ-öø-ÿ]', t) and t not in STOPWORDS
            ]

            # Extract heading tokens for boosting
            heading_tokens = []
            if heading_boost_text:
                heading_tokens_raw = token_pattern.findall(heading_boost_text)
                heading_tokens = [
                    self._normalize_token(t)
                    for t in heading_tokens_raw
                    if len(t) >= 3
                ]
                heading_tokens = [
                    t for t in heading_tokens
                    if re.search(r'[a-zA-ZÀ-ÖØ-öø-ÿ]', t) and t not in STOPWORDS
                ]

            # Unigram counts with heading boost
            counts: Dict[str, int] = {}
            for token in body_tokens:
                counts[token] = counts.get(token, 0) + 1
            for ht in heading_tokens:
                counts[ht] = counts.get(ht, 0) + 2  # Boost headings

            # Bigrams (phrases) with heading boost
            phrases: Dict[str, int] = {}

            def build_bigrams(tokens: List[str], boost: int = 1):
                for i in range(len(tokens) - 1):
                    a = tokens[i]
                    b = tokens[i + 1]
                    if a in STOPWORDS or b in STOPWORDS:
                        continue
                    if len(a) < 3 or len(b) < 3:
                        continue
                    phrase = f"{a} {b}"
                    phrases[phrase] = phrases.get(phrase, 0) + boost

            build_bigrams(body_tokens, 1)
            if heading_tokens:
                build_bigrams(heading_tokens, 2)  # Boost heading phrases

            # Sort by count
            phrase_items = sorted(
                [(p, c) for p, c in phrases.items() if c >= min_count],
                key=lambda x: -x[1]
            )[:max_tags * 2]

            word_items = sorted(
                [(w, c) for w, c in counts.items() if c >= min_count],
                key=lambda x: -x[1]
            )[:max_tags * 2]

            # Merge, avoiding redundancy
            selected: List[Tuple[str, int]] = []
            used_words: Set[str] = set()

            # Prioritize phrases
            for phrase, count in phrase_items:
                if count <= 0:
                    continue
                selected.append((phrase, count))
                parts = phrase.split(' ')
                used_words.update(parts)
                if len(selected) >= max_tags:
                    break

            # Add unigrams if space remains
            if len(selected) < max_tags:
                for word, count in word_items:
                    if count <= 0:
                        continue
                    if word in used_words:
                        continue  # Skip if part of selected phrase
                    selected.append((word, count))
                    if len(selected) >= max_tags:
                        break

            # Convert to output format with smart capitalization
            return [
                {'name': self._display_name(name), 'count': count}
                for name, count in selected
            ]

        except Exception as e:
            logger.error(f"Tag extraction failed: {e}")
            return []

    def _update_tags_in_object(
        self,
        obj: Dict[str, Any],
        parent_dir: str,
        max_tags: int,
        min_count: int,
        output_format: str,
        follow_includes: bool
    ) -> bool:
        """Update tags in an object and its children recursively."""
        was_modified = False

        # Check if this object has a body field
        body = obj.get('body')
        if body and isinstance(body, str):
            # Generate tags from body
            generated_tags = self.compute_tags_from_markdown(body, max_tags, min_count)

            if generated_tags:
                # Convert to appropriate format
                if output_format == 'simple':
                    obj['tags'] = [t['name'] for t in generated_tags]
                else:
                    obj['tags'] = generated_tags

                was_modified = True
                self.entities_updated += 1
                self.total_tags_generated += len(generated_tags)

        # Process children recursively
        children = obj.get('children', [])
        if children and isinstance(children, list):
            for child in children:
                if child and isinstance(child, dict):
                    # Check if this is an include directive
                    if 'include' in child and isinstance(child['include'], str) and follow_includes:
                        include_path = child['include']
                        if include_path.startswith('/'):
                            full_path = os.path.join(parent_dir, include_path)
                        else:
                            full_path = os.path.normpath(os.path.join(parent_dir, include_path))

                        if full_path not in self.processed_files:
                            self._process_included_file(full_path, max_tags, min_count, output_format, follow_includes)
                    else:
                        child_modified = self._update_tags_in_object(
                            child, parent_dir, max_tags, min_count, output_format, follow_includes
                        )
                        was_modified = was_modified or child_modified

        return was_modified

    def _process_included_file(
        self,
        file_path: str,
        max_tags: int,
        min_count: int,
        output_format: str,
        follow_includes: bool
    ):
        """Process an included file."""
        self.processed_files.add(file_path)

        if not os.path.exists(file_path):
            self.errors.append(f"Include file not found: {file_path}")
            return

        if not is_codex_file(file_path):
            self.errors.append(f"Include is not a valid codex file: {file_path}")
            return

        try:
            import yaml

            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            is_json = file_path.lower().endswith('.json')

            if is_json:
                import json
                data = json.loads(content)
            else:
                data = yaml.safe_load(content)

            parent_dir = os.path.dirname(file_path)
            was_modified = self._update_tags_in_object(
                data, parent_dir, max_tags, min_count, output_format, follow_includes
            )

            if was_modified:
                self._write_codex_file(file_path, data, 'json' if is_json else 'yaml')
                self.files_modified.append(file_path)
                logger.info(f"Updated included file: {file_path}")

        except Exception as e:
            self.errors.append(f"Failed to process include '{file_path}': {e}")

    def _write_codex_file(self, file_path: str, data: Dict[str, Any], fmt: str):
        """Write codex data to file with proper formatting."""
        import yaml

        if fmt == 'json':
            import json
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        else:
            # Create custom Dumper to avoid modifying global yaml state
            class CodexDumper(yaml.SafeDumper):
                pass

            def str_representer(dumper, s):
                if '\n' in s or len(s) > 80:
                    return dumper.represent_scalar('tag:yaml.org,2002:str', s, style='|')
                return dumper.represent_scalar('tag:yaml.org,2002:str', s)

            CodexDumper.add_representer(str, str_representer)

            with open(file_path, 'w', encoding='utf-8') as f:
                yaml.dump(data, f, Dumper=CodexDumper, default_flow_style=False, allow_unicode=True, sort_keys=False, width=120)

    def generate_tags(
        self,
        input_path: str,
        max_tags: int = 10,
        min_count: int = 3,
        output_format: str = 'simple',
        follow_includes: bool = False,
        dry_run: bool = False
    ) -> Dict[str, Any]:
        """
        Generate tags in a codex file.

        Returns:
            Dict with keys: success, entities_updated, total_tags_generated, files_modified, errors
        """
        # Reset state
        self.entities_updated = 0
        self.total_tags_generated = 0
        self.files_modified = []
        self.errors = []
        self.processed_files = set()

        try:
            import yaml

            if not os.path.exists(input_path):
                raise FileNotFoundError(f"Input file not found: {input_path}")

            self.processed_files.add(input_path)

            with open(input_path, 'r', encoding='utf-8') as f:
                file_content = f.read()

            is_json = input_path.lower().endswith('.json')

            if is_json:
                import json
                codex_data = json.loads(file_content)
            else:
                codex_data = yaml.safe_load(file_content)

            if not codex_data or not isinstance(codex_data, dict):
                raise ValueError("Invalid codex file structure")

            parent_dir = os.path.dirname(input_path)
            was_modified = self._update_tags_in_object(
                codex_data, parent_dir, max_tags, min_count, output_format, follow_includes
            )

            if was_modified and not dry_run:
                self._write_codex_file(input_path, codex_data, 'json' if is_json else 'yaml')
                self.files_modified.append(input_path)

            return {
                'success': True,
                'entities_updated': self.entities_updated,
                'total_tags_generated': self.total_tags_generated,
                'files_modified': self.files_modified,
                'errors': self.errors
            }

        except Exception as e:
            return {
                'success': False,
                'entities_updated': 0,
                'total_tags_generated': 0,
                'files_modified': [],
                'errors': [str(e)] + self.errors
            }


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Generate tags from body fields in Codex files',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python tag_generator.py story.codex.yaml
    python tag_generator.py story.codex.yaml --count 15
    python tag_generator.py story.codex.yaml --min-count 5
    python tag_generator.py story.codex.yaml --format detailed
    python tag_generator.py story.codex.yaml --follow-includes
    python tag_generator.py story.codex.yaml --dry-run
        """
    )

    parser.add_argument('input', help='Input codex file path')
    parser.add_argument('--count', type=int, default=10, help='Maximum tags per entity (default: 10)')
    parser.add_argument('--min-count', type=int, default=3, help='Minimum word occurrences (default: 3)')
    parser.add_argument('--format', choices=['simple', 'detailed'], default='simple',
                        help='Output format: simple (strings) or detailed (with counts)')
    parser.add_argument('--follow-includes', action='store_true', help='Process included files')
    parser.add_argument('-d', '--dry-run', action='store_true', help='Preview without making changes')
    parser.add_argument('-v', '--verbose', action='store_true', help='Verbose output')

    args = parser.parse_args()

    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    print(f"{'[DRY RUN] ' if args.dry_run else ''}Generating tags: {args.input}")
    print(f"  Max tags: {args.count}")
    print(f"  Min count: {args.min_count}")
    print(f"  Format: {args.format}")
    print(f"  Follow includes: {args.follow_includes}")
    print()

    generator = TagGenerator()
    result = generator.generate_tags(
        args.input,
        max_tags=args.count,
        min_count=args.min_count,
        output_format=args.format,
        follow_includes=args.follow_includes,
        dry_run=args.dry_run
    )

    if result['success']:
        print(f"Entities updated: {result['entities_updated']}")
        print(f"Total tags generated: {result['total_tags_generated']}")

        if result['files_modified']:
            print(f"\nFiles modified:")
            for f in result['files_modified']:
                print(f"  - {f}")

        if result['errors']:
            print(f"\nWarnings:")
            for e in result['errors']:
                print(f"  - {e}")

        if result['entities_updated'] == 0:
            print("\nNo tags generated (body fields may be too short or words don't meet minimum count)")

        sys.exit(0)
    else:
        print(f"Failed: {result['errors'][0] if result['errors'] else 'Unknown error'}")
        sys.exit(1)


if __name__ == '__main__':
    main()
