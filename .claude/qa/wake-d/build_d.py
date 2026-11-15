#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""wake-d：補挂日本館藏、新建日本刊本 Book、寫台賬。用法：build_d.py [--apply]"""
import json, os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__)); BI = os.path.abspath(os.path.join(HERE, '../../..'))
sys.path.insert(0, os.path.join(BI, '.claude/qa')); sys.path.insert(0, HERE)
import mintid, decisions_d as D
APPLY = '--apply' in sys.argv
TODAY = '2026-11-15'; LANE = 'wake-d'
S = '/tmp/claude-0/-home-user/899c0af0-484b-5c15-91e5-4641de15fdd6/scratchpad'
shard = json.load(open(S + '/shard3.json')); BP = json.load(open(S + '/d_bookpaths.json'))
def jd(d): return json.dumps(d, ensure_ascii=False, indent=2) + '\n'
LINE = '和刻本日本館藏專項（車道 wake-d，2026-11-15）：'
changed = []
# ---- 補挂
for bid, (note, hold) in D.PATCH.items():
    p = os.path.join(BI, BP[bid]); b = json.load(open(p, encoding='utf-8'))
    prov = b.setdefault('provenance', []); have = {(x.get('institution'), x.get('call_number', '')) for x in prov}
    added = 0
    for inst, call, src in hold:
        if (inst, call) in have: continue
        e = {'institution': inst}
        if call: e['call_number'] = call
        e['source'] = src; prov.append(e); added += 1
    if not added: continue
    a, c, z = b['revision'].split('.'); b['revision'] = '%s.%s.%d' % (a, c, int(z) + 1); b['revised_at'] = TODAY
    line = LINE + '補挂日本館藏。依據：' + note + '。'
    b['ai_note'] = (b['ai_note'] + '\n' + line) if b.get('ai_note') else line
    changed.append((p, b))
# ---- 新建
ids = mintid.mint('Book', LANE, len(D.NEW)) if APPLY else ['dry%07d' % i for i in range(len(D.NEW))]
grp = {}
for (key, *_), bid in zip(D.NEW, ids): grp.setdefault(key.rstrip('0123456789'), []).append(bid)
newrows = []
for it, bid in zip(D.NEW, ids):
    key, wid, title, ed, et, reign, year, pub, place, meas, basis, desc, hold, ncids = it
    d = {'schema_version': 1, 'type': 'book', 'title': title, 'work_id': wid, 'edition': ed, 'edition_type': et,
         'dating': {'era': '日本', 'reign': reign, 'year': year, 'certainty': 'attested', 'source': 'catalog', 'basis': basis}}
    pi = {}
    if pub: pi['publisher'] = pub
    if place: pi['place'] = place
    if pi: d['publication_info'] = pi
    if meas: d['measures'] = [{'number': meas[0], 'unit': meas[1]}]
    d['provenance'] = [dict(institution=i, **({'call_number': c} if c else {}), source=s) for i, c, s in hold]
    srcs = [{'id': 'cinii-' + n.lower(), 'name': 'CiNii Books', 'type': 'url', 'details': 'https://ci.nii.ac.jp/ncid/' + n} for n in ncids]
    for m in re.findall(r'NDL (R\d+-I\d+)', basis): srcs.append({'id': 'ndl-' + m.lower(), 'name': 'NDL Search', 'type': 'url', 'details': 'https://ndlsearch.ndl.go.jp/books/' + m})
    d['description'] = {'text': desc, 'sources': ['%s %s' % (s['name'], s['details']) for s in srcs]}
    d['sources'] = srcs
    sib = [x for x in grp[key.rstrip('0123456789')] if x != bid]
    d['ai_note'] = LINE + '新建（庫內該 Work 下無此日本刊本）。據 CiNii Books 書誌與所藏館頁核定（刊者、年、卷冊、所藏館及索書號錄自該頁），未核原書。' + ('同 Work 下並列另立的日本刊本（異版，未硬並）：' + '、'.join(sib) + '。' if sib else '')
    d['id'] = bid; d['revision'] = '1.0.0'; d['revised_at'] = TODAY
    safe = re.sub(r'[\\/:*?"<>|（）() ,，;；「」《》、·]', '', ed)[:24]
    path = 'Book/%s/%s/%s/%s-%s%s.json' % (bid[-3], bid[-2], bid[-1], bid, title, safe)
    changed.append((os.path.join(BI, path), d)); newrows.append((bid, title, ed, hold, ncids))
# ---- 台賬
patched = set(D.PATCH); newwork = {}
rows = []
POST = re.compile(r'昭和|大正|民國|光緒三十一年|排印|影印|景印|石印|鉛印')
for x in shard:
    bid = x['id']; e = x['edition'] or ''
    if bid in patched:
        hs = '；'.join(sorted({h[0] for h in D.PATCH[bid][1]})); src = D.PATCH[bid][1][0][2].split('；')[0].split(' ', 2)[-1]
        rows.append((bid, x['title'], '補挂', hs, src, D.PATCH[bid][0])); continue
    if x['jp']: j, r = '無對應', '庫內已有日本館藏（總目著錄），未再補'
    elif POST.search(e) and '無求備齋' not in e: j, r = '無對應', '1912後影印／排印本，口徑不補'
    elif re.search(r'鈔本|抄本|寫本|鈔|抄|影鈔', e): j, r = '無對應', '日本鈔本：日本目錄中無法確認為同一抄本，不補'
    else: j, r = '存疑', 'NDL／CiNii 未檢得刊者年份俱合的同版，或同年有多種印次，不硬補'
    rows.append((bid, x['title'], j, '', '', r))
for bid, title, ed, hold, ncids in newrows:
    rows.append((bid, title, '新建', '；'.join(sorted({h[0] for h in hold})), 'https://ci.nii.ac.jp/ncid/' + ncids[0], ed))
tsv = '\n'.join('\t'.join(r) for r in [('Book id', '題名', '判定', '日本館藏', '依據URL', '說明')] + rows) + '\n'
print('補挂', len([1 for p, b in changed if b['revision'] != '1.0.0']), '新建', len(newrows), '台賬行', len(rows))
if not APPLY: sys.exit(0)
for p, d in changed:
    os.makedirs(os.path.dirname(p), exist_ok=True); open(p, 'w', encoding='utf-8').write(jd(d))
open(os.path.join(HERE, 'ledger.tsv'), 'w', encoding='utf-8').write(tsv)
json.dump([os.path.relpath(p, BI) for p, d in changed], open(os.path.join(HERE, 'changed.json'), 'w'), ensure_ascii=False, indent=0)
print('已寫')
