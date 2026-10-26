#!/usr/bin/env python3
"""抽检取样：从挂接清单随机抽 N 条，附所在记录、所属 Work 与 Entity 摘要，供另一子 agent 复核。
    python3 spot.py <挂接清单.json> <N> <输出.jsonl> [种子]"""
import glob, json, os, random, sys
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))


def find(kind, i):
    h = glob.glob(os.path.join(ROOT, kind, i[-3], i[-2], i[-1], i + '-*.json'))
    return json.load(open(h[0], encoding='utf-8')) if h else {}


L = json.load(open(sys.argv[1], encoding='utf-8')); n = int(sys.argv[2])
random.seed(int(sys.argv[4]) if len(sys.argv) > 4 else 11)
with open(sys.argv[3], 'w', encoding='utf-8') as f:
    for x in random.sample(L, min(n, len(L))):
        r = json.load(open(os.path.join(ROOT, x['path']), encoding='utf-8'))
        w = find('Work', r['work_id']) if r.get('work_id') else {}
        e = find('Entity', x['entity_id'])
        f.write(json.dumps({'path': x['path'], 'slot': x['slot'], 'title': r.get('title'), 'edition': r.get('edition'), 'authors': r.get('authors'),
                            'section': ((r.get('indexed_by') or [{}])[0]).get('section'), 'work_title': w.get('title'), 'work_authors': w.get('authors'),
                            'attach_name': x['name'], 'tier': x.get('tier'), 'why': x.get('why'),
                            'entity': {'id': e.get('id'), 'name': e.get('primary_name'), 'dyn': e.get('dynasty'), 'dates': e.get('dates'), 'np': e.get('native_place'),
                                       'alt': e.get('alt_names'), 'note': (e.get('ai_note') or '')[:300]}}, ensure_ascii=False) + '\n')
print('抽样', min(n, len(L)))
