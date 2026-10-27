#!/usr/bin/env python3
"""新-子目异名-史：逐对机判（子目-乙判据＋4a-α 口径），输出 pairs.tsv 供人工复核与 mkbatch。
用法（book-index 根目录）：python3 judge.py <feat.json> <out.tsv> [人工改判.tsv]
判定：A 同撰人（含獨撰類继承丛书撰者）且卷数不矛盾；B 总目互见（一侧非叢書部著录的版本列出另一侧所属丛书本）且撰人不矛盾、卷数不矛盾；
C 两侧撰人皆明确且不同；D 其余（无同源证据、卷数矛盾、互见但撰人异、泛称题名）。
已在 dedup-judged 的对、会把已判分立对连成一簇的边一律不并。"""
import csv, glob, itertools, json, os, re, sys
sys.path.insert(0, '.claude/qa'); sys.path.insert(0, 'scripts')
from scan import VARIANTS  # noqa: E402
F = json.load(open(sys.argv[1], encoding='utf-8'))
OVR = {}
if len(sys.argv) > 3:
    for r in csv.reader(open(sys.argv[3], encoding='utf-8'), delimiter='\t'):
        if r and not r[0].startswith('#'): OVR[frozenset(r[:2])] = (r[2], r[3])
# 已判分立／存疑对
JUDGED = {}
for p in glob.glob('.claude/qa/dedup-judged/*.tsv'):
    for r in csv.reader(open(p, encoding='utf-8'), delimiter='\t'):
        if len(r) >= 2 and re.fullmatch(r'[0-9a-z]{12}', r[0].lstrip('# ')) and re.fullmatch(r'[0-9a-z]{12}', r[1]):
            JUDGED[frozenset((r[0].lstrip('# '), r[1]))] = os.path.basename(p)
print('载入已判对', len(JUDGED), file=sys.stderr)
assert JUDGED
ANON = {'', '佚名', '闕名', '缺名', '無名氏', '不著撰人', '不著撰者', '不題撰人', '不詳', '撰者不詳'}
EXTRA = str.maketrans('粤峯琹', '粵峰琴')
def nm(s): return re.sub(r'[\s·・]', '', (s or '').translate(VARIANTS).translate(EXTRA))
DYN = sorted('先秦 周 秦 漢 西漢 東漢 後漢 三國 魏 蜀 吳 晉 晋 西晉 東晉 南朝 宋 齊 梁 陳 北魏 北齊 北周 隋 唐 五代 前蜀 後蜀 南唐 後唐 後晉 遼 金 元 明 清 民國 日本 朝鮮 高麗 南宋 北宋'.split(), key=len, reverse=True)
ROLE = re.compile(r'(等)?(奉敕撰|敕撰|撰|輯|編|錄|譯|注|註|著|纂|述|校|補遺|補|考|鈔|抄|選|評|訂|集|筆述|口授|增訂|重訂|彙編|參訂|同撰|合撰|箋|疏|釋|講|說|記|刪|定|批|點|圈點|手輯|修|譜|繪|書)+.*$')
RJI = re.compile(r'^(手)?輯(佚|錄|補|校)?$|^輯$|^(采|搜|纂)輯$')
RZHU = re.compile(r'注|註|箋|疏|解|評|點|批|校|音|考異|章句|釋|訂|刪|補')
def rclass(role):
    r = (role or '').strip()
    if re.search(r'撰|著|述|作', r): return 'pri'
    if '輯' in r and not re.search(r'編|纂', r): return 'ji'
    if RZHU.search(r): return 'zhu'
    return 'oth'   # 編、纂、閱、刻、錄等：可能是丛书编者／刻者，不作撰者异同的硬证据
ROLE2 = re.compile(r'((?:等)?(?:奉敕撰|敕撰|撰|輯|編|錄|譯|注|註|著|纂|述|校|補遺|補|考異|考|鈔|抄|選|評|訂|集|筆述|口授|增訂|重訂|彙編|參訂|同撰|合撰|箋|疏|釋|講|說|記|刪|定|批|點|圈點|手輯|修|譜|繪|書|音)+.*)$')
def parse_ai(ai):
    """著者串 → [(名, 角色类)]"""
    out = []
    for seg in re.split(r'[;；,，、]', ai or ''):
        tuo = bool(re.match(r'^(舊題|題|原題|舊本題)', seg.strip()))
        seg = re.sub(r'^(舊本題|舊題|題|原題)', '', seg.strip())
        if not seg or re.search(r'[見部類。:：]', seg): continue
        m = ROLE2.search(seg)
        role = m.group(1) if m else ''
        seg = seg[:m.start()] if m else seg
        segs = [seg]
        for d in DYN:   # 朝代字与姓同形（魏、陳、宋……），去与不去两样都留
            if seg.startswith(d) and len(seg) - len(d) >= 2: segs.append(seg[len(d):]); break
        cs = []
        for sg in segs:
            m2 = re.match(r'^(.*?)[（(](.*?)[）)]', sg)
            cs += [m2.group(1), m2.group(2)] if m2 else [sg]
        for c in cs:
            c = nm(c)
            if c and '□' not in c and len(c) <= 6 and c not in ANON: out.append((c, 'oth' if tuo else rclass(role)))
    return out
