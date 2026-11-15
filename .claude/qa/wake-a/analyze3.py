#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json, os, re, sys, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fetch2, fetch3, analyze2
from analyze2 import nz, era_year
S = fetch2.S
db = json.load(open(S + '/a_db.json')); works = json.load(open(S + '/a_works.json'))
bw = collections.defaultdict(list)
for b in db['books']: bw[b['work_id']].append(b)
CH = re.compile(r'書局|汲古|國子監|国子監|商務|中華|出版者不明|同文|官書|刊本局|石印|上海|北京|廣|广|蘇|金陵|浙江|崇文書|掃葉|[Pp]ress')
def bkyear(b):
    y = (b.get('dating') or {}).get('year')
    ed = b.get('edition') or ''
    ys = {y} if y else set()
    for m in re.finditer(r'(1[5-9]\d\d)', ed): ys.add(int(m.group(1)))
    e = era_year(ed.replace('丁未','').replace('(','').replace('（',''))
    if e: ys.add(e)
    # era with 乙亥(十二年) pattern: 文化乙亥(十二年)
    m = re.search(r'(' + analyze2.ERAS + r')[^\d元]{0,4}[(（]?([一二三四五六七八九十元]+)年', ed)
    if m:
        cn = {'元':1,'一':1,'二':2,'三':3,'四':4,'五':5,'六':6,'七':7,'八':8,'九':9}
        t = m.group(2); n = 10 if t == '十' else (10 + cn.get(t[1], 0) if t.startswith('十') else (cn.get(t[0], 0) * 10 + cn.get(t[2], 0) if len(t) == 3 and t[1] == '十' else (cn.get(t[0], 0) * 10 if len(t) == 2 and t[1] == '十' else cn.get(t, 0))))
        if n: ys.add(analyze2.ERA_START[m.group(1)] + n - 1)
    return ys
def pubs(x):
    p = x.get('dc:publisher') or []
    if isinstance(p, str): p = [p]
    return p
out = []
for w in works:
    W = db['works'][w['wid']]
    tset = {nz(w['title'])} | {nz(t) for t in W.get('additional_titles', [])}
    au = [nz(a) for a in w['au']]
    exist = [(b['id'], b.get('edition'), bkyear(b)) for b in bw[w['wid']]]
    cand = collections.defaultdict(list)
    seen = set()
    for src, lst in (('cinii', fetch3.items(fetch3.getj(fetch3.q(w['title'])))),):
        for x in lst:
            t = nz(re.sub(r'[,，]?\s*\d+[巻卷篇冊]?.*$', '', x['title']))
            if t not in tset: continue
            d = x.get('dc:date') or ''
            if not re.fullmatch(r'\d{4}', d): continue
            ps = pubs(x)
            if not ps or CH.search(' '.join(ps)): continue
            cre = nz(x.get('dc:creator') or '')
            aok = (not au) or any(a[:2] in cre for a in au) or not cre
            cand[(int(d), nz(ps[0].split('[')[0]))].append((x, aok))
    for k, v in sorted(cand.items()):
        ys = [e for e in exist if k[0] in e[2]]
        out.append(dict(i=w['i'], wid=w['wid'], wt=w['title'], au=w['au'], year=k[0], pub=k[1], n=len(v), aok=all(a for _, a in v), ncid=[x['@id'][-10:] for x, _ in v][:6], title=v[0][0]['title'], cre=v[0][0].get('dc:creator'), pubs=pubs(v[0][0]), owners=[x.get('cinii:ownerCount') for x, _ in v][:6], have=[e[0] for e in ys], nexist=len(exist), jpex=[(e[0], e[1], sorted(e[2])) for e in exist if e[1] and any(t in e[1] for t in ('日本','和刻','江戶','江户','寛','天保','文政','文化','明治'))]))
json.dump(out, open(S + '/a_c3.json', 'w'), ensure_ascii=False)
by = collections.defaultdict(list)
for o in out: by[o['i']].append(o)
for i, os_ in by.items():
    o0 = os_[0]; print('##', i, o0['wt'], o0['au'], 'existJP', [(a, b[:14], c) for a, b, c in o0['jpex']])
    for o in os_: print('   ', o['year'], o['pub'][:14], 'x%d' % o['n'], '作者ok' if o['aok'] else '作者?', 'HAVE' + str(o['have']) if o['have'] else '--NEW?', o['ncid'][:3], o['title'][:20], '|', (o['cre'] or '')[:24], '|', o['pubs'][:2])
print(len(out))
