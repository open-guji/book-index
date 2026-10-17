#!/usr/bin/env python3
"""旧 `Book.provenance[].seals` 字符串 → 印章候选匹配表＋印文频次表（GUJI-542 P3，只读）。

  python3 .claude/qa/seal_candidates.py --out ../book-index-draft/docs/seal-match

只读：不写任何 Book／Entity、不动 index。输出（TSV，UTF-8，确定性、可重跑）：
  frequency.tsv   主表：规范印文 → 次数、Book 数、色形变体、机构前 3、写法变体、是否已有印章条、示例 Book
  matches.tsv     辅表：每条旧字符串一行（行数＝字符串总数）
  summary.md      各状态条数、解析失败原因、≥20 次而无条的印文名单

状态：命中（印文唯一对上一枚现行印章条，且条上的形与解析出的形不冲突）／歧义（对上多枚，或形冲突；**不自选**）／
無條／多印（一条字符串里不止一枚，逐枚匹配，见「多印逐枚」列）／解析失败（留原串，不猜）。
异体字只做下面 VARIANT 小表，不用 opencc 全量简繁。
"""
from __future__ import annotations
import argparse
import collections
import os
import re
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, os.path.join(ROOT, 'build'))

# 小表：只收印文里确实成对出现的异体（天祿繼鑑／鑒、祕／秘 等）；别扩成大字典
VARIANT = {'祕': '秘', '鑑': '鑒', '裏': '裡', '衞': '衛', '爲': '為', '啓': '啟', '卽': '即', '舘': '館', '嶽': '岳'}

COLOR = r'(?:大|小|雙)?(?:朱白相間|朱白|朱|白|藍|黑|紅|墨)'
SHAPE = r'(?:長方|長橢|橢圓|方|長|橢|圓|葫蘆|鼎|瓶|聯珠)?形?印?'
TAIL = re.compile(r'^(%s)?(%s)$' % (COLOR, SHAPE))
BARE = re.compile(r'^(.+?)(%s)(%s)$' % (COLOR, SHAPE))
SEGMENT_LEAD = re.compile(r'^[^「」]{0,20}[：:]')           # 「每冊首頁：」「卷末：」之類位置前缀
FAIL_REASONS = [('滿漢', '滿漢合璧'), ('圖案', '圖案／肖形印'), ('肖形', '圖案／肖形印'), ('朱白相間', '朱白相間'),
                ('朱白交錯', '朱白相間'), ('朱白合', '朱白相間'), ('？', '带「？」存疑'), ('(偽)', '带偽注'), ('（偽）', '带偽注')]


def norm(t: str) -> str:
    t = re.sub(r'\s+', '', t)
    return ''.join(VARIANT.get(c, c) for c in t)


def _seg(seg: str):
    """一段 → (印文, 色, 形) 或 (None, 原因)。"""
    seg = SEGMENT_LEAD.sub('', seg.strip()).strip()
    if not seg:
        return None, '空'
    m = re.match(r'^(%s)(%s)「([^」]+)」$' % (COLOR, SHAPE), seg)       # 「朱方「雨農藏書」」：色形在前
    if m:
        return (m.group(3).strip(), m.group(1), m.group(2).replace('印', '').replace('形', '')), None
    m = re.match(r'^「([^」]+)」(.*)$', seg)
    if m:
        text, tail = m.group(1), m.group(2).strip()
        t = TAIL.match(tail)
        if t:
            return (text.strip(), t.group(1) or '', (t.group(2) or '').replace('印', '').replace('形', '')), None
        for k, why in FAIL_REASONS:
            if k in seg:
                return None, why
        return None, '尾部不合色形格式'
    for k, why in FAIL_REASONS:
        if k in seg:
            return None, why
    m = BARE.match(seg)
    if m:
        return (m.group(1).strip(), m.group(2), m.group(3).replace('印', '').replace('形', '')), None
    if '「' in seg or '」' in seg:
        return None, '引号不成对'
    return (seg, '', ''), None            # 无引号无色形：整串当印文，色形缺


def parse(s: str):
    """→ ([(印文, 色, 形)…], 失败原因或 None)。多枚按「。」拆；任一段失败则整串失败（不猜）。"""
    segs = [x for x in re.split(r'[。；;]', s) if x.strip()]
    if not segs:
        return [], '空'
    out = []
    for x in segs:
        r, why = _seg(x)
        if r is None:
            return [], why
        out.append(r)
    return out, None


def match(text: str, shape: str, seals: dict):
    """seals：{seal_id: (规范印文, 形)}。→ (状态, [seal_id…], 备注)。"""
    key = norm(text)
    hit = [i for i, (t, _f) in seals.items() if t == key]
    if not hit:
        return '無條', [], ''
    if len(hit) > 1:
        return '歧義', hit, '同印文多枚印章条'
    f = seals[hit[0]][1]
    if f and shape and f not in shape and shape not in f:
        return '歧義', hit, '形不合（條 %s／書 %s）' % (f, shape)
    return '命中', hit, '' if f else '條上無形，形未核'


def live_seals(ents: dict) -> dict:
    out = {}
    for i, d in ents.items():
        if isinstance(d, dict) and d.get('subtype') == 'seal' and not d.get('merged_into'):
            out[i] = (norm(d.get('seal_text') or d.get('primary_name') or ''), d.get('seal_form') or '')
    return out


