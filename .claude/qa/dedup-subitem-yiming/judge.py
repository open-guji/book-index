"""新-子目异名（含叢書子目、丛书异名或对单行本的同题组）逐对机判。
输入 $OUT/feat.json（../dedup-subitem-yi/feat.py 产出），输出 $OUT/pairs.tsv：每对一行，判 A（机械并）／C（分立）／R（交子 agent 核）。
判据：子目-乙判据（有效撰人含獨撰类继承丛书撰人、卷数串、同源丛书、纬书辑者）＋4a-α（子目缺撰人、所属丛书撰者＝单行本首位责任者）。"""
import json, os, re, sys, itertools, collections
ROOT = os.environ.get('BOOK_INDEX', '.')
S = os.environ.get('OUT', '/tmp/yiming')
os.environ['OUT'] = S
sys.argv = [sys.argv[0]]
exec(open(os.path.join(ROOT, '.claude/qa/dedup-subitem-yi/sig.py')).read().split('out=[]\nfor gi')[0])
DUNHUANG = ['鳴沙石室', '敦煌', '西陲祕籍']
WEI = {'孫瑴': ['墨海金壺', '守山閣叢書', '叢書集成初編', '玲瓏山館叢書'], '喬松年': ['山右叢書初編', '喬勤恪公全集'],
       '黃奭': ['漢學堂', '黃氏逸書考'], '劉學寵': ['青照堂叢書摘'], '說郛': ['說郛'], '袁鈞': ['十笏園叢刊'], '馬國翰': ['玉函山房輯佚書']}
def wei(c):
    for k, ks in WEI.items():
        if any(x in c for x in ks): return k
ANON = {'', '佚名', '闕名', '缺名', '無名氏', '不著撰人', '不著撰者', '不題撰人', '不詳', '撰者不詳', '□□'}
ORD = [('先秦', 0), ('春秋', 0), ('戰國', 0), ('周', 0), ('秦', 0), ('漢', 1), ('三國', 2), ('魏', 2), ('蜀', 2), ('吳', 2), ('晉', 2),
       ('南朝', 3), ('北朝', 3), ('劉宋', 3), ('齊', 3), ('梁', 3), ('陳', 3), ('北魏', 3), ('北齊', 3), ('北周', 3), ('隋', 4), ('唐', 4),
       ('五代', 5), ('後唐', 5), ('南唐', 5), ('前蜀', 5), ('後蜀', 5), ('宋', 6), ('趙宋', 6), ('遼', 6), ('金', 6), ('元', 7), ('明', 8),
       ('清', 9), ('民國', 10), ('中華民國', 10)]
def dord(d):
    d = (d or '').strip()
    if d in ('劉宋',): return 3
    for k, v in sorted(ORD, key=lambda x: -len(x[0])):
        if k in d: return v
    return None
def dcompat(da, db):
    oa = {dord(x) for x in da} - {None}; ob = {dord(x) for x in db} - {None}
    if not oa or not ob: return True
    return min(abs(x - y) for x in oa for y in ob) <= 1
WEIJI = {'孫瑴', '喬松年', '黃奭', '劉學寵', '馬國翰', '殷元正', '趙在翰', '袁鈞', '王仁俊', '王謨', '茆泮林', '陳喬樅'}
def info(w):
    ns, dy, src = names_of(w)
    first = None
    for a in w['authors']:
        n = nm(a[0])
        if n and n not in ANON: first = n; break
    if not first:
        for ti, ai, sec, sm in w['ib']:
            p = parse_ai(ai)
            if p:
                seg = re.split(r'[;；]', ai)[0]
                for n in p:
                    if n in nm(seg): first = n; break
                if first: break
    if not first and ns: first = sorted(ns)[0]
    ns = {n for n in ns if n not in ANON}
    for ti, ai, sec, sm in w['ib']:
        for seg in re.split(r'[;；]', ai or ''):
            for d in DYN:
                if seg.strip().startswith(d): dy.add(d); break
    if w['dyn']: dy.add(w['dyn'])
    js = {x[1] for x in juan_of(w)} - {None}
    secs = {sec or '' for ti, ai, sec, sm in w['ib']}
    return dict(inh=inherit(w), ns=ns, first=first, dy=dy, src=src, js=js, sub=bool(w['col']), secs=secs,
                eids={a[3] for a in w['authors'] if a[3]})
CLASSIC = set('周易 易經 尚書 書經 詩經 毛詩 周禮 儀禮 禮記 左傳 春秋 春秋左傳 公羊傳 穀梁傳 春秋公羊傳 春秋穀梁傳 論語 孟子 大學 中庸 孝經 爾雅 檀弓 易傳 夏小正 四書 五經 十三經 說文 說文解字'.split())
def inherit(w):
    if not any('獨撰類' in (sec or '') for ti, ai, sec, sm in w['ib']): return set()
    c = col.get(w['colrec'])
    return {nm(a['name']) for a in (c or {}).get('authors') or [] if a.get('name')}
