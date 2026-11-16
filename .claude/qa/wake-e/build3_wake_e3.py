#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""和刻本專項第三輪·車道 wake-e（主題組 E 諸子）：通名大 Work 穷尽，新建日本刊本 Book。用法 build3_wake_e3.py [--apply]
依據：CiNii Books 檢索（count=200 分頁）→ 簇（刊年+書肆）→ NCID 頁（刊記、所藏館）。"""
import json, os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__)); BI = os.path.abspath(os.path.join(HERE, '../../..'))
sys.path.insert(0, os.path.join(BI, '.claude/qa')); sys.path.insert(0, HERE)
import spec_wake_e3 as sp
from final_spec_wake_e3 import FINAL
APPLY = '--apply' in sys.argv; TODAY = '2026-11-16'; LANE = 'wake-e'
S = '/tmp/claude-0/-home-user/899c0af0-484b-5c15-91e5-4641de15fdd6/scratchpad/'
R = json.load(open(S + 'e_ncidpages.json'))
EXCL = {'BA62021513', 'BB16430779'}  # 奧付書肆集合不同（後印）／見返「內閣藏板」，不併入
DROP = {'lw-dy1788', 'ly-1748', 'lsz-1751', 'zj-1681', 'zj-1825', 'zs-1822', 'zh-1802', 'sz-1864', 'ld-tm1705', 'lz-uk1657', 'lf-1810', 'ld-zx1803', 'lx-1773', 'lzy-1787', 'lyj-1797', 'lsj-1813', 'lb-1770', 'lg-1773'}
CH = dict(zip('学図属総関蔵国会経済広沢当号数対応芸医台専権歴',
              '學圖屬總關藏國會經濟廣澤當號數對應藝醫臺專權歷'))
def conv(s):
    return ''.join(CH.get(c, c) for c in s)
def inst(d):
    seg = d['hold'].split('| 件 |', 1)
    f = seg[1].split('|')[0].strip() if len(seg) > 1 else ''
    if not f: return None
    f = f.replace('大学共同利用機関法人 人間文化研究機構 ', '').replace('附属図書館 中央図書館', '附属図書館')
    f = f.replace(' 大学院人文社会系研究科・文学部', ' 大学院人文社会系研究科').replace('情報管理施設', '').strip()
    return conv(re.sub(r'\s+', '', f))
KIKI = re.compile(r'(刊記|奥付|奧付|見返|木記|封面|奥書|版記|識語)')
def kiki(d):
    ps = d['note'].split(' / ')
    for pri in (r'刊記|奥付|奧付|木記', r'版記|奥書|封面|巻末|卷末', r'見返'):
        for p in ps:
            if re.search(pri, p):
                m = re.search(r'「([^」]{6,70})」', p)
                if m and re.search(r'[年歳]|屋|堂|館|板|梓|刊|藏|蔵|鎸|鐫|新|補刻', m.group(1)) and '製本所' not in p and '識語' not in p and '書目' not in p:
                    return conv(p[:110].strip())
    return None
def jd(d): return json.dumps(d, ensure_ascii=False, indent=2) + '\n'
SIB = {'lh-1667a': 'lh-1667b', 'lh-1667b': 'lh-1667a', 'mz-1835a': 'mz-1835b', 'mz-1835b': 'mz-1835a'}
XSIB = {'ld-nd1732': ('ld-sw1774', '安永三年須原屋平左衞門等刊本（%s）版心亦有「盧橘堂」，疑為同板後印，未能確認，故分立互見。'),
        'ld-sw1774': ('ld-nd1732', '享保十七年野田太兵衞刊本（%s）版心亦有「盧橘堂」，疑為其板木後印，未能確認，故分立互見。'),
        'zy-1653': ('zy-1751', '寬延四年勝村治右衞門後修本（%s）刊記沿承應二年原刊記，互見。'),
        'zy-1751': ('zy-1653', '承應二年小嶋市郎右衞門原刊本（%s），互見。')}
FIN = [f for f in FINAL if f[0] not in DROP]
import mintid
ids = mintid.mint('Book', LANE, len(FIN)) if APPLY else ['dryb%06d' % i for i in range(len(FIN))]
idof = {f[0]: i for f, i in zip(FIN, ids)}
changed = []; rows = []
for f, bid in zip(FIN, ids):
    key, skeys, wk, title, reign, year, cert, pub, ed, et = f
    ncids = []
    for k, w, t, sels in sp.SPEC:
        if k in skeys:
            for s in sels: ncids += sp.sel(*s)
    ncids = [x for x in sorted(set(ncids))[:12] if x not in EXCL]
    prov = []; insts = []; srcs = []; kk = []
    for n in ncids:
        d = R[n]; i = inst(d)
        url = 'https://ci.nii.ac.jp/ncid/' + n
        srcs.append({'id': 'cinii-' + n, 'name': 'CiNii Books', 'type': 'url', 'details': url})
        if i:
            prov.append({'institution': i, 'source': 'CiNii Books ' + url})
            if i not in insts: insts.append(i)
        x = kiki(d)
        if x and x not in kk: kk.append(x)
    if not prov: raise SystemExit('no holders ' + key)
    vol = ''
    for k, w, t, sels in sp.SPEC:
        if k == skeys[0]:
            for s in sels:
                for kx, v in sp.CL:
                    if kx[2] == s[0]:
                        for r in v:
                            if s[1] in r[1] and ((s[2][1:] == r[3][:len(s[2]) - 1]) if s[2].startswith('^') else (s[2] in r[3])):
                                m = re.search(r'(\d+)\s*[巻卷]', r[1]); vol = m.group(0).replace('巻', '卷') if m else vol
    dtxt = '《%s》，%s。%s%s%s藏。' % (title, ed, (vol + '。') if vol else '', ('CiNii著錄：' + kk[0] + '。') if kk else '', '、'.join(insts[:8]) + ('等' if len(insts) > 8 else ''))
    sib = SIB.get(key)
    if sib and sib in idof: dtxt += '同年另有%s刊本（%s），疑同版異肆印次，未能確認，故分立互見。' % ('千鍾房' if key == 'mz-1835a' else '松本氏', idof[sib]) if key.startswith('mz') else '同年另有另一書肆刊本（%s），未能確認是否同版，故分立互見。' % idof[sib]
    if key == 'sw-1852': dtxt += '同板系另有天保四年昌平坂學問所官板山城屋佐兵衞發行本（99ju75ipkx），本條為嘉永五年出雲寺萬次郎重印，互見。'
    if key in XSIB and XSIB[key][0] in idof: dtxt += XSIB[key][1] % idof[XSIB[key][0]]
    basis = ('CiNii Books 著錄刊年 %d（%s）；刊記／見返／奧書所載' % (year, reign)) if cert == 'attested' else ('CiNii Books 著錄 %d（%s）；該年為序跋年，非確證刊年' % (year, reign))
    note = '2026-11-16 和刻本日本馆藏专项第三輪（wake-e，通名大Work穷尽）：據CiNii Books 著錄新建（出版者、刊年、刊記錄自該等記錄，所藏館取自NCID頁「大學圖書館所藏」），未核原書；已對origin/main跨Work查重。'
    if key == 'zn-1739': note += '部分館藏見返作「平安書肆藤花房（或作藤書房）／東都書舗錦山房合梓」，奧付／刊記同為元文四年五月，視為同一發行，未析。'
    if len(skeys) > 1 or len(ncids) > 1: note += '本條合併 %d 筆 NCID（%s），其出版事項、刊記一致；各館著錄的共同發行書肆略有出入，未析。' % (len(ncids), '、'.join(ncids[:12]))
    dd = {'schema_version': 1, 'type': 'book', 'title': title, 'work_id': wk, 'edition': ed}
    if et: dd['edition_type'] = et
    dd['dating'] = {'era': '日本', 'reign': reign, 'year': year, 'certainty': cert, 'source': 'catalog', 'basis': basis}
    if pub: dd['publication_info'] = {'publisher': pub, 'place': '日本'}
    dd.update({'provenance': prov, 'description': {'text': dtxt, 'sources': [s['details'] for s in srcs]}, 'sources': srcs, 'ai_note': note,
               'id': bid, 'revision': '1.0.0', 'revised_at': TODAY})
    safe = re.sub(r'[\\/:*?"<>|（）() ,，;；「」《》、·・]', '', ed)[:24]
    p = 'Book/%s/%s/%s/%s-%s%s.json' % (bid[-3], bid[-2], bid[-1], bid, title, safe)
    changed.append((p, dd)); rows.append((bid, title, '新建', '、'.join(insts), '; '.join(s['details'] for s in srcs[:4]), key))
for p, d in changed: print(p)
if APPLY:
    for p, d in changed:
        os.makedirs(os.path.dirname(os.path.join(BI, p)), exist_ok=True)
        open(os.path.join(BI, p), 'w', encoding='utf-8').write(jd(d))
    open(os.path.join(HERE, 'files3.txt'), 'w').write('\n'.join(p for p, _ in changed) + '\n')
    with open(os.path.join(HERE, 'ledger3.tsv'), 'w') as fo:
        fo.write('Book id\t題名\t判定\t日本館藏\t依據URL(前4)\t簇key\n')
        for r in rows: fo.write('\t'.join(r) + '\n')