def eff(w):
    """有效撰人：{'pri','ji','zhu'} 名集合、朝代集合、entity、来源"""
    R = {'pri': set(), 'ji': set(), 'zhu': set(), 'oth': set()}; dy, eid = set(), set()
    for a in w['authors']:
        n = nm(a[0])
        if n and n not in ANON and '□' not in n: R[rclass(a[1])].add(n)
        if a[2]: dy.add(a[2].translate(VARIANTS))
        if a[3]: eid.add(a[3])
    for ti, ai, sec, sm in w['ib']:
        for n, c in parse_ai(ai): R[c].add(n)
    src = 'self' if any(R.values()) else ''
    if not src and any('獨撰類' in (x[2] or '') for x in w['ib']):
        for c in w['cols']:
            for a in c['auth']:
                n = nm(a[0])
                if n and n not in ANON: R['pri'].add(n)
                if a[2]: dy.add(a[2].translate(VARIANTS))
                if a[3]: eid.add(a[3])
        src = 'col' if R['pri'] else ''
    R['all'] = R['pri'] | R['ji'] | R['zhu'] | R['oth']
    return R, dy, eid, src
def edrole(w, e):
    """子目撰人与所属丛书编者同名（疑把丛书编者当子目撰人，4a-B EDROLE 规则）"""
    cn = {nm(a[0]) for c in w['cols'] for a in c['auth'] if a[0]}
    return bool(cn and e[0]['all'] and e[0]['all'] & cn and not any('獨撰類' in (x[2] or '') for x in w['ib']))
def relate(ea, eb):
    """→ (same, diff, 说明)"""
    A, B = ea[0], eb[0]
    if not A['all'] or not B['all']: return False, False, ''
    if A['ji'] and B['ji'] and not A['ji'] & B['ji']: return False, True, '輯者異'
    if A['zhu'] and B['zhu'] and not A['zhu'] & B['zhu'] and not (A['zhu'] & B['all'] or B['zhu'] & A['all']): return False, True, '注者異'
    if A['ji'] or B['ji']:
        j = (A['ji'] & B['all']) | (B['ji'] & A['all'])
        if j: return True, False, '輯者同（%s）' % '／'.join(sorted(j))
        return False, not (A['all'] & B['all']), '輯本對他本'
    if A['pri'] and B['pri']:
        if A['pri'] & B['pri'] or (ea[2] & eb[2]): return True, False, '撰者同（%s）' % '／'.join(sorted(A['pri'] & B['pri']) or ['同 entity'])
        return False, True, '撰者異'
    if A['all'] & B['all']: return True, False, '責任者同（%s）' % '／'.join(sorted(A['all'] & B['all']))
    return False, True, '責任者異'
CNUM = dict(zip('〇零一二兩三四五六七八九', [0, 0, 1, 2, 2, 3, 4, 5, 6, 7, 8, 9]))
def cn(t):
    n = cur = 0
    for ch in t:
        if ch in CNUM: cur = CNUM[ch]
        elif ch in '十百千': n += (cur or 1) * {'十': 10, '百': 100, '千': 1000}[ch]; cur = 0
    return n + cur
def juans(w):
    s = set()
    if w['juan']: s.add(w['juan'])
    for ti, ai, sec, sm in w['ib']:
        if not ti: continue
        t = re.sub(r'[（(][^）)]*[）)]', '', nm(ti))
        k = nm(w['title'])
        rest = t[len(k):] if t.startswith(k) else t
        m = re.match(r'[•]?([〇零一二兩三四五六七八九十百千]+)卷', rest)
        if m: s.add(cn(m.group(1)))
        elif '不分卷' in rest: s.add(0)
    return s
def jconf(a, b):
    if not a or not b: return False
    if a & b: return False
    # 不分卷对一卷视同
    if (a | b) <= {0, 1}: return False
    return True
