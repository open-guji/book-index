#!/usr/bin/env python3
"""3a 第二轮：从普查「同题组.tsv」取同首位未判组，生成逐组档案（dossier.jsonl）并机械分档。

    python3 dossier.py <census 同题组.tsv> <out dir> [--exclude ids.tsv ...]

档案每组含各 Work 的题名、责任者、section、Book 数、卷数集合（Book measure_info/title_info 首个「N卷」）、
所属 Collection 题名与 section、description/ai_note 摘要。分档见 tier()。"""
import argparse, collections, glob, json, os, re, sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))
CN = {'〇': 0, '零': 0, '一': 1, '二': 2, '兩': 2, '三': 3, '四': 4, '五': 5, '六': 6, '七': 7, '八': 8, '九': 9}


def cnum(s):
    if s.isdigit():
        return int(s)
    n, cur = 0, 0
    for ch in s:
        if ch in CN:
            cur = CN[ch]
        elif ch == '十':
            n += (cur or 1) * 10; cur = 0
        elif ch == '百':
            n += (cur or 1) * 100; cur = 0
        elif ch == '千':
            n += (cur or 1) * 1000; cur = 0
        else:
            return None
    return n + cur


JUAN = re.compile(r'([〇零一二兩三四五六七八九十百千\d]+)卷')


def first_juan(s):
    m = JUAN.search(s or '')
    return cnum(m.group(1)) if m else None


def load(p):
    return json.load(open(p, encoding='utf-8'))


def wpath(i):
    h = glob.glob(os.path.join(ROOT, 'Work', *i[-3:], i + '-*.json'))
    return h[0] if len(h) == 1 else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('tsv'); ap.add_argument('out')
    ap.add_argument('--exclude', action='append', default=[])
    a = ap.parse_args()
    excl = set()
    for f in a.exclude:
        for line in open(f, encoding='utf-8'):
            excl.update(re.findall(r'\b[0-9a-z]{12}\b', line))
    groups = []
    for line in open(a.tsv, encoding='utf-8'):
        c = line.rstrip('\n').split('\t')
        if len(c) >= 6 and c[1] == '同首位' and c[2] == '未判':
            groups.append((c[0], c[3], c[5].split(',')))
    ids = {i for _, _, g in groups for i in g}
    print('组 %d，Work %d' % (len(groups), len(ids)), file=sys.stderr)
    books = collections.defaultdict(list)
    colls = set()
    for p in glob.iglob(os.path.join(ROOT, 'Book', '*', '*', '*', '*.json')):
        s = open(p, encoding='utf-8').read()
        m = re.search(r'"work_id": "([0-9a-z]+)"', s)
        if m and m.group(1) in ids:
            b = json.loads(s)
            ti = ' '.join(x.get('title_info', '') for x in b.get('indexed_by') or [])
            j = first_juan(b.get('measure_info')) or first_juan(ti.replace(b.get('title') or '', '', 1))
            ci = [x.get('id') for x in b.get('contained_in') or []]
            colls.update(ci)
            books[m.group(1)].append({'id': b['id'], 'edition': b.get('edition') or '', 'juan': j,
                                      'measure': b.get('measure_info') or '', 'title_info': ti[:80], 'coll': ci})
    cinfo = {}
    for c in colls:
        h = glob.glob(os.path.join(ROOT, 'Collection', *c[-3:], c + '-*.json'))
        if h:
            d = load(h[0])
            cinfo[c] = {'title': d.get('title'), 'sec': ' '.join(x.get('section', '') or '' for x in d.get('indexed_by') or []),
                        'authors': '/'.join('%s%s' % (x.get('name'), x.get('role') or '') for x in d.get('authors') or [])}
    os.makedirs(a.out, exist_ok=True)
    out = open(os.path.join(a.out, 'dossier.jsonl'), 'w', encoding='utf-8')
    cnt = collections.Counter()
    for bulei, key, g in groups:
        ws = []
        for i in g:
            p = wpath(i)
            d = load(p)
            au = d.get('authors') or []
            bs = books.get(i, [])
            js = sorted({b['juan'] for b in bs if b['juan']} | ({d['juan_count']} if isinstance(d.get('juan_count'), int) else set()))
            ws.append({'id': i, 'path': os.path.relpath(p, ROOT), 'title': d.get('title'),
                       'authors': [{k: x.get(k) for k in ('name', 'role', 'dynasty', 'entity_id')} for x in au],
                       'inherited': bool(au and '獨撰類子目不另題撰人' in (au[0].get('role_basis') or '')),
                       'sec': sorted({x.get('section') or '' for x in d.get('indexed_by') or []}),
                       'nbooks': len(bs), 'juan': js,
                       'editions': sorted({b['edition'] for b in bs})[:6],
                       'colls': sorted({'%s｜%s｜%s' % (cinfo.get(c, {}).get('title'), cinfo.get(c, {}).get('authors'), cinfo.get(c, {}).get('sec')) for b in bs for c in b['coll']})[:6],
                       'related': [r.get('id') or r.get('work_id') for r in d.get('related_works') or []],
                       'desc': str(d.get('description') or '')[:200], 'note': (d.get('ai_note') or '')[:300]})
        t, why = tier(bulei, ws, excl)
        cnt[t] += 1
        out.write(json.dumps({'bulei': bulei, 'key': key, 'tier': t, 'why': why, 'works': ws}, ensure_ascii=False) + '\n')
    print(dict(cnt), file=sys.stderr)


