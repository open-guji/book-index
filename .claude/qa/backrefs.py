#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""「誰指著我」——一條記錄被別處指著的地方，做成一張可查之表。

**所以立此**：坑 41 說併條之善後三件、坑 61 補第四、坑 64 第五，
每次以為數全了就又冒出一處。坑 64 自己下的結論是：
「根子是『一條記錄被別處指著的地方』沒有一張總表——與其一次次補，
不如把『誰指著我』做成可查之物。」本檔即那張表。

    python3 .claude/qa/backrefs.py <id> [<id> ...]     # 列誰指著它
    python3 .claude/qa/backrefs.py --audit             # 全庫懸空稽核
    python3 .claude/qa/backrefs.py --root ../book-index-draft --audit

**schema-v2（2026-10-07 起，SCHEMA〈〇〉）**：源檔裡一條關係只存一側，故本表只列
**存儲一側**的引用——反向（`Work.books`、`Entity.works`、`Collection.books／contained_works`、
`has_part`／`studied_by` 等）已不在源檔，由 build 生成，改名／併條都不必管它們。
現行引用處（`PLACES`）：

  Book.work_id                       版本 → 作品
  Collection.work_id                 叢編 → 傘狀作品
  {Work,Book,Collection}.contained_in 成員 → 叢編
  Work.authors.entity_id             作品 → 人物
  Work.related_works                 規範方向之關係（跨 Work／Collection 二 id 空間——坑 61）
  *.indexed_by／emendated_by          著錄 → 志書（source_bid、in_note_of）
  Book.base_edition                  底本（book_id／work_id）
  Book.lineage                       承襲（derived_from[].ref、related_to[].book_id）
  Collection.contains                結構組成（work_id／book_id／collection_id）
  Book.related_books／Collection.related_*  對稱關係（存小 id 側）
  Work／Entity.merged_in／merged_from／merged_into  併條之賬（墓誌，不算懸空）
  classification/<法>/members        分類成員行

舊格式欄（`LEGACY`）若仍在源檔（迁移後新進之舊格式批），照列並標「舊格式」——
它們是 `check_v2.py` 該擋的殘留，併條工具**不改寫**它們。

