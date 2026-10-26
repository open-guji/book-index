#!/usr/bin/env python3
"""去重细拆单元 3b-0（署名异写先行）候选生成：读普查 同题组.tsv 的「未判·不同」组，
组内两两配对，标出署名同一的独立证据（同 entity、Entity alt_names、著录 author_info 原文同列两名、
CBDB/Wikidata 同号、名互含），并附朝代、卷数、部类、版本数、互链，供逐组判定。

    python3 cands.py <同题组.tsv> <out.jsonl>
"""
import collections, csv, importlib.util, itertools, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
sys.path[:0] = [os.path.join(ROOT, 'scripts'), os.path.join(ROOT, '.claude', 'qa')]
spec = importlib.util.spec_from_file_location('dc', os.path.join(ROOT, 'scripts', 'dedup-census.py'))
dc = importlib.util.module_from_spec(spec); spec.loader.exec_module(dc)
import backrefs  # noqa: E402
import sqlite3
try:
    import opencc
    T2S = opencc.OpenCC('t2s').convert
except ImportError:  # 无 opencc 时只用 VARIANTS
    T2S = lambda s: s
CBDB = os.environ.get('CBDB', os.path.join(ROOT, '..', 'cbdb-archive', '20260919', 'cbdb_20260919.sqlite3'))

W, E, NB = {}, {}, collections.Counter()
for t, p, d in backrefs.iter_records(ROOT):
    if d.get('merged_into'):
        continue
    if t == 'Work':
        W[d['id']] = d
    elif t == 'Entity' and d.get('subtype') == 'people':
        E[d['id']] = d
    elif t == 'Book' and d.get('work_id'):
        NB[d['work_id']] += 1
print('载入 Work %d、人物 %d、Book 挂接 %d' % (len(W), len(E), sum(NB.values())), file=sys.stderr)
assert W and E


def nm(x):
    return dc.norm_name(x if isinstance(x, str) else (x.get('name') if isinstance(x, dict) else ''))


ALIAS = {eid: ({nm(e.get('primary_name'))} | {nm(x) for x in e.get('alt_names') or []}) - {''} for eid, e in E.items()}
XID = {eid: {(k, str(v)) for k, v in (e.get('external_ids') or {}).items() if k in ('cbdb_id', 'wikidata_id', 'viaf_id') and v}
       for eid, e in E.items()}
PUZHI = re.compile(r'(譜|谱|志|誌|家乘|宗乘)$')
EXAM = re.compile(r'(硃卷|貢卷|齒錄|同年錄|試卷|闈墨|課藝|朱卷)$')

# CBDB：人名 → [(personid, 朝代代码, {别名: 类型})]；别名含「姓＋字號」形
CB = collections.defaultdict(list)
if os.path.exists(CBDB):
    _c = sqlite3.connect(CBDB)
    _alt = collections.defaultdict(dict)
    for pid, a, t in _c.execute('select c_personid, c_alt_name_chn, c_alt_name_type_code from ALTNAME_DATA'):
        if a:
            _alt[pid][nm(a)] = t
    for pid, n, sur, dy in _c.execute('select c_personid, c_name_chn, c_surname_chn, c_dy from BIOG_MAIN'):
        if not n:
            continue
        al = {}
        for a, t in _alt.get(pid, {}).items():
            al[a] = t
            if sur and not a.startswith(sur):
                al[nm(sur) + a] = t
        CB[nm(n)].append((pid, dy, al))
print('CBDB 人名 %d' % len(CB), file=sys.stderr)
assert CB, 'CBDB 未载入'
CBT = {3: '別名', 4: '字', 5: '號', 6: '諡', 9: '小名', 10: '小字', 11: '賜號', 13: '俗名', 19: '法號', 20: '道號'}


def cbdb_ev(n1, n2, e1):
    out = []
    want = (E.get(e1) or {}).get('external_ids', {}).get('cbdb_id') if e1 else None
    for pid, dy, al in CB.get(n1, ()):
        if want and str(pid) != str(want):
            continue
        if n2 in al:
            out.append('CBDB:%s(%s)%s=%s' % (n1, pid, CBT.get(al[n2], al[n2]), n2))
    return out


def first(w):
    a = [x for x in W[w].get('authors') or [] if isinstance(x, dict)][:1]
    return a[0] if a else None


def texts(w):
    out = []
    for x in W[w].get('indexed_by') or []:
        for k in ('author_info', 'summary', 'title_info', 'note'):
            if x.get(k):
                out.append((x.get('source'), k, x[k]))
    return out


def rel(w1, w2):
    return any(isinstance(r, dict) and r.get('id') == w2 or r == w2 for r in W[w1].get('related_works') or [])


def juan(w):
    j = W[w].get('juan_count') or {}
    return j.get('number') if isinstance(j, dict) else None


def info(w):
    a = first(w)
    return {'id': w, 'title': W[w].get('title'), 'name': a.get('name'), 'role': a.get('role'), 'eid': a.get('entity_id'),
            'ename': (E.get(a.get('entity_id')) or {}).get('primary_name'), 'dyn': a.get('dynasty') or W[w].get('dynasty'),
            'juan': juan(w), 'books': NB[w], 'nidx': len(W[w].get('indexed_by') or []),
            'sections': sorted({x.get('section') for x in W[w].get('indexed_by') or [] if x.get('section')})[:3],
            'authors': [(x.get('name'), x.get('role')) for x in W[w].get('authors') or [] if isinstance(x, dict)][:4]}


