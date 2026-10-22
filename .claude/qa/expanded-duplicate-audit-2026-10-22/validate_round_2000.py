"""Count new cases and detect pair overlap with all earlier reviewed cases."""
import collections
import itertools
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
LANES = ['classics_titles', 'history_titles', 'masters_titles',
         'collections_titles', 'people_names_aliases', 'people_religious_variants']

def member_ids(case):
    items = case.get('ids') or case.get('members') or ([case.get('keeper')] + case.get('losers', []))
    return sorted({i if isinstance(i, str) else i['id'] for i in items if isinstance(i, str) or isinstance(i, dict) and 'id' in i})

old_pairs, new_pairs, cases, errors = {}, {}, {}, []
for lane in LANES:
    for rel in ['cases-all.json' if lane == 'people_religious_variants' else 'cases.json',
                'hourly-20261022/cases.json', 'astra-review-20261022/cases.json', 'hourly-20261022T1900/cases.json']:
        for case in json.loads((ROOT / lane / rel).read_text()):
            for pair in itertools.combinations(member_ids(case), 2):
                old_pairs.setdefault(pair, []).append(case['case_id'])
    for case in json.loads((ROOT / lane / 'hourly-20261022T2000/cases.json').read_text()):
        cid = case['case_id']
        ids = member_ids(case)
        if cid in cases or len(ids) < 2:
            errors.append([cid, 'duplicate case ID or missing members'])
        cases[cid] = {'lane': lane, 'ids': ids, 'status': case['status']}
        for pair in itertools.combinations(ids, 2):
            new_pairs.setdefault(pair, []).append(cid)
overlaps = [{'ids': p, 'new': cs, 'old': old_pairs[p]} for p, cs in new_pairs.items() if p in old_pairs]
cross = [{'ids': p, 'cases': cs} for p, cs in new_pairs.items() if len(cs) > 1]
result = {'base': 'c6dd8356d613fc5614beb88f0a61a3d04cfb069e', 'reviewed_cases': len(cases),
          'unique_case_member_pairs': len(new_pairs), 'case_counts': dict(collections.Counter(c['status'] for c in cases.values())),
          'case_details': cases, 'old_pair_overlaps': overlaps, 'cross_lane_duplicate_pairs': cross, 'errors': errors,
          'scope': 'Case identities and pair overlap only. Multi-member case pairs are not all asserted duplicates.'}
(ROOT / 'round-2000-validation.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({k: v for k, v in result.items() if k != 'case_details'}, ensure_ascii=False))
raise SystemExit(bool(errors or overlaps or cross))
