#!/usr/bin/env python3
"""按 P3 匹配口径回填 `Book.provenance[].seal_marks`（GUJI-542 P4）。

  python3 .claude/qa/seal_backfill.py --seal <seal_id> [--seal …] [--limit 200] [--dry-run]
  python3 .claude/qa/seal_backfill.py --seal <seal_id> --variants      # 只列异形清单

只写 `seal_marks`：旧 `seals` 字符串、revision 等其它字段一字不动；幂等（已有该 seal_id 的项跳过）；
`--dry-run` 只报不写。仅回填「命中且形色已核」的行：条上 `seal_form` 与书上形一致、条上 `seal_style` 的色
（朱文／白文）与书上色一致；条上无形、形色不合、歧义、多印、解析失败一律不写（形色不合列入 --variants 异形清单）。
选取按 (book_id, provenance 序号) 排序，`--limit` 取前 N 项，分批即反复运行。
"""
from __future__ import annotations
import argparse
import collections
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, 'build'))
import seal_candidates as sc  # noqa: E402


def seal_info(ents):
    """seal_id → (规范印文, 形, 色)；色取 seal_style 首字（朱文→朱、白文→白）。"""
    out = {}
    for i, d in ents.items():
        if isinstance(d, dict) and d.get('subtype') == 'seal' and not d.get('merged_into'):
            st = d.get('seal_style') or ''
            out[i] = (sc.norm(d.get('seal_text') or d.get('primary_name') or ''), d.get('seal_form') or '', st[:1] if st[:1] in '朱白' else '')
    return out


def classify(text, color, shape, sid, info):
    """→ 'ok'｜'形未核'｜'异形'。命中已由调用方保证（印文唯一对上）。"""
    _t, f, c = info[sid]
    if not f and not c:
        return '形未核'
    if f and shape and f not in shape and shape not in f:
        return '异形'
    if c and color and c not in color:
        return '异形'
    if (f and not shape) or (c and not color):
        return '形未核'
    return 'ok'


def plan(books, ents, seal_ids):
    """→ (可写 [(book_id, pi, seal_id, 原串)], 异形 [(…, 书上色形)], 已有计数, 形未核计数)。"""
    info = seal_info(ents)
    by_text = collections.defaultdict(list)
    for i, (t, _f, _c) in info.items():
        by_text[t].append(i)
    todo, odd, have, unk = [], [], 0, 0
    for bid, b in books:
        for pi, pv in enumerate((b.get('provenance') if isinstance(b, dict) else None) or []):
            if not isinstance(pv, dict):
                continue
            mine = {m.get('seal_id') for m in pv.get('seal_marks') or [] if isinstance(m, dict)}
            for s in pv.get('seals') or []:
                if not isinstance(s, str):
                    continue
                items, why = sc.parse(s)
                if why or len(items) != 1:
                    continue
                text, color, shape = items[0]
                hit = by_text.get(sc.norm(text), [])
                if len(hit) != 1 or hit[0] not in seal_ids:
                    continue
                sid = hit[0]
                if sid in mine:
                    have += 1
                    continue
                k = classify(text, color, shape, sid, info)
                if k == 'ok':
                    todo.append((bid, pi, sid, s))
                elif k == '异形':
                    odd.append((bid, pi, sid, s, color + shape))
                else:
                    unk += 1
    key = lambda r: (r[0], r[1])
    return sorted(todo, key=key), sorted(odd, key=key), have, unk


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--root', default=ROOT)
    ap.add_argument('--seal', action='append', required=True, help='印章条 id，可多次')
    ap.add_argument('--limit', type=int, default=200)
    ap.add_argument('--dry-run', action='store_true')
    ap.add_argument('--variants', action='store_true', help='只列异形清单（形色与条不合）')
    a = ap.parse_args(argv)
    import v2common as V
    recs, _, _ = V.load_repo(a.root)
    books = ((i, recs['Book'][i].data) for i in sorted(recs['Book']))
    ents = {i: r.data for i, r in recs['Entity'].items()}
    todo, odd, have, unk = plan(books, ents, set(a.seal))
    if a.variants:
        for r in odd:
            print('\t'.join(str(x) for x in r))
        print('异形 %d 项' % len(odd), file=sys.stderr)
        return
    batch = todo[:a.limit]
    print('可写 %d（本批 %d）；已有 %d；异形 %d；形未核 %d' % (len(todo), len(batch), have, len(odd), unk))
    if a.dry_run:
        for r in batch[:20]:
            print('  ', r)
        return
    marks = collections.defaultdict(list)
    for bid, pi, sid, s in batch:
        marks[bid].append((pi, sid, s))
    for bid, lst in marks.items():
        rec = recs['Book'][bid]
        d = rec.data
        for pi, sid, s in lst:
            pv = d['provenance'][pi]
            ms = pv.setdefault('seal_marks', [])
            if any(m.get('seal_id') == sid for m in ms):
                continue
            ms.append({'seal_id': sid, 'note': s})
        with open(rec.path, 'w', encoding='utf-8', newline='\n') as f:
            f.write(json.dumps(d, ensure_ascii=False, indent=2) + '\n')
    print('已写 %d 项，%d 个 Book' % (len(batch), len(marks)))


if __name__ == '__main__':
    main()