NUMCUT = re.compile(r'[〇零一二兩三四五六七八九十百千□]+[種卷册冊𢎥集輯編].*$|[（(].*$')
def core(t):
    return NUMCUT.sub('', nm(t)).strip()
def col_cores(w):
    out = set()
    for c in w['cols']:
        for t in (c['title'], c['ctitle']):
            k = core(t or '')
            if len(k) >= 2: out.add(k)
    return out
P_BEN = re.compile(r'([^；;：:，,（(）)]+?)本(?:[（(]|$)')
def ben_tokens(w):
    """本 Work 非叢書部著录（总目单书著录）版本串里的「X本」"""
    toks = set()
    for ti, ai, sec, sm in w['ib']:
        if sec and sec.startswith('叢書部'): continue
        body = sm.split('：', 1)[1] if '：' in sm else sm
        for seg in re.split(r'[；;]', body):
            m = P_BEN.match(seg.strip())
            if m:
                t = nm(m.group(1))
                if len(t) >= 2: toks.add(t)
    return toks
def huxian(a, b):
    """a 的单书著录版本列出 b 所属丛书本"""
    ta, cb = ben_tokens(a), col_cores(b)
    for t in ta:
        for c in cb:
            if t == c or (len(t) >= 3 and t in c) or (len(c) >= 3 and c in t and not re.search(r'續|二集|三集|補編', t.replace(c, '', 1))):
                return f'{t}本'
    return ''
# 同源丛书家族（子目-乙判据第三节）
FAM = [('說郛系', ['說郛', '唐宋叢書', '說集']), ('六譯館', ['六譯館叢書']), ('天中許子', ['天中許子政學合一集', '許三禮遺書']),
       ('王國維遺書', ['海寧王忠慤公遺書', '海寧王靜安先生遺書']), ('魏元曠', ['潛園二十四種', '魏氏全書']),
       ('胡文煥', ['格致叢書', '百家名書', '壽養叢書', '胡氏粹編']), ('葉德輝', ['麗廔叢書', '郋園先生全書', '雙楳景闇叢書', '觀古堂彙刻書']),
       ('虞山鈔本', ['海虞雜志', '虞陽說苑', '虞陽說彙', '素心書屋叢鈔', '沈氏家藏秘笈', '沈氏家藏祕笈']),
       ('漢學堂', ['漢學堂叢書', '漢學堂知足齋叢書', '黃氏逸書考']), ('微波榭', ['微波榭叢書', '戴氏遺書']), ('函海', ['函海', '續函海'])]
def fams(w):
    out = set()
    for c in w['cols']:
        t = nm(c['title'])
        for k, ks in FAM:
            if any(nm(x) in t for x in ks): out.add(k)
    return out
GENERIC = set('詞 札記 雜志 雜誌 雜箸 雜著 藝文 水利 荒政 選舉 試帖 遊記 詞稿 對策 備忘 内篇 外篇 函稿 校勘記 詩訣 年譜 家譜 行狀 墓誌銘 傳 記 志 序 跋 附錄 日記 自序 自訂年譜 行述 事略 家傳 本傳 年表 世系 紀年 雜記 筆記 隨筆 文集 詩集 奏議 奏疏 疏稿 公牘 書牘 尺牘 圖說 圖 考 說 錄'.split())
DUN = ('敦煌', '鳴沙石室', '西陲祕籍', '西陲秘籍')
def dyn_ok(a, b):
    if not a or not b: return True
    for x in a:
        for y in b:
            if x == y or x in y or y in x: return True
            if {x, y} <= {'宋', '南宋', '北宋'} or {x, y} <= {'晉', '西晉', '東晉', '晋'} or {x, y} <= {'漢', '西漢', '東漢', '後漢'}: return True
    return False