def run(books, ents):
    """books：iterable of (book_id, book dict)。→ (matches 行, frequency 行, 统计)。"""
    seals = live_seals(ents)
    rows, agg = [], {}
    fails = collections.Counter()
    for bid, b in books:
        for pi, pv in enumerate((b.get('provenance') if isinstance(b, dict) else None) or []):
            if not isinstance(pv, dict):
                continue
            for s in pv.get('seals') or []:
                if not isinstance(s, str):
                    continue
                items, why = parse(s)
                inst = pv.get('institution') or ''
                if why:
                    fails[why] += 1
                    rows.append((bid, pi, inst, s, '', '解析失敗', '', why, ''))
                    continue
                per, ids = [], []
                for text, color, shape in items:
                    st, hit, note = match(text, shape, seals)
                    per.append('%s:%s' % (st, ','.join(hit)) if hit else st)
                    ids += hit
                    a = agg.setdefault(norm(text), {'n': 0, 'books': set(), 'cs': collections.Counter(),
                                                    'inst': collections.Counter(), 'raw': collections.Counter(),
                                                    'ex': []})
                    a['n'] += 1
                    a['books'].add(bid)
                    a['cs'][(color + shape) or '（無色形）'] += 1
                    a['inst'][inst] += 1
                    a['raw'][text.strip()] += 1
                    if len(a['ex']) < 2 and bid not in a['ex']:
                        a['ex'].append(bid)
                if len(items) > 1:
                    status, note = '多印', ''
                else:
                    status, _h, note = match(items[0][0], items[0][2], seals)
                rows.append((bid, pi, inst, s, '|'.join('%s/%s/%s' % t for t in items), status,
                             ','.join(dict.fromkeys(ids)), note, '|'.join(per) if len(items) > 1 else ''))
    freq = []
    for k, a in agg.items():
        has = [i for i, (t, _f) in seals.items() if t == k]
        freq.append((k, a['n'], len(a['books']),
                     ';'.join('%s×%d' % x for x in sorted(a['cs'].items(), key=lambda x: (-x[1], x[0]))),
                     ';'.join('%s×%d' % x for x in sorted(a['inst'].items(), key=lambda x: (-x[1], x[0]))[:3]),
                     ';'.join(x for x in sorted(a['raw']) if norm(x) == k and x != k) if len(a['raw']) > 1 else '',
                     ','.join(has), ','.join(sorted(a['ex']))))
    freq.sort(key=lambda r: (-r[1], r[0]))
    return rows, freq, {'fails': fails}


ROW_HEAD = ['book_id', 'provenance序號', '機構', '原字串', '印文／色／形', '狀態', '候選seal_id', '備註', '多印逐枚']
FREQ_HEAD = ['規範印文', '次數', '涉及Book數', '色形變體', '機構前3', '寫法變體', '已有印章條', '示例Book']


def tsv(head, rows):
    esc = lambda x: str(x).replace('\t', ' ').replace('\n', ' ')
    return '\n'.join('\t'.join(esc(c) for c in r) for r in [head] + [list(r) for r in rows]) + '\n'


def summary(rows, freq, st):
    c = collections.Counter(r[5] for r in rows)
    n = len(rows)
    L = ['# 印章 seals 字串候選匹配（GUJI-542 P3）', '',
         '來源：book-index main，`Book.provenance[].seals` 全量；腳本 `.claude/qa/seal_candidates.py`（只讀、確定性）。', '',
         '## 狀態', '', '| 狀態 | 條數 | 占比 |', '|---|---|---|']
    for k in ('命中', '歧義', '無條', '多印', '解析失敗'):
        L.append('| %s | %d | %.1f%% |' % (k, c.get(k, 0), 100.0 * c.get(k, 0) / n if n else 0))
    L += ['', '合計 %d 條字串；不同規範印文 %d 種。' % (n, len(freq)), '', '## 解析失敗原因', '', '| 原因 | 條數 |', '|---|---|']
    L += ['| %s | %d |' % x for x in sorted(st['fails'].items(), key=lambda x: (-x[1], x[0]))]
    big = [r for r in freq if r[1] >= 20 and not r[6]]
    L += ['', '## ≥20 次而無印章條的印文（%d 種，合計 %d 條）' % (len(big), sum(r[1] for r in big)), '',
          '| 規範印文 | 次數 | Book數 | 色形 | 示例Book |', '|---|---|---|---|---|']
    L += ['| %s | %d | %d | %s | %s |' % (r[0], r[1], r[2], r[3], r[7]) for r in big]
    L += ['', '已有印章條者見 frequency.tsv「已有印章條」列。建條須另請示（用戶已定：不大批建印主），每枚須有獨立來源。', '']
    return '\n'.join(L)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--root', default=ROOT)
    ap.add_argument('--out', required=True, help='輸出目錄（建議 book-index-draft/docs/seal-match）')
    a = ap.parse_args(argv)
    import v2common as V
    recs, _, _ = V.load_repo(a.root)
    books = ((i, recs['Book'][i].data) for i in sorted(recs['Book']))
    ents = {i: r.data for i, r in recs['Entity'].items()}
    rows, freq, st = run(books, ents)
    os.makedirs(a.out, exist_ok=True)
    for name, txt in (('matches.tsv', tsv(ROW_HEAD, rows)), ('frequency.tsv', tsv(FREQ_HEAD, freq)),
                      ('summary.md', summary(rows, freq, st))):
        with open(os.path.join(a.out, name), 'w', encoding='utf-8', newline='\n') as f:
            f.write(txt)
    print('字串 %d 條；印文 %d 種；狀態 %s' % (len(rows), len(freq), dict(collections.Counter(r[5] for r in rows))))


if __name__ == '__main__':
    main()