sys.path.insert(0, os.path.join(ROOT, '.claude/qa'))
from scan import VARIANTS  # noqa: E402
PUNCT = re.compile(r'[\s·・、，,。．.：:；;「」『』《》〈〉]')


def tnorm(t):
    # 括注保留（括注不同才算题名有别），只抹异体与标点
    return PUNCT.sub('', (t or '').translate(VARIANTS)).replace('(', '（').replace(')', '）')


GENEALOGY = re.compile(r'[譜谱]')
REVISE = re.compile(r'增訂|增补|增補|重訂|續|补遺|補遺|拾遺|外集|別集|附錄|選|鈔|抄|摘|節本|略')


ERA = {'先秦': 0, '秦': 1, '漢': 2, '西漢': 2, '東漢': 2, '三國': 3, '三國魏': 3, '魏': 3, '蜀': 3, '吳': 3, '晉': 4, '西晉': 4, '東晉': 4,
       '南朝宋': 5, '南朝齊': 5, '南朝梁': 5, '南朝陳': 5, '北魏': 5, '北齊': 5, '北周': 5, '梁': 5, '陳': 5, '南北朝': 5,
       '隋': 6, '唐': 7, '五代': 8, '宋': 9, '北宋': 9, '南宋': 9, '趙宋': 9, '遼': 9, '金': 9, '元': 10, '元末明初': 10.5,
       '明': 11, '明末清初': 11.5, '清': 12, '民國': 13, '中華民國': 13}


def dyn_ok(dyn):
    # 同代或相邻（如 清／民國、元／明、南宋／宋）算兼容；未知朝代名不判兼容
    v = [ERA.get(d) for d in dyn]
    if None in v:
        return len(dyn) <= 1
    return not v or max(v) - min(v) <= 1


def huibian_like(w):
    secs = list(w['sec']) + [c.split('｜')[-1] for c in w['colls']]
    return any('叢書部' in s and '獨撰' not in s for s in secs)


def tier(bulei, ws, excl):
    if any(w['id'] in excl for w in ws):
        return 'X', '他单元已领'
    f = [w['authors'][0] for w in ws]
    eids = {x['entity_id'] for x in f if x.get('entity_id')}
    if len(eids) > 1:
        return 'D', '首位 entity 不同'
    dyn = {x['dynasty'] for x in f if x.get('dynasty')}
    if not dyn_ok(dyn):
        return 'C', '朝代不同:' + '/'.join(sorted(dyn))
    flags = []
    if len({x.get('role') or '' for x in f}) > 1:
        flags.append('role_diff')
    if len({tuple(tnorm(a['name']) for a in w['authors']) for w in ws}) > 1:
        flags.append('coauth_diff')
    titles = {w['title'] for w in ws}
    if len({tnorm(t) for t in titles}) > 1:
        flags.append('title_diff')
    if any(GENEALOGY.search(w['title'] or '') for w in ws) or any('譜' in s for w in ws for s in w['sec']):
        return 'C', '家谱'
    if any(REVISE.search(w['title'] or '') for w in ws) and len(titles) > 1:
        flags.append('revise_word')
    maxes = [max(w['juan']) for w in ws if w['juan']]
    if maxes and max(maxes) - min(maxes) > 1:
        # 各条卷数集合皆落在最大者已有的卷数集合内（单行本 Work 本已挂此卷数之本）→ 退人工复核，否则存疑
        big = max((w for w in ws if w['juan']), key=lambda w: max(w['juan']))
        if all(set(w['juan']) <= set(big['juan']) for w in ws):
            flags.append('juan_subset')
        else:
            return 'C', '卷数上限悬殊:' + ';'.join(str(w['juan']) for w in ws)
    huibian = [w for w in ws if any('叢書部' in s and '獨撰' not in s for s in w['sec'])]
    if huibian and maxes and max(maxes) > 1:
        flags.append('huibian_vs_multi')
    if any(not w['juan'] for w in ws) and any(huibian_like(w) for w in ws):
        flags.append('huibian_nojuan')
    if any(len(w['juan']) > 1 for w in ws):
        flags.append('juan_mixed')
    cbase = {re.sub(r'[〇一二三四五六七八九十百]+種.*$', '', c.split('｜')[0]) for w in ws for c in w['colls']}
    if len(tnorm(ws[0]['title'])) <= 2 and len(cbase) > 1:
        flags.append('generic_title')
    if len(ws) > 3:
        flags.append('big_group')
    if not flags:
        return 'A', ''
    return 'B', ','.join(flags)


if __name__ == '__main__':
    main()
