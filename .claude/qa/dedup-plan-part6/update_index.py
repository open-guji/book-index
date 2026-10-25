#!/usr/bin/env python3
"""（部分 6 版：加 Collection→index/collections.json）只刷新本批改动记录在 index/ 里的条目（用官方 build_derived.index_entry／write_index）。
全量刷新会混入 main 上与本批无关的既有漂移，故只动受影响条目；写前核对「旧记录算出的条目 == 现有条目」，
不等的（既有漂移）跳过并报出。用法：update_index.py <batch 目录>"""
import json, pathlib, subprocess, sys
ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'build'))
import build_derived as B  # noqa: E402

DIR = {'Entity': 'entities', 'Work': 'works', 'Book': 'books', 'Collection': 'collections'}
names = subprocess.check_output(['git', '-c', 'core.quotePath=false', 'diff', '--name-only', 'origin/main'], cwd=ROOT, text=True).split('\n')
shards, rows, skipped = {}, [], []
for rel in names:
    typ = rel.split('/')[0]
    if typ not in DIR or not rel.endswith('.json'):
        continue
    new = json.loads((ROOT / rel).read_text(encoding='utf-8'))
    try:
        old = json.loads(subprocess.check_output(['git', 'show', 'origin/main:' + rel], cwd=ROOT))
    except subprocess.CalledProcessError:
        continue
    srel = "index/collections.json" if typ == "Collection" else f"index/{DIR[typ]}/{B.shard_of(new['id']):x}.json"
    if srel not in shards:
        shards[srel] = json.loads((ROOT / srel).read_text(encoding='utf-8'))
    cur = shards[srel].get(new['id'])
    try:
        if cur is None or cur != B.index_entry(old, typ, rel):
            skipped.append((new['id'], '现有条目与旧记录算出不一致（既有漂移或缺条）')); continue
        after = B.index_entry(new, typ, rel)
    except Exception as e:  # noqa
        skipped.append((new['id'], 'index_entry 异常 %r' % e)); continue
    if after != cur:
        shards[srel][new['id']] = after
        rows.append(new['id'])
n = B.write_index(str(ROOT), shards)
out = pathlib.Path(sys.argv[1]) / 'index-update.json'
out.write_text(json.dumps({'entries_changed': len(rows), 'files_written': n, 'skipped': skipped}, ensure_ascii=False, indent=1) + '\n')
print(len(rows), n, skipped[:5], len(skipped))
