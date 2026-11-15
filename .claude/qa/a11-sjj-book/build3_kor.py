#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""第三輪·批2（朝鮮）：據 KORCIS 詳情（kor_cache.json）建 Work（諺解類）與 Book。用法：build3_kor.py [--apply]；須自 worktree 根或任意處運行（BI 自動推）。"""
import json, os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__)); BI = os.path.abspath(os.path.join(HERE, '../../..'))
sys.path.insert(0, os.path.join(BI, '.claude/qa')); sys.path.insert(0, HERE)
import mintid, data3_b2 as D
APPLY = '--apply' in sys.argv
TODAY = '2026-11-15'; LANE = 'a11-sjj-book'
K = json.load(open(os.path.join(HERE, 'kor_cache.json'), encoding='utf-8'))
def jd(d): return json.dumps(d, ensure_ascii=False, indent=2) + '\n'
def holdings(no):
    t = K[no]; i = t.index('MARC', t.index('시작권호')); j = next(n for n, x in enumerate(t) if x.startswith('도서관에 대한'))
    seg = t[i + 1:j]; out = []; n = 0
    while n < len(seg):
        if re.fullmatch(r'\d+', seg[n]) and n + 3 < len(seg):
            inst = seg[n + 3]; rest = []; m = n + 4
            while m < len(seg) and seg[m] != '목차': rest.append(seg[m]); m += 1
            call = rest[0] if rest and not re.match(r'^(卷|\d+-\d+\()', rest[0]) else ''
            vol = [x for x in rest if x != call]
            out.append((inst, call, vol)); n = m
        else: n += 1
    return out
def field(no, name):
    t = K[no]
    try: i = t.index(name)
    except ValueError: return ''
    return ' '.join(x for x in t[i + 2:i + 4] if x not in ('판사항', '발행사항', '형태사항', '주기사항', ':'))[:80]
newwork = {}; files = {}; rows = []
nw = len(D.WORKS); nb = len(D.B)
if APPLY: wids = mintid.mint('Work', LANE, nw); bids = mintid.mint('Book', LANE, nb)
else: wids = ['dryw%06d' % i for i in range(nw)]; bids = ['dryb%06d' % i for i in range(nb)]
for (key, (title, auth, roots, juan, desc)), wid in zip(D.WORKS.items(), wids):
    newwork[key] = wid
    wd = {'schema_version': 1, 'id': wid, 'type': 'work', 'title': title,
          'authors': [{'name': n, 'role': r, 'dynasty': '朝鮮'} for n, r in auth],
          'dynasty': '朝鮮',
          'related_works': [{'id': D.ROOT[r], 'relation': 'studies' if key == '三經四書釋義' else 'contains_text_of'} for r in roots],
          'period_upper': 'ming', 'period_upper_basis': 'catalog_bound：現存最早刊本為朝鮮光海君／宣祖朝刻本（見 Book 層 KORCIS 著錄），故成書不晚於明末'}
    if juan: wd['measures'] = [{'number': juan, 'unit': '卷'}]
    wd['description'] = {'text': desc, 'sources': ['韓國古文獻綜合目錄(KORCIS) https://www.nl.go.kr/korcis/']}
    wd['ai_note'] = '2026-11-15 十三經縱向補全·Book 層第三輪（朝鮮批）：庫內無此書而補建 Work；責任者、卷數據 KORCIS 書目著錄；未核原書。'
    wd['revision'] = '1.0.0'; wd['revised_at'] = TODAY
    files['Work/%s/%s/%s/%s-%s.json' % (wid[-3], wid[-2], wid[-1], wid, title)] = wd
for (wk, nos, ed, et, dt, extra), bid in zip(D.B, bids):
    wid = newwork.get(wk) or D.EXW[wk]; title = (D.WORKS[wk][0] if wk in D.WORKS else wk)
    reign, year, cert, basis = dt
    prov = []
    for no in nos:
        for inst, call, vol in holdings(no):
            p = {'institution': D.INST.get(inst, inst)}
            if call: p['call_number'] = call
            nt = '；'.join(x for x in ['KORCIS卷次欄：' + '、'.join(vol) if vol else '', 'KORCIS書目號' + no] if x)
            p['notes'] = nt; p['source'] = '韓國古文獻綜合目錄(KORCIS) 書目號%s' % no
            prov.append(p)
    d = {'schema_version': 1, 'type': 'book', 'title': title, 'work_id': wid, 'edition': ed, 'edition_type': et,
         'dating': {'era': '朝鮮', 'reign': reign, 'year': year, 'certainty': cert, 'source': 'catalog', 'basis': basis}}
    if len(nos) == 1:
        m = re.search(r'(\d+)冊', field(nos[0], '형태사항'))
        if m: d['measures'] = [{'number': int(m.group(1)), 'unit': '冊'}]
    d['provenance'] = prov
    src = [('korcis-' + no, '韓國古文獻綜合目錄(KORCIS)', 'https://www.nl.go.kr/korcis/ 書目號' + no) for no in nos]
    d['description'] = {'text': '%s：%s。館藏與請求記號據 KORCIS 書目詳情頁。' % (ed, extra), 'sources': ['%s %s' % (n, u) for _, n, u in src]}
    d['sources'] = [{'id': i, 'name': n, 'type': 'url', 'details': u} for i, n, u in src]
    d['ai_note'] = '十三經縱向補全·Book 層第三輪（2026-11-15，朝鮮批）：據 KORCIS 書目詳情頁（判種、發行事項、形態、館藏請求記號）核定，未核原書；方括號年份為編目者推定，已標 inferred。'
    d['id'] = bid; d['revision'] = '1.0.0'; d['revised_at'] = TODAY
    safe = re.sub(r'[\\/:*?"<>|（）() ,，;；「」《》、·]', '', ed)[:40]
    files['Book/%s/%s/%s/%s-%s%s.json' % (bid[-3], bid[-2], bid[-1], bid, title, safe)] = d
    rows.append((wk, nos, bid, ed))
print('Work', nw, 'Book', nb)
for p in files: print(p)
if not APPLY: sys.exit(0)
for pth, d in files.items():
    os.makedirs(os.path.join(BI, os.path.dirname(pth)), exist_ok=True)
    open(os.path.join(BI, pth), 'w', encoding='utf-8').write(jd(d))
json.dump({'rows': rows, 'files': list(files)}, open(os.path.join(HERE, 'result3_b2.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('已寫')
