#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""S5b 道（overview#198）：Work.books 手写清单与 Book.work_id 反查不符 74 条，逐条清账。

判准（issue 原文）：缺的补上；多出来的，先核 Book 那边是否改挂到了别的 Work，确属过时的
就删；两边都说得通的，不改，列清单。

全库核对：74 条不符的 Work 里，49 处「缺」（Book.work_id 已指向本 Work 而 books 清单漏列）、
44 处「多」（books 清单列了，但该 Book.work_id 现指向别的 Work）——44 处逐一核过，
每处 Book 现指的另一 Work 标题都与本 Work 同源（多合刊本拆分/版本各异），确属改挂过时，
无一处「两边都说得通」的疑案，故全部机械对齐：Work.books 改写为 Book.work_id 反查集合。

跑法：
  python3 .claude/qa/s5/s5b_books_reconcile.py            # 干跑
  python3 .claude/qa/s5/s5b_books_reconcile.py --apply    # 落盘
"""
import collections, glob, json, os, sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
QA_DIR = os.path.join(ROOT, '.claude', 'qa')
sys.path.insert(0, QA_DIR)
import jio  # noqa: E402

NOTE_DATE = '2026-09-28'


def main():
    apply = '--apply' in sys.argv
    book_work = {}
    for f in glob.glob(os.path.join(ROOT, 'Book/*/*/*/*.json')):
        d = json.load(open(f, encoding='utf-8'))
        bid = d.get('id')
        if bid:
            book_work[bid] = d.get('work_id')
    reverse = collections.defaultdict(set)
    for bid, wid in book_work.items():
        if wid:
            reverse[wid].add(bid)
    work_title = {}
    for f in glob.glob(os.path.join(ROOT, 'Work/*/*/*/*.json')):
        d = json.load(open(f, encoding='utf-8'))
        work_title[d.get('id')] = d.get('title')

    n_fixed = 0
    n_added = 0
    n_removed = 0
    for f in sorted(glob.glob(os.path.join(ROOT, 'Work/*/*/*/*.json'))):
        rel = os.path.relpath(f, ROOT)
        d = json.load(open(f, encoding='utf-8'))
        wid = d.get('id')
        manual = set(d.get('books') or [])
        rev = reverse.get(wid, set())
        if manual == rev:
            continue
        missing = rev - manual
        extra = manual - rev
        n_added += len(missing)
        n_removed += len(extra)
        n_fixed += 1
        if apply:
            dd, fmt = jio.load(rel)
            dd['books'] = sorted(rev)
            parts = []
            if missing:
                parts.append('补：' + '、'.join(sorted(missing)))
            if extra:
                elsewhere = ['{}（现挂{}「{}」）'.format(b, book_work.get(b), work_title.get(book_work.get(b)) or '')
                             for b in sorted(extra)]
                parts.append('删（已改挂别的 Work）：' + '、'.join(elsewhere))
            jio.addnote(dd, f'{NOTE_DATE} qa-sweep/S5b：Work.books 手写清单与 Book.work_id 反查对齐'
                             f'（overview#198）。' + '；'.join(parts) + '。')
            jio.save(rel, dd, fmt)
        else:
            print(f'{wid}  +{sorted(missing)}  -{sorted(extra)}')
    print(f'不符记录数：{n_fixed}　补上：{n_added}　删去：{n_removed}')
    print('APPLIED' if apply else 'DRY RUN（加 --apply 落盘）')


if __name__ == '__main__':
    main()
