#!/usr/bin/env python3
"""Read-only evidence and upstream-drift audit. No confirmed case is auto-applied.

Run against the original full checkout using --root; --upstream must be a fetched
ref. The optional --text-root reads a Git tree, not all text-body references.
"""
import argparse
import collections
import hashlib
import json
import pathlib
import subprocess

BASE = 'bfaf3cfb3b9b0475fc9fd8d2ce216c291ebc9cca'
LANES = ['classics_titles', 'history_titles', 'masters_titles',
         'collections_titles', 'people_names_aliases', 'people_religious_variants']

def git(root, *args):
    return subprocess.check_output(['git', *args], cwd=root)

def records(case):
    found = {}
    def walk(x):
        if isinstance(x, dict):
            if x.get('path') and x.get('sha256') and isinstance(x['path'], str):
                found[x['path']] = {'path': x['path'], 'sha256': x['sha256'], 'id': x.get('id')}
            for v in x.values():
                walk(v)
        elif isinstance(x, list):
            for v in x:
                walk(v)
    walk(case)
    for i, p in case.get('paths', {}).items():
        if isinstance(p, str) and case.get('sha256', {}).get(i):
            found[p] = {'path': p, 'sha256': case['sha256'][i], 'id': i}
    return list(found.values())

def run():
    ap = argparse.ArgumentParser()
    ap.add_argument('--root', type=pathlib.Path, required=True)
    ap.add_argument('--upstream', default='origin/main')
    ap.add_argument('--text-root', type=pathlib.Path)
    ap.add_argument('--text-ref', default='FETCH_HEAD')
    ap.add_argument('--output', type=pathlib.Path, required=True)
    a = ap.parse_args()
    folder = pathlib.Path(__file__).resolve().parent
    upstream = git(a.root, 'rev-parse', a.upstream).decode().strip()
    changed = set(git(a.root, 'diff', '--name-only', '-z', BASE, upstream).decode().split('\0'))
    assets = collections.defaultdict(list)
    text_sha = None
    if a.text_root:
        text_sha = git(a.text_root, 'rev-parse', a.text_ref).decode().strip()
        for p in git(a.text_root, 'ls-tree', '-rz', '--name-only', text_sha).decode().split('\0'):
            parts = p.split('/')
            if len(parts) > 5 and parts[0] in ('Work', 'Book'):
                assets[parts[4]].append(p)
    result = {'research_base': BASE, 'upstream_sha': upstream,
              'text_tree_sha': text_sha, 'native_mutations': 0,
              'full_text_content_reference_scan_complete': False,
              'note': 'confirmed is an identity decision, not authorization from this report to apply; live-reference, draft and text migration gates remain.',
              'lanes': {}, 'errors': [], 'cross_lane_overlap': []}
    all_members = collections.defaultdict(list)
    unique_refs = {}
    for lane in LANES:
        d = folder/lane
        f = d/('cases-all.json' if lane == 'people_religious_variants' else 'cases.json')
        cases = json.loads(f.read_text())
        base_counts = dict(collections.Counter(c['status'] for c in cases))
        hourly = d/'hourly-20261022'
        new_cases = json.loads((hourly/'cases.json').read_text()) if (hourly/'cases.json').exists() else []
        superseded = {c.get('supersedes_case_id') or c.get('supersedes') for c in new_cases}
        old_ids = {c['case_id'] for c in cases}
        for old in superseded - {None}:
            if old not in old_ids:
                result['errors'].append({'lane': lane, 'error': 'unknown superseded case', 'case_id': old})
        cases = [c for c in cases if c['case_id'] not in superseded] + new_cases
        if len({c['case_id'] for c in cases}) != len(cases):
            result['errors'].append({'lane': lane, 'error': 'duplicate case ID'})
        row = {'canonical_case_file': str(f.relative_to(folder)), 'case_counts_before_this_run': base_counts,
               'this_run_decisions': dict(collections.Counter(c['status'] for c in new_cases)),
               'superseded_case_ids': sorted(superseded - {None}),
               'case_counts': dict(collections.Counter(c['status'] for c in cases)),
               'confirmed_losers': sum(len(c.get('losers', [])) for c in cases if c['status'] == 'confirmed'),
               'upstream_drift': [], 'loser_text_assets': [], 'case_files_to_read_after_base': []}
        if (hourly/'cases.json').exists():
            row['case_files_to_read_after_base'].append(str((hourly/'cases.json').relative_to(folder)))
        row['effective_case_ids'] = [c['case_id'] for c in cases]
        row['execution_hold_case_ids'] = ['JC-001'] if lane == 'classics_titles' else []
        row['all_cases_applied'] = False
        for c in cases:
            for r in records(c):
                unique_refs[r['path']] = r['sha256']
                p = a.root/r['path']
                if not p.exists() or hashlib.sha256(p.read_bytes()).hexdigest() != r['sha256']:
                    result['errors'].append({'lane': lane, 'case_id': c['case_id'], 'path': r['path'], 'error': 'local reviewed hash mismatch'})
                if r['path'] in changed:
                    raw = git(a.root, 'show', f'{upstream}:{r["path"]}')
                    now = json.loads(raw)
                    row['upstream_drift'].append({'case_id': c['case_id'], 'path': r['path'],
                        'upstream_sha256': hashlib.sha256(raw).hexdigest(), 'merged_into': now.get('merged_into'),
                        'reason': 're-review upstream source before apply; local baseline evidence is not current'})
            if c['status'] == 'confirmed':
                for i in [c.get('keeper')] + c.get('losers', []):
                    if i:
                        all_members[i].append({'lane': lane, 'case_id': c['case_id']})
                for i in c.get('losers', []):
                    if i in assets:
                        row['loser_text_assets'].append({'case_id': c['case_id'], 'id': i,
                            'file_count': len(assets[i]), 'paths': assets[i],
                            'gate': 'must migrate/check both sides in book-text before any tombstone'})
        result['lanes'][lane] = row
    for i, uses in all_members.items():
        if len(uses) > 1:
            result['cross_lane_overlap'].append({'id': i, 'uses': uses})
    result['unique_source_hashes_checked'] = len(unique_refs)
    result['source_hash_manifest'] = unique_refs
    a.output.write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n')
    print(json.dumps({'unique_hashes': len(unique_refs), 'errors': len(result['errors']),
       'upstream_drift_occurrences': sum(len(x['upstream_drift']) for x in result['lanes'].values()),
       'text_asset_loser_groups': sum(len(x['loser_text_assets']) for x in result['lanes'].values()),
       'overlapping_members': len(result['cross_lane_overlap'])}, ensure_ascii=False))
    return bool(result['errors'])

if __name__ == '__main__':
    raise SystemExit(run())
