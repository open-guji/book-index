#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""和刻本專項第三輪（車道 wake-h，主題組 H）：小學類書與其它＋中井竹山《逸史》立 Work。
用法：build3.py [--apply] [--bi <worktree>] ；台賬 ledger3.tsv 同時寫出。腳本名唯一（build3_wakeh）。"""
import argparse, json, os, re, sys, importlib
HERE = os.path.dirname(os.path.abspath(__file__))
ap = argparse.ArgumentParser(); ap.add_argument('--apply', action='store_true'); ap.add_argument('--bi', default='/tmp/wk-wake-h3'); ap.add_argument('--mods', default='items_yishi')
A = ap.parse_args()
BI = A.bi; TODAY = '2026-11-15'
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(BI, '.claude/qa'))
import mintid
ITEMS = []
for m in A.mods.split(','):
    ITEMS += importlib.import_module(m).ITEMS
WORKS = importlib.import_module('works_new').WORKS if os.path.exists(os.path.join(HERE, 'works_new.py')) else []
def jd(d): return json.dumps(d, ensure_ascii=False, indent=2) + '\n'
files = {}; rows = []
wid = {}
if A.apply:
    nw = mintid.mint('Work', 'wake-h', len(WORKS)) if WORKS else []
else:
    nw = ['dryw%08d' % i for i in range(len(WORKS))]
for w, i in zip(WORKS, nw):
    d = dict(w['data']); d = {'schema_version': 1, 'id': i, 'type': 'work', **d}
    d['revision'] = '1.0.0'; d['revised_at'] = TODAY
    wid[w['key']] = i
    files['Work/%s/%s/%s/%s-%s.json' % (i[-3], i[-2], i[-1], i, d['title'])] = d
    rows.append((i, d['title'], '新建Work', '', '', ''))
ids = mintid.mint('Book', 'wake-h', len(ITEMS)) if (A.apply and ITEMS) else ['dry%07d' % i for i in range(len(ITEMS))]
for it, bid in zip(ITEMS, ids):
    wk = wid.get(it['work'], it['work'])
    d = {'schema_version': 1, 'type': 'book', 'title': it['title'], 'work_id': wk, 'edition': it['edition']}
    if it['etype']: d['edition_type'] = it['etype']
    dt = {'era': '日本', 'reign': it['reign']}
    if it.get('year'): dt['year'] = it['year']
    dt.update({'certainty': it['cert'], 'source': 'catalog', 'basis': it['dbasis']})
    d['dating'] = dt
    if it['pub']: d['publication_info'] = {'publisher': it['pub']}
    if it['meas']: d['measures'] = [{'number': n, 'unit': u} for n, u in it['meas']]
    prov = []; seen = set()
    for inst, call, src in it['hold']:
        if (inst, src) in seen: continue
        seen.add((inst, src)); e = {'institution': inst}
        if call: e['call_number'] = call
        e['source'] = src; prov.append(e)
    if prov: d['provenance'] = prov
    d['description'] = {'text': it['desc'], 'sources': [s[1] + ' ' + s[2] for s in it['src'][:3]]}
    d['sources'] = [{'id': i, 'name': n, 'type': 'url', 'details': u} for i, n, u in it['src']]
    d['ai_note'] = '2026-11-15 和刻本日本館藏專項第三輪（車道 wake-h）：據 NDL Search／CiNii Books 書目頁新建（庫內該 Work 原無此版）；版本名、刊年、出版者、館藏均錄自上列頁面，未核原書。' + it['note']
    d['id'] = bid; d['revision'] = '1.0.0'; d['revised_at'] = TODAY
    safe = re.sub(r'[\\/:*?"<>|（）() ,，;；「」《》、·]', '', it['edition'])[:24]
    files['Book/%s/%s/%s/%s-%s%s.json' % (bid[-3], bid[-2], bid[-1], bid, it['title'], safe)] = d
    rows.append((bid, it['title'], '新建', '、'.join(sorted({h[0] for h in it['hold']}))[:200], ' '.join(s[2] for s in it['src'][:3]), it['edition']))
print('Work', len(WORKS), 'Book', len(ITEMS))
if not A.apply:
    for p in files: print(p)
    sys.exit(0)
for pth, d in files.items():
    fp = os.path.join(BI, pth); os.makedirs(os.path.dirname(fp), exist_ok=True)
    open(fp, 'w', encoding='utf-8').write(jd(d))
QA = os.path.join(BI, '.claude/qa/wake-h'); os.makedirs(QA, exist_ok=True)
mode = 'a' if os.path.exists(os.path.join(QA, 'ledger3.tsv')) else 'w'
with open(os.path.join(QA, 'ledger3.tsv'), mode, encoding='utf-8') as f:
    if mode == 'w': f.write('Book id\t題名\t判定\t日本館藏\t依據URL\t版本\n')
    for r in rows: f.write('\t'.join(r) + '\n')
old = json.load(open(os.path.join(QA, 'files3.json'))) if os.path.exists(os.path.join(QA, 'files3.json')) else []
json.dump(old + list(files), open(os.path.join(QA, 'files3.json'), 'w'), ensure_ascii=False)
print('已寫', len(files))
wj = os.path.join(QA, 'wid.json'); o = json.load(open(wj)) if os.path.exists(wj) else {}
o.update(wid); json.dump(o, open(wj, 'w'), ensure_ascii=False)
