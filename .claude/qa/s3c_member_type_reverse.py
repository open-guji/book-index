#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""S3c 道：Collection._member_type 计入反挂成员（issue open-guji-core/overview#191）。

S3b（overview#171）的 `_member_type` 只看 Collection 自己的正向清单（`books`／
`contained_works`），漏了 Book／Work 透过自身 `contained_in[].id` 反挂到某 Collection
的情形——协调者验收 #171 时指出：全库最大的几部丛编（如「國立故宮博物院善本舊籍」
约 1.7 万条、「欽定四庫全書·文淵閣本」约 3,600 条）正是全靠反挂，正向清单本就是空的，
S3b 因此漏推了它们的 member_type。

本脚本：
1. 扫全库 Book／Work，建 Collection id -> 反挂计数（Book 侧、Work 侧各一个 Counter）。
2. 用 verify.derive_member_type(d, reverse_has_book, reverse_has_work) 对全库 84 条
   Collection 重新推导 `_member_type`，写回有变动的记录。
3. 打印前后对比（只列有变动的）与新分布，供写进 issue 评论。

跑法：
  python3 .claude/qa/s3c_member_type_reverse.py            # 干跑
  python3 .claude/qa/s3c_member_type_reverse.py --apply    # 落盘（可重跑幂等）
"""
import collections, glob, json, os, sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import verify


def build_reverse_counters():
    IB, IW = verify.idx('books'), verify.idx('works')
    rev_b, rev_w = collections.Counter(), collections.Counter()
    for _, ie in IB.items():
        p = os.path.join(ROOT, ie['path'])
        if not os.path.exists(p): continue
        d = json.load(open(p))
        for ci in (d.get('contained_in') or []):
            cid_ = ci.get('id') if isinstance(ci, dict) else ci
            if cid_: rev_b[cid_] += 1
    for _, ie in IW.items():
        p = os.path.join(ROOT, ie['path'])
        if not os.path.exists(p): continue
        d = json.load(open(p))
        for ci in (d.get('contained_in') or []):
            cid_ = ci.get('id') if isinstance(ci, dict) else ci
            if cid_: rev_w[cid_] += 1
    return rev_b, rev_w


def main():
    apply = '--apply' in sys.argv
    files = {}
    for f in glob.glob(os.path.join(ROOT, 'Collection/*/*/*/*.json')):
        if f.endswith('volume_book_mapping.json'):
            continue
        d = json.load(open(f, encoding='utf-8'))
        files[d['id']] = f

    rev_b, rev_w = build_reverse_counters()

    changed = []
    dist_after = collections.Counter()
    n = 0
    for cid, f in sorted(files.items()):
        d = json.load(open(f, encoding='utf-8'))
        rhb, rhw = bool(rev_b.get(cid, 0)), bool(rev_w.get(cid, 0))
        old = d.get('_member_type')
        new = verify.derive_member_type(d, rhb, rhw)
        dist_after[new] += 1
        if old == new:
            continue
        changed.append((cid, d.get('title'), d.get('subtype'),
                         len(d.get('books') or []), len(d.get('contained_works') or []),
                         rev_b.get(cid, 0), rev_w.get(cid, 0), old, new))
        if new is None:
            if '_member_type' in d:
                del d['_member_type']
        else:
            d['_member_type'] = new
        n += 1
        if apply:
            with open(f, 'w', encoding='utf-8') as out:
                json.dump(d, out, ensure_ascii=False, indent=2)
                out.write('\n')

    print(f'{"id":<14}{"title":<20}{"subtype":<16}{"fwd_b":>6}{"fwd_w":>6}{"rev_b":>7}{"rev_w":>7}  {"old":<6}-> new')
    for cid, title, subtype, fb, fw, rb, rw, old, new in changed:
        print(f'{cid:<14}{title:<20}{subtype:<16}{fb:>6}{fw:>6}{rb:>7}{rw:>7}  {str(old):<6}-> {new}')
    print()
    print(f'共 {len(files)} 條 Collection，{n} 條變動')
    print('新分布：', dict(dist_after))
    print('APPLIED' if apply else 'DRY RUN（加 --apply 落盤）')


if __name__ == '__main__':
    main()
