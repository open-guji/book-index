"""子目-甲：由 feat_sub.json 判出可并簇。同一组（同题）里，所属丛书题名去卷种数后相同的叢書子目 Work 成簇；
簇内：各条所挂 Collection 互不相同（同一 Collection 内同题两条疑为异篇，不并）、子目自身首位责任者至多一个且朝代相容、
所属 Collection 首位撰者至多一个、卷数（Work juan_count／Book juan_count／title_info 里的卷数）全等或缺，即并。
跳过 4a-α 清单里的 Work id。用法：P4WORK=<目录> python3 cand_sub.py <4a-alpha.json> [--judged 输出 dedup-judged tsv]"""
import os, sys, json, re, collections
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__) + '/../../../scripts'))
from importlib import import_module
cen = import_module('dedup-census')
norm_name, ANON = cen.norm_name, cen.ANONYMOUS
WK = os.environ['P4WORK']
G = json.load(open(WK + '/feat_sub.json'))
alpha = set()
for c in json.load(open(sys.argv[1])):
    alpha |= {c['keeper'], *c['losers']}
CN = '〇一二三四五六七八九'
def cn2i(s):
    s = s.replace('零', '〇')
    if all(ch in CN for ch in s) and len(s) > 1:
        return int(''.join(str(CN.index(ch)) for ch in s))
    n, cur = 0, 0
    for ch in s:
        if ch in CN: cur = CN.index(ch)
        elif ch == '十': n += (cur or 1) * 10; cur = 0
        elif ch == '百': n += (cur or 1) * 100; cur = 0
        elif ch == '千': n += (cur or 1) * 1000; cur = 0
    return n + cur
JR = re.compile(r'^[^附]*?([〇零一二三四五六七八九十百千]+)卷')
def tjuan(t):
    m = JR.search(t or '')
    return cn2i(m.group(1)) if m else ('不分卷' if '不分卷' in (t or '') else None)
def fa(m):
    a = [x for x in m['authors'] if x[0]]
    if not a: return None
    n = norm_name(a[0][0])
    return None if n in ANON else n
DYN = {'清': {'清'}, '明': {'明'}}
NUM = re.compile(r'[〇零一二三四五六七八九十百千]+(種|卷|集|冊)|不分卷|存')
# 同一丛书的异称（Collection 题名改写或丛书改名重印）：文淵閣本、薈要摛藻堂本；黃奭《漢學堂叢書》即《黃氏逸書考》
ALIAS = {'欽定四庫全書文淵閣本': '文淵閣四庫全書', '欽定四庫全書薈要摛藻堂本': '摛藻堂四庫全書薈要', '黃氏逸書考附': '漢學堂叢書', '黃氏逸書考': '漢學堂叢書'}
def ctnorm(t):
    n = cen.norm(NUM.sub('', t or ''))
    return ALIAS.get(n, n)
out, judged, skip = [], [], collections.Counter()
for g in G:
    by = collections.defaultdict(list)
    for m in g['members']:
        if m['parent'] and m['bookcols']:
            by[m['parent'][2]].append(m)
    for pk, ms in by.items():
        if len(ms) < 2: continue
        ids = [m['id'] for m in ms]
        if set(ids) & alpha:
            ms = [m for m in ms if m['id'] not in alpha]; skip['含4a-α条，剔除']+=1
            if len(ms) < 2: continue
        # 同一 Collection 内同题多条：疑为异篇
        cc = collections.Counter(c for m in ms for c in set(m['bookcols']))
        if any(v > 1 for v in cc.values()):
            skip['同一Collection内同题多条'] += 1
            judged.append((ms, 'D', '同一叢書版本內同題多條，疑為異篇或重出，待核')); continue
        fas = {fa(m) for m in ms} - {None}
        if len(fas) > 1:
            skip['子目责任者不同'] += 1
            judged.append((ms, 'C', '同名叢書子目，子目責任者不同（%s），同題異書' % '／'.join(sorted(fas)))); continue
        dys = {a[1] for m in ms for a in m['authors'][:1] if a[1]}
        if len(dys) > 1:
            skip['朝代不一'] += 1; judged.append((ms, 'D', '子目責任者朝代不一（%s）' % '／'.join(sorted(dys)))); continue
        cas = {norm_name(c['author']) for m in ms for c in m['bookcolinfo'] if c and c.get('author')} - set(ANON) - {''}
        cts = {ctnorm(c['title']) for m in ms for c in m['bookcolinfo'] if c}
        if len(pk) < 2 or len(cts) != 1:
            skip['丛书题名归一后不一或过短'] += 1; judged.append((ms, 'D', '所屬叢書題名歸一後不一（%s），疑非同一叢書' % '／'.join(sorted(cts)))); continue
        js = set()
        for m in ms:
            if m['juan'] is not None: js.add(m['juan'])
            js |= set(m['bjuan'])
            for t in m['tinfo']:
                j = tjuan(t)
                if j is not None: js.add(j)
        if len(js) > 1:
            skip['卷数不一'] += 1; judged.append((ms, 'D', '卷數不一（%s）' % '／'.join(map(str, sorted(js, key=str))))); continue
        ms.sort(key=lambda m: (-m['nbooks'], -len(m['authors']), m['id']))
        k = ms[0]
        out.append(dict(bulei=g['bulei'], cat=g['cat'], key=g['key'], parent=pk, keeper=k['id'], keeper_title=k['title'],
                        losers=[m['id'] for m in ms[1:]], col_authors=sorted(cas), juan=sorted(js, key=str), author=next(iter(fas), ''),
                        evidence=['《%s》（%s）屬《%s》，Collection %s，題錄「%s」%s' % (m['title'], m['id'], m['parent'][1], ','.join(sorted(set(m['bookcols']))),
                                  '／'.join(sorted(set(m['tinfo']))), '，撰者 ' + m['authors'][0][0] if m['authors'] else '') for m in ms]))
print(len(out), '组', sum(len(o['losers']) for o in out), '条被并'); print(skip.most_common())
print(collections.Counter(o['bulei'] for o in out), collections.Counter(o['cat'] for o in out))
json.dump(out, open(WK + '/cand_sub.json', 'w'), ensure_ascii=False, indent=1)
json.dump([[[m['id'] for m in ms], v, why] for ms, v, why in judged], open(WK + '/judged_sub.json', 'w'), ensure_ascii=False, indent=1)
