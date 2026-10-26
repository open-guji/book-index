#!/usr/bin/env python3
"""去重方案 3a-3：Work 著录原文里自证「一名／又名／原名／即」的异题同书候选。

    python3 scan_alias.py <out_dir> [--whitelist f.tsv ...]

产出 hits.tsv：每条命中（来源 Work、所在字段、标记词、上下文、别名、命中 Work）。
"""
import argparse, collections, importlib.util, json, os, re, sys
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
sys.path.insert(0, os.path.join(ROOT, '.claude/qa'))
spec = importlib.util.spec_from_file_location('dc', os.path.join(ROOT, 'scripts/dedup-census.py'))
dc = importlib.util.module_from_spec(spec); spec.loader.exec_module(dc)
import backrefs  # noqa: E402

MARK = r'一名|又名|亦名|原名|初名|舊名|本名|一作|又作|一題|又題|原題|題作|或題|一稱|又稱|亦稱|俗稱|簡稱|改名|更名|易名|蓋即|即'
R = re.compile(r'(' + MARK + r')[為为曰作：:]?\s*[《〈「『]?([^，,。；;、《》〈〉「」『』（）()\s]{2,30})')
JUAN = re.compile(r'(不分卷|[一二三四五六七八九十百千〇零兩\d]+[卷冊册篇種回]).*$')

def strip_juan(t):
    m = JUAN.search(t)
    return t[:m.start()] if m and m.start() >= 2 else t

def text_fields(d):
    for i, ib in enumerate(d.get('indexed_by') or []):
        if isinstance(ib, dict):
            for k in ('title_info', 'author_info', 'summary', 'note', 'notes'):
                if isinstance(ib.get(k), str):
                    yield 'indexed_by[%d].%s' % (i, k), ib[k]
    for k in ('description', 'note', 'notes'):
        v = d.get(k)
        if isinstance(v, dict): v = v.get('text')
        if isinstance(v, str):
            yield k, v
    for i, t in enumerate(d.get('additional_titles') or []):
        if isinstance(t, dict):
            yield 'additional_titles[%d]' % i, '又名' + (t.get('title') or t.get('name') or '')
        elif isinstance(t, str):
            yield 'additional_titles[%d]' % i, '又名' + t

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('out'); ap.add_argument('--whitelist', action='append', default=[])
    a = ap.parse_args(); os.makedirs(a.out, exist_ok=True)
    W = {}
    for t, p, d in backrefs.iter_records(ROOT):
        if t == 'Work' and not d.get('merged_into') and '敦煌遺書' not in (d.get('ai_note') or ''):
            W[d['id']] = d
    print('载入 live Work', len(W), file=sys.stderr)
    assert W
    judged = set()
    for f in a.whitelist:
        for line in open(f, encoding='utf-8'):
            x = line.rstrip('\n').split('\t')
            if len(x) >= 2: judged.add(frozenset(x[:2]))
    linked = set()
    for w, d in W.items():
        for r in d.get('related_works') or []:
            if isinstance(r, dict) and r.get('id'):
                linked.add(frozenset((w, r['id'])))
    tidx = collections.defaultdict(set)
    for w, d in W.items():
        tidx[dc.norm(d.get('title'))].add(w)
        for ib in d.get('indexed_by') or []:
            if isinstance(ib, dict) and ib.get('title_info'):
                tidx[dc.norm(strip_juan(dc.norm(ib['title_info'])))].add(w)
    rows, seen = [], set()
    for w, d in W.items():
        own = dc.norm(d.get('title'))
        for fld, txt in text_fields(d):
            for m in R.finditer(txt):
                raw = m.group(2)
                al = dc.norm(strip_juan(raw))
                if len(al) < 2 or al == own: continue
                for w2 in tidx.get(al, ()):
                    if w2 == w: continue
                    key = (w, w2, m.group(1), fld)
                    if key in seen: continue
                    seen.add(key)
                    pr = frozenset((w, w2))
                    left = re.split(r'[。；;！？]', txt[max(0, m.start() - 60): m.start()])[-1]
                    ctx = txt[max(0, m.start() - 25): m.end() + 10].replace('\t', ' ').replace('\n', ' ')
                    rows.append((w, d.get('title') or '', fld, m.group(1), raw, w2, W[w2].get('title') or '',
                                 'judged' if pr in judged else ('linked' if pr in linked else ''), ctx, left.replace('\t', ' ').replace('\n', ' ')))
    with open(os.path.join(a.out, 'hits.tsv'), 'w', encoding='utf-8') as f:
        f.write('src\tsrc_title\tfield\tmark\talias_raw\tdst\tdst_title\tstate\tcontext\tleft\n')
        for r in rows: f.write('\t'.join(r) + '\n')
    ids = {r[0] for r in rows} | {r[5] for r in rows}
    ntitle = collections.Counter(dc.norm(d.get('title')) for d in W.values())
    feats = {}
    for i in ids:
        d = W[i]
        au = [x for x in d.get('authors') or [] if isinstance(x, dict)]
        feats[i] = {'title': d.get('title'), 'ntitle_n': ntitle[dc.norm(d.get('title'))],
                    'authors': [[x.get('name'), x.get('role'), x.get('dynasty'), x.get('entity_id')] for x in au],
                    'dynasty': d.get('dynasty'), 'juan': d.get('juan_count'),
                    'title_info': [ib.get('title_info') for ib in d.get('indexed_by') or [] if isinstance(ib, dict)][:6],
                    'sections': sorted({ib.get('section') or '' for ib in d.get('indexed_by') or [] if isinstance(ib, dict)})[:4],
                    'sources': sorted({ib.get('source') or '' for ib in d.get('indexed_by') or [] if isinstance(ib, dict)}),
                    'n_ib': len(d.get('indexed_by') or []),
                    'related': [r.get('id') for r in d.get('related_works') or [] if isinstance(r, dict)],
                    'contained_in': d.get('contained_in')}
    json.dump(feats, open(os.path.join(a.out, 'works.json'), 'w', encoding='utf-8'), ensure_ascii=False)
    c = collections.Counter(r[3] for r in rows)
    print('命中', len(rows), '对(无序)', len({frozenset((r[0], r[5])) for r in rows}), dict(c.most_common()), file=sys.stderr)

if __name__ == '__main__':
    main()
