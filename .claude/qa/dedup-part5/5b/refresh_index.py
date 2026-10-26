#!/usr/bin/env python3
"""对已合入的若干批（各批 merges.json）定点刷新 index/ 条目：旧记录取各批 merges.json 的 base 版本，
现有条目须等于旧记录算出的条目才改（否则视为既有漂移跳过）。用法：refresh_index.py <batch 目录>..."""
import json, pathlib, subprocess, sys
ROOT = pathlib.Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / 'build'))
import build_derived as B  # noqa: E402
DIR = {'Entity': 'entities', 'Work': 'works', 'Book': 'books'}
shards, rows, skipped = {}, [], []
for d in sys.argv[1:]:
    m = json.load(open(pathlib.Path(d) / 'merges.json', encoding='utf-8'))
    for g in m['merges']:
        for pre in g['preconditions']:
            rel = pre['path']; typ = rel.split('/')[0]
            old = json.loads(subprocess.check_output(['git', 'show', m['base'] + ':' + rel], cwd=ROOT))
            new = json.loads((ROOT / rel).read_text(encoding='utf-8'))
            srel = f"index/{DIR[typ]}/{B.shard_of(new['id']):x}.json"
            if srel not in shards: shards[srel] = json.loads((ROOT / srel).read_text(encoding='utf-8'))
            cur = shards[srel].get(new['id'])
            try:
                if cur is None or cur != B.index_entry(old, typ, rel):
                    skipped.append((new['id'], '现有条目与旧记录算出不一致（既有漂移或缺条）')); continue
                after = B.index_entry(new, typ, rel)
            except Exception as e:  # noqa
                skipped.append((new['id'], 'index_entry 异常 %r' % e)); continue
            if after != cur: shards[srel][new['id']] = after; rows.append(new['id'])
n = B.write_index(str(ROOT), shards)
print('entries_changed', len(rows), 'files', n, 'skipped', len(skipped))
