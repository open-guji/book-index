"""新-子目异名-集未：逐对机器初分档。输入 $P4WORK/zj-feat.json，输出 $P4WORK/zj-pairs.tsv。
档：A 同撰人卷不矛盾；B 一侧缺撰人但有同版／互见证据、卷不矛盾；B? 一侧或两侧缺撰人、卷同、无反证无证据；
C? 两侧有撰人而不同；D 卷数矛盾等。B?／C?／D 都要逐组人读（ovr.tsv 覆盖）。"""
import os, re, sys, json, itertools, collections, csv, glob
WK = os.environ.get('P4WORK', '/tmp/p4'); ROOT = os.path.abspath(os.path.dirname(__file__) + '/../../..')
sys.path.insert(0, ROOT + '/.claude/qa'); from scan import VARIANTS
F = json.load(open(WK + '/zj-feat.json'))
# 人物别名（只取本单元涉及的 entity）
need = set()
for g in F:
    for w in g['works']: pass
ALIAS = collections.defaultdict(set)
NUM = re.compile(r'[一二三四五六七八九十百千〇零]+(種|卷|集|冊|册)|不分卷|存[^）)]*|[（(][^）)]*[）)]')
def core(t): return NUM.sub('', (t or '')).translate(VARIANTS).strip()
FAM = [['說郛', '唐宋叢書', '說集', '五朝小說', '古今說海', '續百川學海', '廣百川學海'], ['四庫全書', '文淵閣', '文津閣', '文溯閣', '文瀾閣', '薈要'],
       ['六譯館'], ['天中許子', '許三禮'], ['海寧王忠慤公', '海寧王靜安'], ['潛園', '魏氏全書'], ['格致叢書', '百家名書', '壽養叢書', '胡氏粹編'],
       ['漢學堂'], ['青照堂'], ['微波榭', '戴氏遺書'], ['函海'], ['麗廔', '郋園', '雙楳景闇', '觀古堂'], ['夷門廣牘', '景印元明善本叢書'],
       ['顧亭林', '亭林先生遺書', '崑山顧氏'], ['船山遺書', '船山全書'], ['知不足齋'], ['學海類編'], ['津逮祕書', '津逮秘書'], ['寶顏堂'], ['稗海'], ['龍威祕書', '龍威秘書'], ['香豔叢書'], ['說庫']]
def fams(t):
    t = (t or '').translate(VARIANTS)
    return {i for i, ks in enumerate(FAM) if any(k.translate(VARIANTS) in t for k in ks)}
JUNK = re.compile(r'[0-9年敕]|本志|見|代$|^國朝|書院$')
TAIL = re.compile(r'(問|音|繪|續|删|刪|增修|增|等)$')
def names(w):
    s = set()
    for x in w['eff']:
        n = TAIL.sub('', x[0])
        n = re.sub(r'^(宋|元|明|清|唐|漢|晉|國朝)(?=..)', '', n) if x[3] != 'self' else n
        if len(n) >= 2 and not JUNK.search(n): s.add(n)
    return s
def chi(w): return any(re.search(r'敕', x[0]) for x in w['eff']) or any('敕' in (i[2] or '') for i in w['ib'])
def juans(w):
    s = set(w['bjuan']);
    if w['juan']: s.add(w['juan'])
    return s
def text(w):  # 一侧的版本／馆藏／summary 文本，查另一侧丛书名
    return ' '.join([' '.join(w['eds']), ' '.join(w['bcols']), ' '.join(i[3] for i in w['ib']), w['desc'], w['note']]).translate(VARIANTS)
def hx(a, b):
    """a 的著录或 Book 提到 b 所在丛书（或同家族）"""
    if not b['col']: return ''
    k = core(b['col']['title'])
    ta = text(a)
    if len(k) >= 3 and k[:4] in ta: return '%s見%s' % (a['id'][-4:], k[:4])
    fb = fams(b['col']['title'])
    if fb and fams(ta) & fb: return '%s同家族版本' % a['id'][-4:]
    return ''
