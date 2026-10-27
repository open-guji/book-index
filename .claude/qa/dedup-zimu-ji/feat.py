"""新-子目异名-集未：逐组抽特征。用法：P4WORK=<工作目录> python3 feat.py <本单元行.tsv>
（工作目录须先有 dedup-part4/load.py 的 cache.pkl；本单元行取 assign_units_20261026.py 输出里本单元代号的行）
输出 $P4WORK/zj-feat.json 与人读稿 $P4WORK/zj-review.txt"""
import os, sys, re, json, collections
HERE = os.path.dirname(os.path.abspath(__file__))
sys.argv = [sys.argv[0]] + sys.argv[1:]
UNIT = sys.argv[1]
exec(open(os.path.join(HERE, '..', 'dedup-part4', 'feat.py')).read().split('groups=[]')[0])
print('载入 Work', len(W), 'Book', len(B), 'Collection', len(C), file=sys.stderr)
assert W and B and C
COLSRC = {}
for c in C.values():
    for s in c.get('sources') or []:
        if isinstance(s, dict) and s.get('id'): COLSRC[s['id']] = c
P = re.compile(r'所屬叢書記錄 ([0-9a-z]{16})（([^）]*(?:（[^）]*）[^）]*)*)）')
DYN = sorted('先秦 周 秦 漢 西漢 東漢 後漢 三國 魏 蜀 吳 晉 西晉 東晉 南朝宋 南朝齊 南朝梁 南朝陳 南朝 北朝 宋 齊 梁 陳 北魏 北齊 北周 隋 唐 五代 前蜀 後蜀 南唐 後唐 後晉 遼 金 元 明 清 民國 日本 朝鮮 高麗 南宋 北宋 越南'.split(), key=len, reverse=True)
ROLE = re.compile(r'(等)?(撰|輯|編|錄|譯|注|註|著|纂|述|校|補遺|補|考|鈔|抄|選|評|訂|集|敕撰|奉敕撰|筆述|口授|增訂|重訂|彙編|參訂|同撰|合撰|箋|疏|釋|音義|講|說|記|書|刪|定|批|點|圈點|手輯|作|撰并書|題)+.*$')
def parse_ai(ai):
    out = []
    for seg in re.split(r'[;；，,]', ai or ''):
        seg = seg.strip(); seg = re.sub(r'^(舊題|題|原題)', '', seg)
        d0 = ''
        for d in DYN:
            if seg.startswith(d): seg = seg[len(d):]; d0 = d; break
        seg = ROLE.sub('', seg)
        m = re.match(r'^(.*?)（(.*?)）', seg)
        for c in ([m.group(1), m.group(2)] if m else [seg]):
            c = norm_name(c)
            if c and '□' not in c and len(c) <= 6 and c not in ANON: out.append((c, d0))
    return out
def colof(w):
    m = P.search(w.get('ai_note') or '')
    if not m: return None
    c = COLSRC.get(m.group(1))
    return dict(rec=m.group(1), title=m.group(2), cid=c['id'] if c else '', ctitle=(c or {}).get('title', ''),
                cauth=[(a.get('name'), a.get('role'), a.get('dynasty')) for a in ((c or {}).get('authors') or []) if isinstance(a, dict)])
def eff(w, col):
    """有效撰人：authors（佚名、补撰人除外）＋総目 author_info；獨撰類无撰人则继承丛书撰人"""
    ns = []; src = ''
    bu = '【獨撰子目补撰人】' in (w.get('ai_note') or '')
    for a in w.get('authors') or []:
        if not isinstance(a, dict): continue
        n = norm_name(a.get('name'))
        if n and n not in ANON: ns.append((n, a.get('dynasty') or '', a.get('role') or '', 'col' if bu else 'self'))
    for i in w.get('indexed_by') or []:
        for n, d in parse_ai(i.get('author_info')): ns.append((n, d, '', 'ai'))
    secs = [i.get('section') or '' for i in w.get('indexed_by') or []]
    if not [x for x in ns if x[3] != 'col'] and col and any('獨撰' in s for s in secs):
        for n, r, d in col['cauth']:
            if norm_name(n) and norm_name(n) not in ANON: ns.append((norm_name(n), d or '', r or '', 'col'))
    seen = set(); res = []
    for x in ns:
        if x[0] not in seen: seen.add(x[0]); res.append(x)
    return res
rows = [l.rstrip('\n').split('\t') for l in open(UNIT, encoding='utf-8')]
out = []; rv = []
for r in rows:
    unit, bl, cat, st, sk, title, ids = r[:7]
    g = dict(bulei=bl, cat=cat, sk=sk, key=title, works=[])
    rv.append('#### %s ［%s／%s／%s］' % (title, bl, cat, sk))
    for i in ids.split(','):
        w = W[i]; f = feat(i); col = colof(w)
        e = eff(w, col)
        ib = [(x.get('section') or '', x.get('title_info') or '', x.get('author_info') or '', (x.get('summary') or '')[:200], x.get('source') or '') for x in w.get('indexed_by') or []]
        d = dict(id=i, title=w.get('title'), eff=e, dyn=f['dyn'], juan=f['juan'], bjuan=sorted(f['bjuan']), col=col,
                 sub=bool(col), ib=ib, eds=f['eds'][:8], nbooks=f['nbooks'], bcols=[c[1] for c in f['cols']][:6],
                 rel=[x.get('id') for x in (w.get('related_works') or []) if isinstance(x, dict)],
                 desc=(json.dumps(w.get('description'), ensure_ascii=False)[:150] if w.get('description') else ''),
                 note=(w.get('ai_note') or '')[:300])
        g['works'].append(d)
        rv.append('  %s 《%s》 撰:%s 朝:%s 卷:%s/%s 丛:%s%s  Book%d:%s' % (i, d['title'], '、'.join('%s%s%s' % (x[1], x[0], '[' + x[3] + ']') for x in e) or '—',
                  d['dyn'], d['juan'], d['bjuan'], (col or {}).get('title', '—'), ('〔丛撰%s〕' % '、'.join('%s%s' % (a[2] or '', a[0]) for a in col['cauth'])) if col and col['cauth'] else '',
                  d['nbooks'], '／'.join(sorted(set(d['eds'])))[:80]))
        for x in ib: rv.append('      ib[%s] %s｜%s｜%s' % (x[0] or x[4], x[1], x[2], x[3][:140]))
        if d['desc']: rv.append('      desc ' + d['desc'][:120])
    out.append(g)
WK = os.environ.get('P4WORK', '/tmp/p4')
json.dump(out, open(WK + '/zj-feat.json', 'w'), ensure_ascii=False)
open(WK + '/zj-review.txt', 'w').write('\n'.join(rv) + '\n')
print('组', len(out), '条', sum(len(g['works']) for g in out))
