#!/usr/bin/env python3
"""163 案遗留修补（2026-10-25）：
1. 人物并条被并者 description.sources 补回 keeper（PNA-2000-005、PRV-T008、PRV-H2000-002、PRV-H2000-004）；
2. MR-022～024 三个 Book 的 contained_in 草稿 Collection ID 按 promotions 换正式 ID 后去重；
3. PRV-H2000-006：Work d59fxwb68a9t 的撰人「釋實叉難陀」补挂 entity hixhd2h9bnrk（释学喜，alt_names 含实叉难陀）。
原值写 leftovers-原值.json。用法：leftovers.py [--apply]"""
import json, sys, os, glob, subprocess
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../..'))
HERE = os.path.dirname(os.path.abspath(__file__))
TODAY = '2026-10-25'
def p(t, i): return glob.glob(f'{ROOT}/{t}/{i[-3]}/{i[-2]}/{i[-1]}/{i}-*.json')[0]
def save(f, j): open(f, 'w', encoding='utf-8').write(json.dumps(j, ensure_ascii=False, indent=2) + '\n')
def bump(j, lvl):
    a, b, c = [int(x) for x in j.get('revision', '1.0.0').split('.')]
    j['revision'] = f'{a}.{b+1}.0' if lvl == 'minor' else f'{a}.{b}.{c+1}'
    j['revised_at'] = TODAY
orig, out = {}, []
# 1
b2 = json.load(open(os.path.join(HERE, '../batch-02/merges.json')))
for g in b2['merges']:
    if g['cluster_id'] not in ('PNA-2000-005', 'PRV-T008', 'PRV-H2000-002', 'PRV-H2000-004'): continue
    f = p('Entity', g['keeper']); k = json.load(open(f, encoding='utf-8'))
    orig[g['keeper']] = {'description': k.get('description')}
    desc = k.get('description') or {}
    srcs = desc.setdefault('sources', [])
    have = {json.dumps(s, sort_keys=True) for s in srcs}
    for pc in g['preconditions']:
        if pc['id'] == g['keeper']: continue
        old = json.loads(subprocess.run(['git', '-C', ROOT, 'show', f"{b2['base']}:{pc['path']}"], capture_output=True, text=True, check=True).stdout)
        for s in ((old.get('description') or {}).get('sources') or []):
            if json.dumps(s, sort_keys=True) not in have:
                s = dict(s); s['note'] = f'原屬並入之 {pc["id"]}（{g["cluster_id"]}）'
                srcs.append(s); have.add(json.dumps({k2: v for k2, v in s.items() if k2 != 'note'}, sort_keys=True))
    k['description'] = desc; bump(k, 'patch'); out.append((f, k))
# 2
pm = {}
for pf in glob.glob(f'{ROOT}/promotions/*.json'):
    for a, v in json.load(open(pf, encoding='utf-8')).items():
        if isinstance(v, dict) and 'production_id' in v: pm[a] = v['production_id']
        elif isinstance(v, dict):
            for a2, v2 in v.items():
                if isinstance(v2, dict) and 'production_id' in v2: pm[a2] = v2['production_id']
for i in ('993wfb6juo', '993wi5ke0w', '993wvk5b7l'):
    f = p('Book', i); j = json.load(open(f, encoding='utf-8'))
    orig[i] = {'contained_in': j.get('contained_in')}
    seen, new = set(), []
    for c in j.get('contained_in') or []:
        c = dict(c); c['id'] = pm.get(c['id'], c['id'])
        if c['id'] in seen: continue
        seen.add(c['id']); new.append(c)
    assert len(new) == 1, new
    j['contained_in'] = new; bump(j, 'patch'); out.append((f, j))
# 3
f = p('Work', 'd59fxwb68a9t'); j = json.load(open(f, encoding='utf-8'))
orig['d59fxwb68a9t'] = {'authors': json.loads(json.dumps(j['authors']))}
a = j['authors'][0]; assert a['name'] == '釋實叉難陀' and 'entity_id' not in a
a['entity_id'] = 'hixhd2h9bnrk'
a['name_basis'] = f'{TODAY} A11 去重 PRV-H2000-006 遺留：entity hixhd2h9bnrk（釋學喜，唐）alt_names 含「實叉難陀」「釋實叉難陀」，同一譯者。'
bump(j, 'minor'); out.append((f, j))
if '--apply' in sys.argv:
    for f, j in out: save(f, j)
    json.dump(orig, open(os.path.join(HERE, 'leftovers-原值.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
for f, _ in out: print(('改 ' if '--apply' in sys.argv else '乾跑 ') + os.path.relpath(f, ROOT))