SUR = lambda n: n[:1]
import pickle
EP = WK + '/zj-ent.pkl'
if os.path.exists(EP): N2E = pickle.load(open(EP, 'rb'))
else:
    N2E = collections.defaultdict(set)
    for p in glob.glob(ROOT + '/Entity/*/*/*/*.json'):
        e = json.load(open(p, encoding='utf-8'))
        if e.get('merged_into') or e.get('subtype') != 'people': continue
        for n in [e.get('primary_name')] + [x.get('name') for x in e.get('alt_names') or [] if isinstance(x, dict)]:
            if n and len(n) >= 2: N2E[n.translate(VARIANTS)].add(e['id'])
    N2E = dict(N2E); pickle.dump(N2E, open(EP, 'wb'))
print('人物名', len(N2E), file=sys.stderr); assert N2E
def alias(na, nb):
    for x in na:
        for y in nb:
            if N2E.get(x, set()) & N2E.get(y, set()): return '%s=%s' % (x, y)
    return ''
def xingjin(na, nb):
    for x in na:
        for y in nb:
            if len(x) == len(y) and x[0] == y[0] and sum(c1 != c2 for c1, c2 in zip(x, y)) == 1: return '%s≈%s' % (x, y)
    return ''
rows = []
for gi, g in enumerate(F):
    for a, b in itertools.combinations(g['works'], 2):
        na, nb = names(a), names(b)
        ja, jb = juans(a), juans(b)
        if ja and jb:
            jr = '同' if ja & jb else ('差1' if min(abs(x - y) for x in ja for y in jb) <= 1 else '悬殊')
        else: jr = '缺'
        da = {x[1] for x in a['eff'] if x[1]} | ({a['dyn']} if a['dyn'] else set()); db = {x[1] for x in b['eff'] if x[1]} | ({b['dyn']} if b['dyn'] else set())
        dconf = bool(da and db and not any(x in y or y in x for x in da for y in db))
        ev = hx(a, b) or hx(b, a)
        fa = fams(a['col']['title']) if a['col'] else set(); fb = fams(b['col']['title']) if b['col'] else set()
        famsame = bool(fa & fb) or bool(a['col'] and b['col'] and core(a['col']['title']) == core(b['col']['title']))
        if na and nb:
            acat = '同' if na & nb else ('别名' if alias(na, nb) else ('形近' if xingjin(na, nb) else ('同姓' if {SUR(x) for x in na} & {SUR(x) for x in nb} else '异')))
            if acat in ('别名', '形近'): ev = (ev + ' ' if ev else '') + (alias(na, nb) or xingjin(na, nb))
        elif chi(a) or chi(b): acat = '敕'
        else: acat = '缺'
        if acat == '同' and not dconf and jr != '悬殊': lv = 'A'
        elif acat in ('缺', '敕') and not dconf and jr in ('同', '差1', '缺') and (ev or famsame): lv = 'B'
        elif acat in ('缺', '敕') and not dconf and jr == '同': lv = 'B?'
        elif acat in ('别名', '形近') and jr != '悬殊': lv = 'B?'
        elif acat in ('异', '同姓') or dconf: lv = 'C?'
        else: lv = 'D'
        rows.append(dict(组=gi, 题名=g['key'], 部类=g['bulei'], 普查类=g['cat'], Work甲=a['id'], Work乙=b['id'], 机判=lv,
                         撰人=acat, 卷=jr, 朝代矛盾='是' if dconf else '', 证据=ev or ('同家族丛书' if famsame else ''),
                         甲丛书=(a['col'] or {}).get('title', '') or '单行', 乙丛书=(b['col'] or {}).get('title', '') or '单行',
                         甲撰人='、'.join(sorted(na)), 乙撰人='、'.join(sorted(nb)), 甲卷='/'.join(map(str, sorted(ja))), 乙卷='/'.join(map(str, sorted(jb)))))
with open(WK + '/zj-pairs.tsv', 'w', newline='') as f:
    wr = csv.DictWriter(f, fieldnames=list(rows[0]), delimiter='\t'); wr.writeheader(); wr.writerows(rows)
print('对', len(rows)); print(collections.Counter(r['机判'] for r in rows))
print(collections.Counter((r['机判'], r['撰人'], r['卷']) for r in rows).most_common(30))