rows = []
for gi, g in enumerate(F):
    ws = [w for w in g['works'] if not w['merged']]
    E = {w['id']: eff(w) for w in ws}
    J = {w['id']: juans(w) for w in ws}
    for a, b in itertools.combinations(ws, 2):
        k = frozenset((a['id'], b['id']))
        ea, eb = E[a['id']], E[b['id']]
        hx = huxian(a, b) or huxian(b, a)
        fm = fams(a) & fams(b) - {'說郛系'}   # 說郛各本归子目-甲，跨说郛系不凭家族并
        if fm and not hx: hx = '同源叢書家族%s' % '／'.join(sorted(fm))
        t = nm(g['key'])
        same, diff, rel = relate(ea, eb)
        strict = rel in ('撰者異', '輯者異') and not re.search(r'(志|圖經|圖志)$', t)
        inh = 'col' in (ea[3], eb[3]) or a['butu'] or b['butu'] or edrole(a, ea) or edrole(b, eb)
        jc = jconf(J[a['id']], J[b['id']])
        dok = dyn_ok(ea[1], eb[1])
        jb = [bool(e[0]['ji']) or any('輯佚類' in (x[2] or '') for x in w['ib']) for e, w in ((ea, a), (eb, b))]
        yuan = [bool(e[0]['pri']) and not e[0]['ji'] and not any('輯佚類' in (x[2] or '') for x in w['ib']) for e, w in ((ea, a), (eb, b))]
        if k in JUDGED: lv, why = 'X', '已判（%s）' % JUDGED[k]
        elif k in OVR: lv, why = OVR[k]
        elif any(d in (x[3] or '') + (x[2] or '') + (w['note'] or '') for w in (a, b) for x in w['ib'] for d in DUN) or any(d in (c['title'] or '') for w in (a, b) for c in w['cols'] for d in DUN):
            lv, why = 'D', '敦煌遺書，不碰'
        elif ((jb[0] and yuan[1]) or (jb[1] and yuan[0])) and not (ea[0]['all'] & eb[0]['all']):
            lv, why = 'D', '原書（史志著錄撰者）對輯佚本，是否同條待定（%s／%s）' % ('、'.join(sorted(ea[0]['all'])) or '缺', '、'.join(sorted(eb[0]['all'])) or '缺')
        elif jc:
            lv, why = ('C' if diff and strict and not inh else 'D'), '卷數矛盾（%s／%s）%s' % (sorted(J[a['id']]), sorted(J[b['id']]), '；撰人異' if diff else '')
        elif same and dok and t not in GENERIC and len(t) >= 2:
            lv, why = 'A', '同撰人：%s%s%s' % (rel, '，據叢書撰者' if 'col' in (ea[3], eb[3]) else '', '；總目互見' + hx if hx else '')
        elif same and not dok:
            lv, why = 'D', '同名撰人朝代不合（%s／%s）' % ('、'.join(sorted(ea[1])), '、'.join(sorted(eb[1])))
        elif hx and not diff and t not in GENERIC and len(t) >= 2:
            lv, why = 'B', '總目互見：單書著錄版本列「%s」，撰人不矛盾（%s／%s），卷數不矛盾' % (hx, '、'.join(sorted(ea[0]['all'])) or '缺', '、'.join(sorted(eb[0]['all'])) or '缺')
        elif diff and inh:
            lv, why = 'D', '撰人異（%s／%s），但一側撰人係據所屬叢書撰者繼承，待核' % ('、'.join(sorted(ea[0]['all'])), '、'.join(sorted(eb[0]['all'])))
        elif hx and diff:
            lv, why = 'D', '總目互見%s 但撰人異（%s／%s），待核' % (hx, '、'.join(sorted(ea[0]['all'])), '、'.join(sorted(eb[0]['all'])))
        elif diff and not strict:
            lv, why = 'D', '%s（%s／%s），無同源證據，非撰者／輯者明確相異，待核' % (rel, '、'.join(sorted(ea[0]['all'])), '、'.join(sorted(eb[0]['all'])))
        elif diff:
            lv, why = 'C', '%s（%s／%s），無同源證據' % (rel, '、'.join(sorted(ea[0]['all'])), '、'.join(sorted(eb[0]['all'])))
        else:
            lv, why = 'D', '%s，無互見或同撰人證據' % ('泛稱題名' if t in GENERIC or len(t) < 2 else '一側或兩側缺撰人')
        rows.append([gi, g['key'], a['id'], b['id'], lv, why,
                     '／'.join(c['title'] for c in a['cols']) or '單行', '／'.join(c['title'] for c in b['cols']) or '單行',
                     '、'.join(sorted(ea[0]['all'])), '、'.join(sorted(eb[0]['all'])), ','.join(map(str, sorted(J[a['id']]))), ','.join(map(str, sorted(J[b['id']])))])
with open(sys.argv[2], 'w', encoding='utf-8', newline='') as f:
    wr = csv.writer(f, delimiter='\t', lineterminator='\n')
    wr.writerow(['组', '题名', 'Work甲', 'Work乙', '判定', '依据', '甲丛书', '乙丛书', '甲撰人', '乙撰人', '甲卷', '乙卷'])
    wr.writerows(rows)
import collections
print(collections.Counter(r[4] for r in rows), len(rows), file=sys.stderr)
