#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""「誰指著我」——一條記錄被別處指著的地方，做成一張可查之表。

**所以立此**：坑 41 說併條之善後三件、坑 61 補第四、坑 64 第五，
每次以為數全了就又冒出一處。坑 64 自己下的結論是：
「根子是『一條記錄被別處指著的地方』沒有一張總表——與其一次次補，
不如把『誰指著我』做成可查之物。」本檔即那張表。

    python3 .claude/qa/backrefs.py <work_id> [<work_id> ...]   # 列誰指著它
    python3 .claude/qa/backrefs.py --audit                     # 全庫懸空稽核

**七處**（非五處——`Collection.contained_works` 與 `Work.books` 是掃出來的，
不在坑 41／61／64 之列，且 `verify.py` 不驗前者）：

  1. index/works/*.json                 索引項            （坑 41）
  2. Entity.works[].work_id             entity 反邊       （坑 41）
  3. Work.indexed_by[]                  著錄（併入 keeper）（坑 41）
  4. Work.related_works[].id / .work_id 他條之關聯        （坑 61；跨 Work／Collection 二 id 空間）
  5. Work.books[]                       所繫之 Book
  6. Collection.contained_works[].id    叢書子目          ← verify.py **不驗**，斷了無人知
  7. Work.merged_in[] / merged_into     併條之賬

坑 61 之戒：`related_works` 之 id 可指 Collection（8rlcsybg2hhm 十三經等），
**「不在 Work 索引裡」不等於「不存在」**。本檔比對五個 id 空間之並集，不單比 Work。
"""
import json, os, glob, sys, argparse, collections

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))


def _idx(fam):
    out = {}
    for f in glob.glob(os.path.join(ROOT, 'index', fam, '*.json')):
        out.update(json.load(open(f)))
    return out


def universe():
    """五個 id 空間之並集——坑 61：以「查某表查不到」為由而刪者，先問「它會不會在別的表裡」。"""
    u = set(_idx('works')) | set(_idx('books')) | set(_idx('entities'))
    u |= set(json.load(open(os.path.join(ROOT, 'index', 'collections.json'))))
    return u


def scan():
    """回 {被指之 id: [(處, 指者之 id, 細目), ...]}。"""
    back = collections.defaultdict(list)
    for wid, ie in _idx('works').items():
        back[wid].append(('index/works', wid, ie.get('path')))
    for p in glob.glob(os.path.join(ROOT, 'Work/*/*/*/*.json')):
        d = json.load(open(p))
        me = d.get('id')
        for r in (d.get('related_works') or []):
            t = r.get('id') or r.get('work_id')      # 坑 54 之族：二形並存
            if t:
                back[t].append(('Work.related_works', me, r.get('relation')))
        for b in (d.get('books') or []):
            back[b].append(('Work.books', me, None))
        for a in (d.get('authors') or []):
            if a.get('entity_id'):
                back[a['entity_id']].append(('Work.authors.entity_id', me, a.get('name')))
        mi = d.get('merged_in') or d.get('merged_into') or []
        for m in (mi if isinstance(mi, list) else [mi]):
            t = m.get('id') if isinstance(m, dict) else m
            if t:
                back[t].append(('Work.merged_in', me, None))
    for p in glob.glob(os.path.join(ROOT, 'Entity/*/*/*/*.json')):
        d = json.load(open(p))
        me = d.get('id')
        for w in (d.get('works') or []):
            if w.get('work_id'):
                back[w['work_id']].append(('Entity.works', me, w.get('role')))
    for p in glob.glob(os.path.join(ROOT, 'Collection/*/*/*/*.json')):
        d = json.load(open(p))
        me = d.get('id')
        for c in (d.get('contained_works') or []):
            t = c.get('id') or c.get('work_id')
            if t:
                back[t].append(('Collection.contained_works', me, c.get('title')))
    return back


def main():
    ap = argparse.ArgumentParser(description='誰指著我')
    ap.add_argument('ids', nargs='*')
    ap.add_argument('--audit', action='store_true', help='全庫懸空稽核（指向不存在之 id 者）')
    ap.add_argument('--zombies', action='store_true', help=
        '稽核「殭屍」：一條**既有 `merged_into`（自稱已被併走）又載著內容**（authors／indexed_by／description）。'
        '成因是併條所留之墓碑（恰五欄、無 authors 無 indexed_by）被後來之入庫誤認作「同題而無撰人」之'
        '待補活條而回填復活。**留著它是危險的**——凡循 merged_into 改指之工具，都會把該書之引用'
        '轉到那個不相干的條上去。處分視所填者而定：仍是同書則併（併之即並去其殭屍），已是別書則'
        '去其 merged_into 令各自獨立。')
    ap.add_argument('--unexecuted', action='store_true', help=
        '稽核「宣告了而未執行的併」：keeper 之 merged_from／merged_in 指著一條**仍是完整記錄**者。'
        '**墓碑不算**——庫例許被併之條留一枚墓碑（僅 id／title／merged_into 數欄、無著錄）以示去向。'
        '此檢與坑 64 之賬病互補：坑 64 是「做了而沒記」，此是「記了而沒做」。')
    a = ap.parse_args()
    if a.zombies:
        z = []
        for p in glob.glob(os.path.join(ROOT, 'Work/*/*/*/*.json')):
            d = json.load(open(p))
            if d.get('merged_into') and (d.get('indexed_by') or d.get('authors') or d.get('description')):
                z.append((d.get('id'), d.get('title'), d.get('merged_into'),
                          len(d.get('indexed_by') or [])))
        print('殭屍（有 merged_into 而又載著內容）：%d' % len(z))
        for i, t, m, n in sorted(z, key=lambda x: x[1] or ''):
            print('   %s %-16s -> %s（著錄 %d 節）' % (i, t, m, n))
        return

    if a.unexecuted:
        recs = {}
        for p in glob.glob(os.path.join(ROOT, 'Work/*/*/*/*.json')):
            d = json.load(open(p)); recs[d.get('id')] = d
        def is_tomb(d):
            return bool(d.get('merged_into')) and len(d.keys()) <= 8 and not d.get('indexed_by')
        real, tombs = [], 0
        for me, d in recs.items():
            for key in ('merged_from', 'merged_in'):
                for m in (d.get(key) or []):
                    t = m.get('id') if isinstance(m, dict) else m
                    if not t or t not in recs or t == me:
                        continue
                    if is_tomb(recs[t]):
                        tombs += 1
                    else:
                        real.append((me, d.get('title'), key, t,
                                     len(recs[t].get('indexed_by') or [])))
        print('宣告已併而所併之條仍是完整記錄：%d 處（另有 %d 處所併者是墓碑，合乎庫例）'
              % (len(real), tombs))
        for me, ti, key, t, n in sorted(real, key=lambda x: x[1] or ''):
            print('   keeper=%s %-16s %s -> %s（尚有著錄 %d 節）' % (me, ti, key, t, n))
        return

    back = scan()
    if a.audit:
        u = universe()
        # merged_in 是墓誌：它本來就指著已廢之 id，不是懸空。
        bad = {}
        for k, v in back.items():
            if k in u:
                continue
            live = [x for x in v if x[0] != 'Work.merged_in']
            if live:
                bad[k] = live
        n = sum(len(v) for v in bad.values())
        print('懸空之 id %d 個，處 %d' % (len(bad), n))
        per = collections.Counter(w for v in bad.values() for w, _, _ in v)
        for w, c in per.most_common():
            print('   %-28s %5d' % (w, c))
        for k, v in sorted(bad.items()):
            for w, src, det in v:
                print('   %s  <- %s  %s  %s' % (k, w, src, det or ''))
        return
    for i in a.ids:
        print('== %s ==' % i)
        for w, src, det in sorted(back.get(i, [])):
            print('   %-28s %s  %s' % (w, src, det or ''))
        if not back.get(i):
            print('   （無人指）')


if __name__ == '__main__':
    main()
