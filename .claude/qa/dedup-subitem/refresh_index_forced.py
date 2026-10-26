#!/usr/bin/env python3
"""update_index.py 因「既有漂移」跳过的 Work 条目（他线改 Work 未刷 index），本批涉及者按现记录强制重算。
用法：refresh_index_forced.py <批次目录>（读写其中 index-update.json）"""
import json, pathlib, sys, glob
ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'build'))
import build_derived as B  # noqa: E402
f = pathlib.Path(sys.argv[1]) / 'index-update.json'
d = json.loads(f.read_text(encoding='utf-8'))
ids = [i[0] for i in d['skipped'] if i[0].startswith('d59')]
shards, n = {}, 0
for i in ids:
    p = glob.glob(str(ROOT / f'Work/{i[-3]}/{i[-2]}/{i[-1]}/{i}-*.json'))[0]
    rec = json.loads(pathlib.Path(p).read_text(encoding='utf-8'))
    s = f"index/works/{B.shard_of(i):x}.json"
    if s not in shards:
        shards[s] = json.loads((ROOT / s).read_text(encoding='utf-8'))
    e = B.index_entry(rec, 'Work', str(pathlib.Path(p).relative_to(ROOT)))
    if shards[s].get(i) != e:
        shards[s][i] = e; n += 1
B.write_index(str(ROOT), shards)
d['forced_refresh'] = ids
f.write_text(json.dumps(d, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
print('强制重算', n, '/', len(ids))
