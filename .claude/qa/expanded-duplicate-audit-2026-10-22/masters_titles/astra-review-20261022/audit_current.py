"""Verify reviewed member bytes against pinned main tree; no native mutations.
Usage: python audit_current.py --tree /path/to/c6dd8356d-ls-tree.z
Create that tree with: git ls-tree -rz c6dd8356d > /path/to/tree.z
"""
import argparse
import gzip
import hashlib
import json
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument('--tree', required=True)
args = parser.parse_args()
root = Path(__file__).resolve().parent
lane = root.parent
old = json.loads(gzip.open(lane / 'reviewed-original-records.json.gz', 'rt').read())
old.update({r['id']: r for r in json.loads((lane / 'hourly-20261022/work-snapshots.json').read_text())})
cases = json.loads((lane / 'cases.json').read_text()) + json.loads((lane / 'hourly-20261022/cases.json').read_text())
current = {r['record']['id']: r for r in json.loads(gzip.open(root / 'current-source-snapshots.json.gz', 'rt').read())}
tree_bytes = Path(args.tree).read_bytes()
tree = {}
for row in tree_bytes.split(b'\0'):
    if row:
        meta, path = row.split(b'\t', 1)
        tree[path.decode()] = meta.decode().split()[2]

def byte_hashes(record):
    raw = (json.dumps(record, ensure_ascii=False, indent=2) + '\n').encode()
    return hashlib.sha256(raw).hexdigest(), hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest()

coverage = []
for case in cases:
    records = []
    for item in case['records']:
        old_sha, old_blob = byte_hashes(old[item['id']]['record'])
        assert old_sha == item['sha256'], (case['case_id'], 'baseline bytes not reproduced')
        main_blob = tree.get(item['path'])
        same = old_blob == main_blob
        if same:
            sha, state, merged = old_sha, 'unchanged', old[item['id']]['record'].get('merged_into')
        else:
            snapshot = current[item['id']]
            sha, blob = byte_hashes(snapshot['record'])
            assert sha == snapshot['sha256'] and blob == main_blob, (case['case_id'], 'changed member not verified')
            state, merged = 'changed_read', snapshot['record'].get('merged_into')
        records.append({**item, 'old_sha256': old_sha, 'old_snapshot_bytes_reproduced': True,
                        'baseline_git_blob': old_blob, 'main_git_blob': main_blob,
                        'state': state, 'sha256': sha, 'merged_into': merged})
    coverage.append({'case_id': case['case_id'], 'status': case['status'], 'type': case['type'],
                     'records': records, 'main_state': 'all_live' if all(not r['merged_into'] for r in records) else 'needs_resolution'})
result = {'upstream_sha': 'c6dd8356d', 'tree_sha256': hashlib.sha256(tree_bytes).hexdigest(),
          'method': 'Exact reconstructed baseline bytes checked by stored SHA256; calculate Git blob SHA1 and compare pinned main ls-tree. Changed records independently read and verified against tree.',
          'scope': '112 members in 56 reviewed cases; not a full-reference scan', 'cases': coverage}
(root / 'main-coverage.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({'cases': len(coverage), 'members': sum(len(c['records']) for c in coverage),
                  'changed': sum(r['state'] == 'changed_read' for c in coverage for r in c['records']),
                  'all_live': all(c['main_state'] == 'all_live' for c in coverage)}))