def jrel(a, b):
    a = {x for x in a if isinstance(x, int)}; b = {x for x in b if isinstance(x, int)}
    if not a or not b: return '缺'
    if a & b: return '同'
    return '差1' if min(abs(x - y) for x in a for y in b) <= 1 else '悬殊'
def judge(g, a, b):
    ia, ib = I[a['id']], I[b['id']]
    if any(x in a['col'] + b['col'] for x in DUNHUANG): return 'D', '敦煌遺書（不碰名單），不判'
    jr = jrel(ia['js'], ib['js'])
    wa, wb = wei(a['col']), wei(b['col'])
    if ia['ns'] and ib['ns']:
        sa, sb = ia['ns'], ib['ns']
        same_first = ia['first'] and ia['first'] == ib['first']
        common = sa & sb
        if not common:
            if ia['inh'] & sb or ib['inh'] & sa:
                return 'R', '獨撰類子目著錄原書撰人，而所屬叢書撰者與另一側同（%s／%s）' % ('、'.join(sorted(sa)), '、'.join(sorted(sb)))
            oa = {dord(x) for x in ia['dy']} - {None}; ob = {dord(x) for x in ib['dy']} - {None}
            if oa and ob and ((min(oa) <= 2 and max(ob) >= 4) or (min(ob) <= 2 and max(oa) >= 4)):
                return 'R', '一側撰人為漢魏原書撰者／注者，疑著錄層次不同（%s／%s）' % ('、'.join(sorted(sa)), '、'.join(sorted(sb)))
            if not ({x[0] for x in sa} & {x[0] for x in sb}):
                return 'C', '撰人異（%s／%s）' % ('、'.join(sorted(sa)), '、'.join(sorted(sb)))
            return 'R', '同姓異名（%s／%s）' % ('、'.join(sorted(sa)), '、'.join(sorted(sb)))
        # 有共同撰人
        ja = (sa - sb) & WEIJI; jb = (sb - sa) & WEIJI
        if ja or jb:
            return 'C', '輯者不同（%s／%s），異輯本' % ('、'.join(sorted(sa)), '、'.join(sorted(sb)))
        if not dcompat(ia['dy'], ib['dy']): return 'R', '同撰人而朝代不合（%s／%s）' % ('、'.join(sorted(ia['dy'])), '、'.join(sorted(ib['dy'])))
        if jr == '悬殊': return 'R', '同撰人而卷數懸殊'
        if g['key'] in CLASSIC or len(g['key']) <= 2:
            return 'R', '經書本名，同撰人（%s）仍需核注本層次' % '、'.join(sorted(common))
        if sa == sb or (same_first and (sa <= sb or sb <= sa) and len(sa ^ sb) <= 1):
            src = '（獨撰類子目繼承叢書撰人）' if 'col' in (ia['src'], ib['src']) else ''
            return 'A', '同撰人（%s）%s，卷數%s' % ('、'.join(sorted(common)), src, {'同': '同', '缺': '一側缺', '差1': '差一'}[jr])
        return 'R', '撰人部分相同（%s／%s）' % ('、'.join(sorted(sa)), '、'.join(sorted(sb)))
    # 至少一侧无撰人
    if wa and wb and wa != wb and {wa, wb} & {'孫瑴', '喬松年', '黃奭', '劉學寵'}:
        return 'C', '緯書異輯（%s／%s）' % (wa, wb)
    if jr == '悬殊': return 'D', '一側缺撰人且卷數懸殊，待核'
    return 'R', '一側或兩側缺撰人（卷數%s）' % {'同': '同', '缺': '不明', '差1': '差一'}[jr]
if __name__ == '__main__':
    feat = json.load(open(S + '/feat.json'))
    I = {w['id']: info(w) for g in feat for w in g['works']}
    rows = []; c = collections.Counter()
    for gi, g in enumerate(feat):
        for a, b in itertools.combinations(g['works'], 2):
            v, why = judge(g, a, b); c[v] += 1
            ia, ib = I[a['id']], I[b['id']]
            rows.append((gi, g['key'], g['cat'], a['id'], b['id'], v, why, a['col'], b['col'],
                         '/'.join(sorted(ia['ns'])), '/'.join(sorted(ib['ns']))))
    print(c, len(rows))
    with open(S + '/pairs.tsv', 'w') as f:
        f.write('组\t题名\t普查类\tWork甲\tWork乙\t判定\t依据\t甲丛书\t乙丛书\t甲撰人\t乙撰人\n')
        for r in rows: f.write('\t'.join(map(str, r)) + '\n')
    json.dump(I, open(S + '/info.json', 'w'), ensure_ascii=False, default=lambda x: sorted(map(str, x)))
