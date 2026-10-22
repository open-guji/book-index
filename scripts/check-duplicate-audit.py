#!/usr/bin/env python3
"""Check audit tombstones, live references, and preservation of book-text IDs."""
import argparse
import collections
import json
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / '.claude/qa'))
import backrefs  # noqa: E402


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def require(condition, message):
    if not condition:
        raise ValueError(message)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--text-index', type=Path, required=True,
                        help='Complete book-text/index/texts directory (16 shards)')
    args = parser.parse_args()
    shards = [args.text_index / f'{shard}.json' for shard in '0123456789abcdef']
    require(all(path.is_file() for path in shards), 'All 16 book-text index shards are required')
    text_ids = {rid for path in shards for rid in read(path)}
    require(text_ids, 'Empty text index cannot validate text preservation')
    ledger = read(ROOT / '.claude/qa/reports/duplicate-audit-2026-10-21/merges.json')
    mapping = {rid: step['keeper'] for step in ledger['merges'] for rid in step['losers']}
    counts = collections.Counter()
    for step in ledger['merges']:
        for entry in step['preconditions']:
            obj = read(ROOT / entry['path'])
            require(obj['id'] == entry['id'], f"Record ID mismatch: {entry['path']}")
            if entry['id'] in step['losers']:
                require(obj.get('merged_into') == step['keeper'], f"Broken tombstone: {obj['id']}")
                require(obj['id'] not in text_ids, f"Retired text-bearing ID: {obj['id']}")
                counts['tombstones'] += 1
            else:
                require(not obj.get('merged_into'), f"Keeper is a tombstone: {obj['id']}")
                history = obj.get('merged_from', []) if step['type'] == 'book' else obj.get('merged_in', [])
                history_ids = {item.get('id') if isinstance(item, dict) else item for item in history}
                require(set(step['losers']) <= history_ids, f"Missing merge history: {obj['id']}")
                counts['keepers'] += 1
    # rg selects candidate files from every live source family, not from the changed-file list.
    with tempfile.TemporaryDirectory() as temp:
        patterns = Path(temp) / 'ids.txt'
        patterns.write_text('\n'.join(mapping) + '\n', encoding='utf-8')
        result = subprocess.run(
            ['rg', '-l', '-F', '-f', str(patterns), '--glob', '*.json',
             'Work', 'Book', 'Collection', 'Entity', 'classification', 'promotions',
             'curation', 'recommended.json'],
            cwd=ROOT, text=True, capture_output=True, check=False,
        )
        require(result.returncode in (0, 1), result.stderr)
    bad = []
    for relative in result.stdout.splitlines():
        obj = read(ROOT / relative)
        counts['candidate_files'] += 1
        family = relative.split('/')[0]
        if family in backrefs.TYPES and not obj.get('merged_into'):
            for where, target, _ in backrefs.refs_of(family, obj):
                if 'merged_in' not in where and target in mapping:
                    bad.append((relative, where, target))
        if family == 'classification':
            require(not any(row[0] in mapping for row in obj.get('members', [])),
                    f'Stale classification member: {relative}')
        if family == 'promotions':
            require(not any(row['production_id'] in mapping for row in obj.get('promotions', {}).values()),
                    f'Stale promotion target: {relative}')
    require(not bad, f'Live references to newly merged IDs: {bad[:30]}')
    print(dict(counts))
    print(f'PASS: no live references to newly merged IDs; no text-bearing IDs retired '
          f'(checked {len(text_ids)} book-text IDs).')


if __name__ == '__main__':
    main()
