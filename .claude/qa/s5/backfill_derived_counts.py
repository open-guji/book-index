#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""S5 道：通用 todo／審核狀態／派生計數／stale_ref 推廣（overview#189）之派生計數回填。

只做一件事：给全库回填两个新增的 `_` 前缀派生计数字段（定义、校验见
SCHEMA.md〈記錄之共通欄位〉、.claude/qa/verify.py:derive_edition_count／derive_member_count）：

1. Work.`_edition_count`：挂在该 Work 下的 Book 数，由 Book.work_id 反查（不採 Work.`books`
   手写清单——两者全库 95,055 条核有 74 条不一致，见已知问题 s5-20260928-work_books手写清单与
   Book反查不一致.json）。＝0 者不写本栏（沿用 `_has_text` 等「只标异常，不标正常」之例）。
2. Collection.`_member_count`：`books`＋`contained_works` 两份平列成员清单之长度和
   （`contains` 是结构组成部分，不计入，与 `_member_type` 同一口径）。＝0 者不写。

跑法：
  python3 .claude/qa/s5/backfill_derived_counts.py            # 干跑，只列将做的改动
  python3 .claude/qa/s5/backfill_derived_counts.py --apply    # 落盘（幂等：再跑一遍应无改动）
"""
import glob, json, os, sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import verify


def _save(f, d):
    with open(f, 'w', encoding='utf-8') as out:
        json.dump(d, out, ensure_ascii=False, indent=2)
        out.write('\n')


def backfill_works(apply):
    IB = verify.idx('books')
    book_work_ids = {}
    import collections
    book_work_ids = collections.Counter(ie.get('work_id') for ie in IB.values() if ie.get('work_id'))
    n = 0
    for f in glob.glob(os.path.join(ROOT, 'Work/*/*/*/*.json')):
        d = json.load(open(f, encoding='utf-8'))
        wid = d.get('id')
        derived = verify.derive_edition_count(wid, book_work_ids)
        cur = d.get('_edition_count')
        want = derived if derived > 0 else None
        if cur == want:
            continue
        n += 1
        if not apply:
            print(f'  [Work._edition_count] {wid} {cur!r} -> {want!r}')
            continue
        if want is None:
            del d['_edition_count']
        else:
            d['_edition_count'] = want
        _save(f, d)
    return n


def backfill_collections(apply):
    n = 0
    for f in glob.glob(os.path.join(ROOT, 'Collection/*/*/*/*.json')):
        if f.endswith('volume_book_mapping.json'):
            continue
        d = json.load(open(f, encoding='utf-8'))
        cid = d.get('id')
        derived = verify.derive_member_count(d)
        cur = d.get('_member_count')
        want = derived if derived > 0 else None
        if cur == want:
            continue
        n += 1
        if not apply:
            print(f'  [Collection._member_count] {cid} {cur!r} -> {want!r}')
            continue
        if want is None:
            del d['_member_count']
        else:
            d['_member_count'] = want
        _save(f, d)
    return n


def main():
    apply = '--apply' in sys.argv
    n_w = backfill_works(apply)
    n_c = backfill_collections(apply)
    print(f'Work._edition_count 寫入/更新 {n_w}　Collection._member_count 寫入/更新 {n_c}')
    print('APPLIED' if apply else 'DRY RUN（加 --apply 落盤）')


if __name__ == '__main__':
    main()
