#!/usr/bin/env python3
"""3c 補：已勘誤的責任者若仍掛著以誤字為主名的人物條目（含部分 2.3 後來新建者），
改掛同題正確著錄的人物；正確著錄無掛接則去掉掛接。用法：fix_entity_links.py [--apply]"""
import glob, json, os, sys, datetime
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
TODAY = datetime.date.today().isoformat()
def path(d, i):
    if len(i) < 3: return None
    h = glob.glob(os.path.join(ROOT, d, i[-3], i[-2], i[-1], i + '-*.json'))
    return h[0] if h else None
def load(p):
    return json.load(open(p, encoding='utf-8'))
def dump(p, d):
    with open(p, 'w', encoding='utf-8') as f:
        json.dump(d, f, ensure_ascii=False, indent=2); f.write('\n')
fixes = json.load(open(os.path.join(HERE, 'fixes-20261025.json'), encoding='utf-8'))
apply = '--apply' in sys.argv
orphans = []
# 同題正確著錄無掛接、但同批其餘著錄已掛定之人
OVERRIDE = {'僧肇': 'hixhd2h9bixi'}
for x in fixes:
    p = path('Work', x['wid'])
    if not p: continue
    d = load(p)
    if d.get('merged_into'): continue
    a = d['authors'][x['idx']] if x['idx'] < len(d.get('authors', [])) else None
    if not a or a.get('name') != x['new'] or not a.get('entity_id'): continue
    ep = path('Entity', a['entity_id'])
    e = load(ep) if ep else {}
    en = e.get('primary_name')
    alts = [z.get('name') for z in e.get('alt_names') or []]
    if en == a['name'] or a['name'] in alts: continue
    target = ''
    op = path('Work', x.get('other') or '')
    if op:
        o = load(op)
        for b in o.get('authors', []):
            if b.get('name') == a['name'] and b.get('entity_id'):
                target = b['entity_id']; break
    target = target or OVERRIDE.get(a['name'], '')
    old = a['entity_id']
    orphans.append((old, en, x['wid'], d['title']))
    print(x['wid'], d['title'], a['name'], '| 原掛', old, en, '→', target or '去掉')
    if not apply: continue
    if target: a['entity_id'] = target
    else: a.pop('entity_id')
    a['name_basis'] = a.get('name_basis', '') + '；原掛 Entity %s（主名「%s」，係誤字所建）%s' % (
        old, en, '改掛同題正確著錄之 %s' % target if target else '去掉掛接，待部分 2 處理')
    r = (d.get('revision') or '1.0.0').split('.'); r[2] = str(int(r[2]) + 1); d['revision'] = '.'.join(r)
    d['revised_at'] = TODAY
    d['ai_note'] = (d.get('ai_note') or '') + '；3c 補（%s）：authors[%d] 改正誤字所建人物之掛接' % (TODAY, x['idx'])
    dump(p, d)
json.dump(sorted(set(orphans)), open(os.path.join(HERE, '_orphans.json'), 'w'), ensure_ascii=False)