坑 61 之戒：`related_works` 之 id 可指 Collection（8rlcsybg2hhm 十三經等），
**「不在 Work 裡」不等於「不存在」**。`universe()` 取四類記錄 id 之並集。
"""
import json, os, glob, argparse, collections

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
TYPES = ('Work', 'Book', 'Collection', 'Entity')
LEGACY = ('Work.books', 'Entity.works', 'Collection.books', 'Collection.contained_works')
MERGE_LOG = 'merged_in'


def record_paths(root, typ):
    """記錄檔＝`<Type>/<a>/<b>/<c>/<id>[-題名].json`；更深者是 sidecar／整理本，不讀。"""
    return sorted(glob.glob(os.path.join(root, typ, '*', '*', '*', '*.json')))


def iter_records(root=None):
    root = root or ROOT
    for t in TYPES:
        for p in record_paths(root, t):
            try:
                d = json.load(open(p, encoding='utf-8'))
            except ValueError:
                continue
            if isinstance(d, dict) and isinstance(d.get('id'), str):
                yield t, p, d


def _ref(x, *keys):
    if isinstance(x, str):
        return x
    if isinstance(x, dict):
        for k in keys or ('id',):
            if isinstance(x.get(k), str) and x[k]:
                return x[k]
    return None


def refs_of(t, d):
    """一條記錄指出去的所有引用：[(處, 目標 id, 細目)]。"""
    out = []
    add = lambda where, tgt, det=None: tgt and out.append((where, tgt, det))
    if t in ('Book', 'Collection'):
        add('%s.work_id' % t, d.get('work_id') if isinstance(d.get('work_id'), str) else None)
    ci = d.get('contained_in') or []
    for c in (ci if isinstance(ci, list) else [ci]):
        add('%s.contained_in' % t, _ref(c, 'id'), (c.get('volume_index') if isinstance(c, dict) else None))
    for a in (d.get('authors') or []):
        if isinstance(a, dict):
            add('%s.authors.entity_id' % t, a.get('entity_id'), a.get('name'))
    for r in (d.get('related_works') or []):
        add('%s.related_works' % t, _ref(r, 'id', 'work_id'), r.get('relation') if isinstance(r, dict) else None)
    for fld in ('indexed_by', 'emendated_by'):
        for n in (d.get(fld) or []):
            if isinstance(n, dict):
                add('%s.%s.source_bid' % (t, fld), n.get('source_bid'), n.get('source'))
                add('%s.%s.in_note_of' % (t, fld), n.get('in_note_of'))
    for be in (d.get('base_edition') or []):
        if isinstance(be, dict):
            add('Book.base_edition', be.get('book_id'), be.get('role'))
            add('Book.base_edition', be.get('work_id'), be.get('role'))
    lin = d.get('lineage') if isinstance(d.get('lineage'), dict) else {}
    for x in (lin.get('derived_from') or []):
        if isinstance(x, dict) and x.get('ref_type', 'book') == 'book':
            add('Book.lineage', x.get('ref'), x.get('relation'))
    for x in (lin.get('related_to') or []):
        add('Book.lineage', _ref(x, 'book_id'), None)
    for c in (d.get('contains') or []):
        if isinstance(c, dict):
            for k in ('work_id', 'book_id', 'collection_id'):
                add('Collection.contains', c.get(k), c.get('type'))
    for fld in ('related_books', 'related_collections'):
        for x in (d.get(fld) or []):
            add('%s.%s' % (t, fld), _ref(x, 'id', 'work_id'), None)
    for fld in ('merged_in', 'merged_from', 'merged_into'):
        v = d.get(fld) or []
        for m in (v if isinstance(v, list) else [v]):
            add(MERGE_LOG if t == 'Work' else '%s.merged_in' % t, _ref(m, 'id'), fld)
    # 舊格式殘留（只列不改）
    if t == 'Work':
        for b in (d.get('books') or []):
            add('Work.books', _ref(b), '舊格式')
    if t == 'Entity':
        for w in (d.get('works') or []):
            add('Entity.works', _ref(w, 'work_id'), '舊格式')
    if t == 'Collection':
        for b in (d.get('books') or []):
            add('Collection.books', _ref(b, 'book_id', 'id'), '舊格式')
        for c in (d.get('contained_works') or []):
            add('Collection.contained_works', _ref(c, 'id', 'work_id'), '舊格式')
    return out


def class_member_refs(root=None):
    """分類成員行：{work_id: [(檔, source)]}。"""
    root = root or ROOT
    out = collections.defaultdict(list)
    for p in sorted(glob.glob(os.path.join(root, 'classification', '*', 'members', '*.json'))):
        d = json.load(open(p, encoding='utf-8'))
        for row in d.get('members') or []:
            if row:
                out[row[0]].append((os.path.relpath(p, root), row[1] if len(row) > 1 else None))
    return out


def universe(root=None):
    """四類記錄 id 之並集——坑 61：以「查某表查不到」為由而刪者，先問「它會不會在別的表裡」。"""
    return {d['id'] for _, _, d in iter_records(root)}


def scan(root=None):
    """回 {被指之 id: [(處, 指者之 id, 細目), ...]}。"""
    root = root or ROOT
    back = collections.defaultdict(list)
    for t, p, d in iter_records(root):
        for where, tgt, det in refs_of(t, d):
            back[tgt].append((where, d['id'], det))
    for wid, rows in class_member_refs(root).items():
        for f, src in rows:
            back[wid].append(('classification.members', f, src))
    return back


def main(argv=None):
    global ROOT
    ap = argparse.ArgumentParser(description='誰指著我')
    ap.add_argument('ids', nargs='*')
    ap.add_argument('--root', default=ROOT, help='數據倉根（預設本倉）')
    ap.add_argument('--ref-root', action='append', default=[],
                    help='另一倉（草稿庫稽核時指正式庫，其 id 不算懸空）')
    ap.add_argument('--audit', action='store_true', help='全庫懸空稽核（指向不存在之 id 者）')
    ap.add_argument('--zombies', action='store_true', help=
        '稽核「殭屍」：一條**既有 `merged_into`（自稱已被併走）又載著內容**（authors／indexed_by／description）。'
        '成因是併條所留之墓碑被後來之入庫誤認作待補活條而回填復活。'
        '處分視所填者而定：仍是同書則併，已是別書則去其 merged_into 令各自獨立。')
    ap.add_argument('--unexecuted', action='store_true', help=
        '稽核「宣告了而未執行的併」：keeper 之 merged_from／merged_in 指著一條**仍是完整記錄**者。'
        '**墓碑不算**（僅 id／title／merged_into 數欄、無著錄）。')
    a = ap.parse_args(argv)
    ROOT = os.path.abspath(a.root)
    works = {d['id']: d for t, _, d in iter_records(ROOT) if t == 'Work'}

    if a.zombies:
        z = [(i, d.get('title'), d.get('merged_into'), len(d.get('indexed_by') or []))
             for i, d in works.items()
             if d.get('merged_into') and (d.get('indexed_by') or d.get('authors') or d.get('description'))]
        print('殭屍（有 merged_into 而又載著內容）：%d' % len(z))
        for i, t, m, n in sorted(z, key=lambda x: x[1] or ''):
            print('   %s %-16s -> %s（著錄 %d 節）' % (i, t, m, n))
        return 0

    if a.unexecuted:
        def is_tomb(d):
            return bool(d.get('merged_into')) and len(d.keys()) <= 8 and not d.get('indexed_by')
        real, tombs = [], 0
        for me, d in works.items():
            for key in ('merged_from', 'merged_in'):
                for m in (d.get(key) or []):
                    t = _ref(m, 'id')
                    if not t or t not in works or t == me:
                        continue
                    if is_tomb(works[t]):
                        tombs += 1
                    else:
                        real.append((me, d.get('title'), key, t, len(works[t].get('indexed_by') or [])))
        print('宣告已併而所併之條仍是完整記錄：%d 處（另有 %d 處所併者是墓碑，合乎庫例）' % (len(real), tombs))
        for me, ti, key, t, n in sorted(real, key=lambda x: x[1] or ''):
            print('   keeper=%s %-16s %s -> %s（尚有著錄 %d 節）' % (me, ti, key, t, n))
        return 0

    back = scan(ROOT)
    if a.audit:
        u = universe(ROOT)
        for rr in a.ref_root:
            u |= universe(os.path.abspath(rr))
        bad = {}
        for k, v in back.items():
            if k in u:
                continue
            live = [x for x in v if not x[0].endswith('merged_in')]   # 併條賬本就指著已廢之 id
            if live:
                bad[k] = live
        n = sum(len(v) for v in bad.values())
        print('懸空之 id %d 個，處 %d' % (len(bad), n))
        per = collections.Counter(w for v in bad.values() for w, _, _ in v)
        for w, c in per.most_common():
            print('   %-32s %5d' % (w, c))
        for k, v in sorted(bad.items()):
            for w, src, det in v:
                print('   %s  <- %s  %s  %s' % (k, w, src, det or ''))
        return 1 if bad else 0
    for i in a.ids:
        print('== %s ==' % i)
        for w, src, det in sorted(back.get(i, []), key=lambda x: (x[0], x[1], str(x[2]))):
            print('   %-32s %s  %s' % (w, src, det or ''))
        if not back.get(i):
            print('   （無人指）')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
