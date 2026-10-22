#!/usr/bin/env python3
"""Roll up successive research decisions, never apply native data mutations.

This validates case replacement and counts only. Source-level checks remain in
each lane's reports; this is not a live-reference or schema validation.
"""
import collections
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
LANES = ['classics_titles', 'history_titles', 'masters_titles',
         'collections_titles', 'people_names_aliases', 'people_religious_variants']


def run():
    result = {'research_ref': 'c6dd8356d613fc5614beb88f0a61a3d04cfb069e',
              'native_merge_groups': 0, 'validation_scope': 'case replacement and counts only',
              'lanes': {}, 'errors': []}
    total = collections.Counter()
    for lane in LANES:
        folder = ROOT / lane
        base = 'cases-all.json' if lane == 'people_religious_variants' else 'cases.json'
        effective = {}
        changes = []
        for rel in [base, 'hourly-20261022/cases.json', 'astra-review-20261022/cases.json', 'hourly-20261022T1900/cases.json', 'hourly-20261022T2000/cases.json']:
            for case in json.loads((folder / rel).read_text()):
                cid = case['case_id']
                old = case.get('supersedes_case_id') or case.get('supersedes')
                prior = effective.pop(old, None) if old else None
                if old and prior is None:
                    result['errors'].append(f'{lane}:{cid}: unknown replacement {old}')
                if cid in effective:
                    result['errors'].append(f'{lane}:{cid}: duplicate ID')
                if rel.startswith('hourly-20261022T2000/'):
                    changes.append({'case_id': cid, 'replaces': old,
                                    'old_status': prior['status'] if prior else None,
                                    'status': case['status']})
                effective[cid] = case
        counts = collections.Counter(c['status'] for c in effective.values())
        total.update(counts)
        result['lanes'][lane] = {'counts': dict(counts), 'effective_case_ids': list(effective),
                                 'this_round': changes, 'native_merge_groups': 0}
    result['effective_counts'] = dict(total)
    result['this_round_reviews'] = sum(len(x['this_round']) for x in result['lanes'].values())
    result['new_confirmations'] = sum(c['status'] == 'confirmed' and c['old_status'] != 'confirmed'
                                    for x in result['lanes'].values() for c in x['this_round'])
    if (ROOT / 'execution.json').exists():
        execution = json.loads((ROOT / 'execution.json').read_text())
        result['native_merge_groups'] = execution['native_merge_groups']
        result['native_data_state'] = execution['state']
        result['data_pr'] = execution['data_pr']
        result['data_prs'] = execution.get('data_prs', [execution['data_pr']])
        for lane, count in execution['lanes'].items():
            result['lanes'][lane]['native_merge_groups'] = count
    (ROOT / 'current-rollup.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({k: v for k, v in result.items() if k != 'lanes'}, ensure_ascii=False))
    return bool(result['errors'])


if __name__ == '__main__':
    raise SystemExit(run())