def alltexts(w, eid):
    out = [s for _, _, s in texts(w)]
    d = W[w].get('description')
    out.append(d.get('text') if isinstance(d, dict) else (d or ''))
    out.append(W[w].get('ai_note') or '')
    e = E.get(eid) or {}
    for k in ('description', 'ai_note'):
        v = e.get(k)
        out.append(v.get('text') if isinstance(v, dict) else (v or ''))
    return [x for x in out if isinstance(x, str) and x]


ALIASWORD = '字|號|号|一名|又名|一作|或作|本名|原名|初名|更名|改名|即|題|之訛|之誤|之異寫'


def zihao(n1, n2, txts):
    # 原文自证：某（某）、某字某、某號某、某一作某、「某」乃「某」之訛…（两名都要出现在同一句里）
    g1, g2 = n1[1:], n2[1:]
    pats = [re.escape(n1) + r'[（(〔]' + re.escape(n2), re.escape(n2) + r'[（(〔]' + re.escape(n1)]
    for a, b in ((n1, g2), (n2, g1), (g1, g2), (g2, g1)):
        if len(a) >= 1 and len(b) >= 1:
            pats.append(re.escape(a) + r'[^。；;\n]{0,10}(?:' + ALIASWORD + r')[「“]?' + re.escape(b))
    for a, b in ((g1, n2), (g2, n1)):
        pats.append(re.escape(a) + r'[，,、]?' + re.escape(b) + r'之?(?:字|號|号|別名|小字)')
    pats.append(re.escape(n1) + r'[^。；;\n]{0,6}(?:' + ALIASWORD + ')[^。；;\n]{0,4}' + re.escape(n2))
    pats.append(re.escape(n2) + r'[^。；;\n]{0,6}(?:' + ALIASWORD + ')[^。；;\n]{0,4}' + re.escape(n1))
    rx = re.compile('|'.join('(?:%s)' % p for p in pats))
    for t in txts:
        for sent in re.split(r'[。；;\n]', dc.norm_name(t) if False else t):
            if n1[:1] in sent and (n1 in sent or n2 in sent):
                m = rx.search(sent)
                if m:
                    return '字號:「%s」' % sent.strip()[:90]
    return None


def evidence(w1, w2):
    a1, a2 = first(w1), first(w2)
    n1, n2 = nm(a1.get('name')), nm(a2.get('name'))
    e1, e2 = a1.get('entity_id'), a2.get('entity_id')
    ev = []
    if e1 and e1 == e2:
        ev.append('同entity')
    for (x, ex), (y, ey) in (((n1, e1), (n2, e2)), ((n2, e2), (n1, e1))):
        if ex and ex in ALIAS and y in ALIAS[ex]:
            ev.append('别名:%s∈%s' % (y, E[ex]['primary_name']) + ('' if not ey or ey == ex else '(对方另挂%s)' % ey))
    if e1 and e2 and e1 != e2 and XID.get(e1, set()) & XID.get(e2, set()):
        ev.append('外部号同:%s' % sorted(XID[e1] & XID[e2]))
    for w in (w1, w2):
        for src, k, s in texts(w):
            t = nm(s)
            if n1 in t and n2 in t and n1 not in n2 and n2 not in n1:
                ev.append('原文:%s/%s/%s「%s」' % (w, src, k, s[:80]))
    ev += cbdb_ev(n1, n2, e1) + cbdb_ev(n2, n1, e2)
    z = zihao(n1, n2, alltexts(w1, e1) + alltexts(w2, e2))
    if z:
        ev.append(z)
    if n1 != n2 and (n1 in n2 or n2 in n1):
        ev.append('名互含')
    if n1 != n2 and T2S(n1) == T2S(n2):
        ev.append('异体')
    return ev


def main():
    rows = list(csv.reader(open(sys.argv[1], encoding='utf-8'), delimiter='\t'))[1:]
    out = open(sys.argv[2], 'w', encoding='utf-8')
    C = collections.Counter()
    for bl, cat, j, key, n, ids in rows:
        if j != '未判' or cat != '不同':
            continue
        ids = [w for w in ids.split(',') if w in W]
        named = [w for w in ids if first(w) and nm(first(w).get('name')) not in dc.ANONYMOUS]
        puzhi = bool(PUZHI.search(key))
        if EXAM.search(key):
            continue
        for w1, w2 in itertools.combinations(named, 2):
            n1, n2 = nm(first(w1).get('name')), nm(first(w2).get('name'))
            if n1 == n2:
                continue
            ev = evidence(w1, w2)
            if n1[:1] == n2[:1]:
                kind = '同姓'
            else:
                kind = '异姓'
            C['对'] += 1
            if not ev and (kind == '异姓' or puzhi):
                continue
            C[kind + ('·有证' if ev else '·无证')] += 1
            out.write(json.dumps({'bulei': bl, 'key': key, 'puzhi': puzhi, 'kind': kind, 'related': rel(w1, w2) or rel(w2, w1),
                                  'ev': ev, 'a': info(w1), 'b': info(w2)}, ensure_ascii=False) + '\n')
    for k, v in sorted(C.items()):
        print(k, v, file=sys.stderr)


if __name__ == '__main__':
    main()
