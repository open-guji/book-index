#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""和刻本專項第三輪·車道 wake-f（醫書組）：通名大 Work 的日本刊本窮盡。
用法：python3 build3.py [--apply]（在 repo 根目錄）。資料取自 CiNii Books NCID 頁（wf3_pn.py 解析，緩存 /tmp/wf_cache）。"""
import json, os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, '../../..'))
sys.path.insert(0, os.path.join(ROOT, '.claude/qa')); sys.path.insert(0, HERE)
from wf3_pn import parse
APPLY = '--apply' in sys.argv; TODAY = '2026-11-15'; LANE = 'wake-f'
CIN = lambda n: 'https://ci.nii.ac.jp/ncid/' + n
KN = '〇一二三四五六七八九'
def kn(n):
    if n == 1: return '元'
    s = ''
    if n >= 10:
        s += ('' if n // 10 == 1 else KN[n // 10]) + '十'
    return s + (KN[n % 10] if n % 10 else '')
SHIN = str.maketrans({'学':'學','図':'圖','属':'屬','医':'醫','総':'總','経':'經','済':'濟','薬':'藥','国':'國','際':'際','発':'發','児':'兒','広':'廣','関':'關','県':'縣','蔵':'藏','歯':'齒','体':'體','会':'會','号':'號','沢':'澤','辺':'邊','戸':'戶','仏':'佛','館':'館','・':'・','農':'農','録':'錄','専':'專','覚':'覺','応':'應','鉄':'鐵','単':'單','営':'營','気':'氣','対':'對','実':'實','写':'寫','来':'來','欧':'歐','圏':'圈','画':'畫','団':'團','当':'當','台':'臺','点':'點','様':'樣','門':'門','与':'與','両':'兩','学':'學','楽':'樂','観':'觀','読':'讀','処':'處','数':'數','徳':'德','駅':'驛','歴':'歷','縄':'繩','盤':'盤','専':'專'})
def inst(h):
    h = h.replace(' ', '')
    return h.translate(SHIN)
def prov_from(ncs, infos):
    out = []; seen = {}
    for nc in ncs:
        d = infos[nc]; prev = None
        for h in d['holders']:
            m = re.match(r'^(.+?)/([A-Za-z0-9\-\. ]+)$', h)
            if m and prev is not None:        # 「宮入文庫/C52」＝前一館的特藏＋索書號
                prev['notes'] = prev.get('notes', '') + ('；' if prev.get('notes') else '') + m.group(1).translate(SHIN); prev['call_number'] = m.group(2).replace(' ', ''); continue
            if re.match(r'^(史料室|財部文庫|.*文庫外.*|.*文庫)$', h.replace(' ', '')) and prev is not None and len(h) <= 8:
                prev['notes'] = prev.get('notes', '') + ('；' if prev.get('notes') else '') + h.replace(' ', '').translate(SHIN); continue
            if h.strip() in ('図書館', '図書室'): continue
            i = inst(h)
            if i in seen:
                continue
            prev = {'institution': i, 'source': 'CiNii Books ' + CIN(nc)}
            seen[i] = prev; out.append(prev)
    return out
def jd(d): return json.dumps(d, ensure_ascii=False, indent=2) + '\n'
def srcent(nc, label='CiNii Books 書目'):
    return {'id': 'cinii-' + nc.lower(), 'name': label, 'type': 'url', 'details': CIN(nc)}

from spec3 import SPEC
def main():
    import mintid
    infos = {}
    for r in SPEC:
        for nc in r['n']:
            if nc not in infos: infos[nc] = parse(nc)
    inlib = set(l.strip()[5:] for l in open('/tmp/claude-0/-home-user/899c0af0-484b-5c15-91e5-4641de15fdd6/scratchpad/f3_ncids.txt'))
    used = {}
    for r in SPEC:
        for nc in r['n']:
            if nc in inlib: print('!! 庫內已有 NCID', nc, r['t'])
            if nc in used: print('!! NCID 重複用於兩條', nc, used[nc], r['t'])
            used[nc] = r['t']
    ids = mintid.mint('Book', LANE, len(SPEC)) if APPLY else ['dry%07d' % i for i in range(len(SPEC))]
    files = []; log = []
    for r, bid in zip(SPEC, ids):
        ncs = r['n']; first = infos[ncs[0]]
        pub = r.get('pub', ''); extra = r.get('x', '')
        ed = '日本%s%s年（%d）%s刊本%s' % (r['g'], kn(r['rn']), r['y'], pub, extra) if not r.get('ed') else r['ed']
        prov = prov_from(ncs, infos)
        nh = sum(len(infos[nc]['holders']) for nc in ncs)
        flag = '' if prov else ' !!無所藏'
        cert = 'attested' if r.get('c', 'a') == 'a' else 'inferred'
        basis = 'CiNii Books 書目著錄刊年（%s）：%s' % (first['imprint'].split(',')[-1].strip() if ',' in first['imprint'] else first['imprint'], '、'.join(ncs[:3]))
        dating = {'era': '日本', 'reign': r['g'], 'year': r['y'], 'certainty': cert, 'source': 'catalog', 'basis': basis}
        d = {'schema_version': 1, 'type': 'book', 'title': r['t'], 'work_id': r['w'], 'edition': ed}
        d['edition_type'] = r.get('et', '刻本')
        d['dating'] = dating
        if r.get('j'): d['measures'] = [{'number': r['j'], 'unit': '卷'}]
        d['provenance'] = prov
        resp = first['resp']
        txt = '《%s》，%s。CiNii Books 著錄：%s；%s。日本和刻本（和刻本專項第三輪補建）。' % (r['t'], ed, first['imprint'], (first['extent'] or '') or '')
        d['description'] = {'text': txt, 'sources': ['CiNii Books ' + CIN(nc) for nc in ncs[:3]]}
        d['sources'] = [srcent(nc) for nc in ncs]
        memo = r.get('m', '')
        d['ai_note'] = '和刻本日本館藏專項第三輪（車道 wake-f，%s）：據 CiNii Books 書目頁（%d 條 NCID：%s；所藏館以各 NCID 頁為準）新建；刊年、書肆、校點者、卷冊錄自該書目頁（刊記／序跋／見返著錄），未核原書。%s' % (TODAY, len(ncs), '、'.join(ncs), memo)
        d['id'] = bid; d['revision'] = '1.0.0'; d['revised_at'] = TODAY
        safe = re.sub(r'[\\/:*?"<>|（）() ,，;；「」《》、·]', '', ed)[:24]
        path = os.path.join('Book', bid[-3], bid[-2], bid[-1], '%s-%s%s.json' % (bid, r['t'], safe))
        files.append(path)
        log.append(('新建', bid, r['t'] + '｜' + ed, ' / '.join(p['institution'] for p in prov) + flag, ' '.join(CIN(nc) for nc in ncs)))
        if APPLY:
            os.makedirs(os.path.dirname(os.path.join(ROOT, path)), exist_ok=True)
            open(os.path.join(ROOT, path), 'w', encoding='utf-8').write(jd(d))
    if APPLY:
        with open(os.path.join(HERE, 'ledger3.tsv'), 'w', encoding='utf-8') as fh:
            for x in log: fh.write('\t'.join(x) + '\n')
        open(os.path.join(HERE, 'changed_files3.txt'), 'w').write('\n'.join(files) + '\n')
    print(len(SPEC), '新建')
    for x in log: print(x[1], x[2][:60], '|', x[3][:120])
main()
