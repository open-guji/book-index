"""Validate every discovery record against its immutable Git tree and raw bytes.

This checks the discovery input, not identity decisions or merge safety.
"""
import argparse
import hashlib
import json
import sqlite3
import subprocess
from pathlib import Path

p = argparse.ArgumentParser()
p.add_argument('--db', required=True)
p.add_argument('--repo', required=True)
p.add_argument('--out', required=True)
a = p.parse_args()
db = sqlite3.connect(f'file:{a.db}?mode=ro', uri=True)
manifest = json.loads(db.execute("select value from metadata where key='manifest'").fetchone()[0])
tree = subprocess.check_output(['git', '-C', a.repo, 'ls-tree', '-r', '-z', manifest['base']])
paths = {}
for row in tree.split(b'\0'):
    if row:
        meta, name = row.split(b'\t', 1)
        paths[name.decode()] = meta.split()[2].decode()
errors = []
counts = {}
for rid, typ, name, path, blob, sha256, data in db.execute('select * from records'):
    raw = data.encode()
    obj = json.loads(data)
    if paths.get(path) != blob:
        errors.append([rid, 'tree blob mismatch'])
    if hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest() != blob:
        errors.append([rid, 'raw Git blob mismatch'])
    if hashlib.sha256(raw).hexdigest() != sha256:
        errors.append([rid, 'SHA256 mismatch'])
    if obj['id'] != rid or obj.get('merged_into') or obj.get('retired'):
        errors.append([rid, 'identity or active-state mismatch'])
    counts[typ] = counts.get(typ, 0) + 1
if hashlib.sha256(tree).hexdigest() != manifest['tree_sha256']:
    errors.append(['tree', 'full tree SHA256 mismatch'])
result = {'base': manifest['base'], 'scope': 'all active Work and Entity discovery inputs; not full reference or merge audit',
          'records_checked': counts, 'total_checked': sum(counts.values()), 'errors': errors}
Path(a.out).write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
print(json.dumps(result, ensure_ascii=False))
raise SystemExit(bool(errors))
