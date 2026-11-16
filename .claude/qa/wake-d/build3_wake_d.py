#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""wake-d 第三輪：史部通名書（史記評林、漢書評林、三國志、資治通鑑、通鑑綱目、十八史略、貞觀政要、國語、唐鑑）
日本刊本窮盡。由 gen3_wake_d.py 的候選簇（/tmp/wk_d3_cand.json）+ 人工取捨表生成 Book。
用法：build3_wake_d.py [--apply]"""
import json, os, re, sys, collections
HERE = os.path.dirname(os.path.abspath(__file__)); BI = os.path.abspath(os.path.join(HERE, '../../..'))
sys.path.insert(0, os.path.join(BI, '.claude/qa')); sys.path.insert(0, HERE)
import wk3lib as L
APPLY = '--apply' in sys.argv
TODAY = '2026-11-15'; LANE = 'wake-d'
CI = 'https://ci.nii.ac.jp/ncid/'
CAND = json.load(open(os.environ.get('WK3_CAND', os.path.join(HERE, 'cand3.json'))))
JP = json.load(open(os.environ.get('WK3_JP', '/tmp/wk_d3_jpbooks.json')))
SKIP = set(json.load(open(os.path.join(HERE, 'skip3.json')))) if os.path.exists(os.path.join(HERE, 'skip3.json')) else set()
FORCE = set(json.load(open(os.path.join(HERE, 'force3.json')))) if os.path.exists(os.path.join(HERE, 'force3.json')) else set()
TAIL = json.load(open(os.path.join(HERE, 'tail3.json'))) if os.path.exists(os.path.join(HERE, 'tail3.json')) else {}
def jd(d): return json.dumps(d, ensure_ascii=False, indent=2) + '\n'
def nt(s): return L.trad(re.sub(r'[\s　]', '', s))
def shops(publine):
    p = publine.rsplit(',', 1)[0] if re.search(r',\s*[^,]*\d{4}\]?', publine) else publine
    p = re.sub(r'\[ほか\]|\[?ほか\]?|\(發行\)|\(發兌\)|\(發売\)|\(藏版\)|\(板行\)|\(賣捌\)', '', p)
    return [nt(x).strip('[]') for x in re.split(r'[,:;]', p) if nt(x).strip('[]')]
MERGEYEAR = {'國語', '十八史略', '漢書評林', '三國志'}
def key(o): return '%s|%s|%s' % (o['target'], o['year'], o['pub'])
# 合併同年且書肆集有交集的簇（同一書肆聯合體的不同排序）
def merge(cs):
    byt = collections.defaultdict(list)
    for o in cs: byt[(o['target'], o['year'])].append(o)
    out = []
    for k, l in byt.items():
        grp = []
        l = sorted(l, key=lambda o: -o['n'])
        if k[0] in MERGEYEAR:
            grp = [dict(items=l, sh=set())]; l = []
        for o in l:
            sh = set(s for s in shops(o['pubfull']) if len(s) >= 3)
            for g in grp:
                if g['sh'] & sh: g['items'].append(o); g['sh'] |= sh; break
            else: grp.append(dict(items=[o], sh=sh))
        for g in grp:
            it = g['items']
            m = dict(it[0]); m['ncids'] = [n for o in it for n in o['ncids']]; m['dup'] = sorted(set(d for o in it for d in o['dup']))
            m['keys'] = [key(o) for o in it]
            out.append(m)
    return sorted(out, key=lambda o: (o['target'], o['year']))
def vols_of(t):
    m = re.findall(r'(\d+)[巻卷]', t); return int(m[0]) if m else None
def build():
    cs = merge(CAND); res = []
    for o in cs:
        ks = o['keys']
        if o['dup'] and not any(k in FORCE for k in ks): continue
        if any(k in SKIP for k in ks): continue
        info = []
        for n in o['ncids'][:6]:
            info.append(L.ncid(n))
        info = [i for i in info if i['title']]
        if not info: continue
        prim = next((i for i in info if '存' not in i['title'] and '缺' not in i['title'] and '欠' not in i['title']), info[0])
        res.append((o, prim, info))
    return res
def main():
    res = build(); N = []
    for o, prim, info in res:
        sh = shops(prim['publine']); y = o['year']
        yrs = nt(o['yr']); mm = re.match(r'([^\d\s]+?)(元|\d+)', yrs)
        reign = mm.group(1) if mm else ''; ky = '元' if mm and mm.group(2) == '元' else (L.kanji_year(mm.group(2)) if mm else '')
        reign = reign.replace('年', '')
        title = re.sub(r'\s*,?\s*\d+[巻卷].*$', '', nt(prim['title'])).strip(' ,')
        title = re.sub(r'\s*[,，]?\s*\d+[巻卷].*$', '', title)
        place = nt(prim['place']) if prim['place'] else ''
        pl1 = place if place in ('京都', '大阪', '江戶', '大坂', '名古屋', '東京') else ''
        pubs = sh[:2]; tail = '等' if len(sh) > 2 else ''
        ed = '日本%s%s年%s%s%s刊' % (reign, ky, pl1, '、'.join(pubs), tail)
        t3 = TAIL.get(o['target'] + '|' + str(o['year']) + '|' + o['pub']) or ''
        ed += t3 if t3 else '本'
        vols = [vols_of(i['title']) for i in info if '存' not in i['title'] and vols_of(i['title'])]
        meas = [{'number': max(vols), 'unit': '卷'}] if vols else []
        ce = re.search(r'(\d+)冊', prim['vols'] or '')
        if ce: meas.append({'number': int(ce.group(1)), 'unit': '冊'})
        prov = []
        seen = set()
        for i in info:
            for lib, cn in i['holders'][:3]:
                lib = nt(lib)
                if lib in seen: continue
                seen.add(lib); cn = cn.strip()
                if re.fullmatch(r'\d{1,3}', cn): cn = ''
                d = {'institution': lib}
                if cn: d['call_number'] = cn
                d['source'] = 'CiNii Books ' + CI + i['ncid']
                prov.append(d)
        notes = [n for n in prim['notes'] if re.search(r'刊記|題簽|見返|版心|訓点|頭注|首書|蔵版|藏版|序|跋|校|點|匡廓|封面|奥付|奧付|刻', n) and len(n) < 300 and not n.startswith('和漢古書')]
        desc = nt(prim['au']) + '。'
        desc += '出版者：' + '、'.join(sh) + '；' + nt(o['yr']) + '。'
        if prim['vols']: desc += 'CiNii 著錄：' + nt(prim['vols']) + '。'
        if notes: desc += 'CiNii 注記：' + '；'.join(nt(n) for n in notes[:5]) + '。'
        ids = [i['ncid'] for i in info]
        srcs = [{'id': 'cinii-' + n.lower(), 'name': 'CiNii Books', 'type': 'url', 'details': CI + n} for n in ids]
        N.append(dict(o=o, prim=prim, info=info, title=title, ed=ed, reign=reign, year=y, pubs=sh, place=place, meas=meas, prov=prov, desc=desc, srcs=srcs, ids=ids, notes=notes))
    ids = __import__('mintid').mint('Book', LANE, len(N)) if APPLY else ['dry%07d' % i for i in range(len(N))]
    for n, bid in zip(N, ids): n['bid'] = bid
    grp = collections.defaultdict(list)
    for n in N: grp[(n['o']['work'], n['year'])].append(n)
    files = {}; rows = [('Book id', '題名', '判定', '日本館藏', '依據URL', '說明')]
    for n in N:
        o = n['o']; bid = n['bid']
        d = {'schema_version': 1, 'type': 'book', 'title': n['title'], 'work_id': o['work'], 'edition': n['ed'], 'edition_type': '刻本',
             'dating': {'era': '日本', 'reign': n['reign'], 'year': n['year'], 'certainty': 'attested', 'source': 'catalog',
                        'basis': 'CiNii Books %s 著錄出版者%s、%s' % (n['prim']['ncid'], '、'.join(n['pubs'][:3]), nt(o['yr']))}}
        pi = {'publisher': '、'.join(n['pubs'])}
        if n['place']: pi['place'] = n['place']
        d['publication_info'] = pi
        if n['meas']: d['measures'] = n['meas']
        if n['prov']: d['provenance'] = n['prov']
        d['description'] = {'text': n['desc'], 'sources': ['CiNii Books ' + CI + x for x in n['ids']]}
        d['sources'] = n['srcs']
        sib = [x['bid'] for x in grp[(o['work'], n['year'])] if x['bid'] != bid]
        exist = [b['id'] + '（' + (b.get('edition') or '') + '）' for b in JP if b['work_id'] == o['work'] and abs(((b.get('dating') or {}).get('year') or 0) - n['year']) <= 1]
        note = ('和刻本日本館藏專項第三輪（車道 wake-d，2026-11-15）：新建（庫內該 Work 下無此刊年書肆之日本刊本；已對全庫日本刊本核查）。'
                '據 CiNii Books 書誌頁核定（出版者、刊年、卷冊、所藏館及索書號錄自該頁），未核原書。同簇共 %d 條 NCID，所藏館錄自其中至多 6 條；書肆名、年號依 CiNii 著錄。' % len(o['ncids']))
        if sib: note += '同 Work 同年並列另立的刊本（書肆不同或印次不明，未硬並）：' + '、'.join(sib) + '。'
        if exist: note += '庫內同年既有日本刊本（互記，不硬並）：' + '；'.join(exist) + '。'
        d['ai_note'] = note
        d['id'] = bid; d['revision'] = '1.0.0'; d['revised_at'] = TODAY
        safe = re.sub(r'[\\/:*?"<>|（）() ,，;；「」《》、·\[\]]', '', n['ed'])[:26]
        files['Book/%s/%s/%s/%s-%s%s.json' % (bid[-3], bid[-2], bid[-1], bid, n['title'][:20], safe)] = d
        rows.append((bid, n['title'], '新建', '；'.join(dict.fromkeys(p['institution'] for p in n['prov'])) or '（NCID 頁無所藏明細）', CI + n['prim']['ncid'], n['ed']))
    print('新建', len(N))
    for p in files: print(p)
    if not APPLY: return
    for p, d in files.items():
        os.makedirs(os.path.join(BI, os.path.dirname(p)), exist_ok=True); open(os.path.join(BI, p), 'w', encoding='utf-8').write(jd(d))
    open(os.path.join(HERE, 'ledger3.tsv'), 'w', encoding='utf-8').write('\n'.join('\t'.join(r) for r in rows) + '\n')
    json.dump(list(files), open(os.path.join(HERE, 'changed3.json'), 'w'), ensure_ascii=False, indent=0)
    print('已寫')
if __name__ == '__main__': main()
