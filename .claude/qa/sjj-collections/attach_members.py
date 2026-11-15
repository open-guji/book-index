#!/usr/bin/env python3
"""按 attach.json 给库内已有 Book 在成员侧加 contained_in（只挂 CiNii 注记明载影印底本、且与库内 Book.edition 或其所属丛编名吻合者）。
Book 的 revision 小版本 +1（contained_in 属存储侧关系，要 bump）。乾跑默认，--apply 才写。"""
import argparse, datetime, json, pathlib, sys
ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path[:0] = [str(ROOT / 'build')]
import v2common as V  # noqa: E401
TODAY = datetime.date.today().isoformat()
ap = argparse.ArgumentParser(); ap.add_argument('--apply', action='store_true'); a = ap.parse_args()
att = json.load(open(pathlib.Path(__file__).parent / 'attach.json', encoding='utf-8'))
n = 0
for bid, v in att.items():
    p = ROOT / v['path']
    raw = p.read_text(encoding='utf-8'); d = json.loads(raw); fmt = V.detect_format(raw, d)
    assert d['id'] == bid and d['type'] == 'book'
    ci = d.setdefault('contained_in', [])
    if any(x['id'] == v['collection'] for x in ci): continue
    item = {'id': v['collection']}
    if v['volume_index']: item['volume_index'] = v['volume_index']
    ci.append(item)
    x, y, z = (int(t) for t in (d.get('revision') or '1.0.0').split('.')); d['revision'] = f'{x}.{y + 1}.0'; d['revised_at'] = TODAY
    n += 1
    if a.apply: p.write_text(V.dump(d, fmt), encoding='utf-8')
print('挂接', n, '（已写）' if a.apply else '（乾跑）')
