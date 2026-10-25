#!/usr/bin/env python3
"""去重普查（只读）：按「正式库全面去重方案」口径，出全库重复与并条善后的计数。

    python3 scripts/dedup-census.py                          # 只看正式库
    python3 scripts/dedup-census.py --draft ../book-index-draft --out /tmp/census
    python3 scripts/dedup-census.py --whitelist 已判分立.tsv  # 另加已判分立／存疑对（每行两个 Work id）

一、重复规模（方案部分 7a）
  W  同题 Work 组：题名去括注、过 scan.py 的 VARIANTS 异体表、去空白标点后相同；按首位责任者分四类
     （同首位／一侧有一侧无／全无／不同），按《中国古籍总目》部类分片。「已判」＝组内各条已由
     related_works 互链连成一片（备注写「待並條」的不算），或由 --whitelist 连成一片。
  A  作者位：无责任者的 Work、首位责任者无 entity_id 的 Work、全部无 entity_id 的作者位。
  B  同 Work 下版本名归一后相同的 Book 组；同 Work 同国图 fid 的重复挂接；有多个国图 Book 的 Work。
  E  人物 Entity 主名归一后相同的组（及其中两条以上被 Work 作者引用者）。
  R  related 备注「待並條」的 Work 与链接数。
二、并条善后（方案部分 7b／7c，任一非零即该修）
  T  墓碑链（merged_into 指向墓碑）、merged_into 悬空、成环。
  H  keeper 未在 merged_in／merged_from 记该墓碑（多为立规前的旧并；只出数，不计入 --strict）。
  L  活记录引用墓碑（backrefs.refs_of 各处，不含并条账）；分类成员行、promotions 指向墓碑或不存在。
  D  草稿库（--draft）任一字段值恰等于正式库墓碑 id 者（键 id 除外，同 fix_draft.py 口径）。

只读，不改任何文件。启动打印各类载入条数，任一类为 0 即报错退出（子部四教训）。
--strict：二类任一非零则退出 1，供合并前闸使用。
"""
import argparse
import collections
import glob
import json
import os
import re
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(ROOT, '.claude/qa'))
import backrefs  # noqa: E402
from scan import VARIANTS  # noqa: E402

BRACKETS = re.compile(r'（[^（）]*）|\([^()]*\)|〔[^〔〕]*〕|【[^【】]*】|\[[^\[\]]*\]')
PUNCT = re.compile(r'[\s·・、，,。．.：:；;「」『』《》〈〉()（）〔〕【】\[\]]')
ANONYMOUS = {'', '佚名', '闕名', '缺名', '無名氏', '不著撰人', '不著撰者', '不題撰人', '不詳', '撰者不詳', '□□'}
BULEI = ('經部', '史部', '子部', '集部', '叢書部')
PENDING = ('待並條', '待并条', '待並条', '待并條')
CATS = ('同首位', '一侧有一侧无', '全无', '不同')


def norm(s):
    return PUNCT.sub('', BRACKETS.sub('', s or '').translate(VARIANTS))


def norm_name(s):
    return PUNCT.sub('', (s or '').translate(VARIANTS)).strip('□') if s else ''


class UF:
    def __init__(self):
        self.p = {}

    def find(self, x):
        self.p.setdefault(x, x)
        while self.p[x] != x:
            self.p[x] = self.p[self.p[x]]
            x = self.p[x]
        return x

    def union(self, a, b):
        self.p[self.find(a)] = self.find(b)


def load_json(path):
    with open(path, encoding='utf-8') as f:
        return json.load(f)


def bulei_of_nodes(root):
    """zongmu 节点 → 一级部类。"""
    tree = os.path.join(root, 'classification/zongmu/tree.json')
    if not os.path.exists(tree):
        return {}
    nodes = {n['id']: n for n in load_json(tree)['nodes']}
    out = {}
    for nid in nodes:
        n = nodes[nid]
        while n.get('parent'):
            n = nodes[n['parent']]
        out[nid] = n['label']
    return out


def census(root, draft=None, whitelist=None):
    counts = collections.Counter()
    meta = {}            # id -> (type, merged_into or None)
    hist = collections.defaultdict(set)   # keeper -> merged_in/merged_from ids
    refs = []            # (from_id, where, target)
    works, books, persons, author_refs = {}, [], [], collections.Counter()
    pending, judged = [], []
    for t, p, d in backrefs.iter_records(root):
        rid, into = d['id'], d.get('merged_into')
        meta[rid] = (t, into)
        counts['%s.%s' % (t, 'tomb' if into else 'live')] += 1
        for k in ('merged_in', 'merged_from'):
            for m in d.get(k) or []:
                hist[rid].add(backrefs._ref(m, 'id'))
        if into:
            continue
        for where, tgt, det in backrefs.refs_of(t, d):
            if not where.endswith('merged_in'):
                refs.append((rid, where, tgt))
        if t == 'Work':
            if '敦煌遺書' in (d.get('ai_note') or ''):
                counts['Work.敦煌遺書跳过'] += 1
                continue
            au = [a for a in d.get('authors') or [] if isinstance(a, dict)]
            works[rid] = (norm(d.get('title')), au)
            for a in au:
                if a.get('entity_id'):
                    author_refs[a['entity_id']] += 1
            for r in d.get('related_works') or []:
                if isinstance(r, dict) and r.get('id'):
                    (pending if any(k in (r.get('note') or '') for k in PENDING) else judged).append((rid, r['id']))
        elif t == 'Book':
            fids = {(r.get('metadata') or {}).get('nlc_fid') for r in d.get('resources') or []
                    if isinstance(r, dict) and r.get('id') == 'nlc'} - {None, ''}
            books.append((rid, d.get('work_id'), norm(d.get('edition')), fids))
        elif t == 'Entity' and d.get('subtype') == 'people':
            persons.append((rid, norm_name(d.get('primary_name'))))

    members = collections.defaultdict(list)   # id -> [(scheme, node)]
    for p in glob.glob(os.path.join(root, 'classification/*/members/*.json')):
        scheme = p.split(os.sep)[-3]
        for row in load_json(p).get('members') or []:
            if row:
                members[row[0]].append((scheme, os.path.basename(p)[:-5]))
                counts['classification.rows'] += 1
    promos = {}
    for p in glob.glob(os.path.join(root, 'promotions/*.json')):
        promos.update(load_json(p).get('promotions') or {})
    counts['promotions'] = len(promos)

    print('载入：' + '，'.join('%s %d' % kv for kv in sorted(counts.items())), file=sys.stderr)
    for need in ('Work.live', 'Book.live', 'Entity.live', 'classification.rows', 'promotions'):
        if not counts[need]:
            sys.exit('载入 %s 为 0，路径或仓不对：%s' % (need, root))

    rep = {'载入': dict(counts)}
    detail = {}

    # ── W 同题组
    bulei = bulei_of_nodes(root)

    def bulei_of(wid):
        bs = {bulei.get(n) for s, n in members.get(wid, ()) if s == 'zongmu'}
        return next((b for b in BULEI if b in bs), '未分类')

    link = UF()
    for a, b in judged:
        link.union(a, b)
    for a, b in whitelist or ():
        link.union(a, b)
    groups = collections.defaultdict(list)
    for wid, (key, au) in works.items():
        if key:
            groups[key].append(wid)
    wrep = collections.Counter()
    rows = []
    for key, ids in groups.items():
        if len(ids) < 2:
            continue
        uf, anon = UF(), 0
        for wid in ids:
            a = works[wid][1][:1]
            name = norm_name(a[0].get('name')) if a else ''
            if name in ANONYMOUS:
                anon += 1
                continue
            uf.union(('w', wid), ('n', name))
            if a[0].get('entity_id'):
                uf.union(('w', wid), ('e', a[0]['entity_id']))
        clusters = len({uf.find(('w', w)) for w in ids if ('w', w) in uf.p})
        cat = CATS[3] if clusters > 1 else CATS[2] if not clusters else CATS[1] if anon else CATS[0]
        done = len({link.find(w) for w in ids}) == 1
        bl = min((bulei_of(w) for w in ids), key=lambda b: BULEI.index(b) if b in BULEI else 9)
        wrep['组'] += 1
        wrep['条'] += len(ids)
        wrep['%s组' % cat] += 1
        wrep['%s·%s组' % (bl, cat)] += 1
        wrep['已判组' if done else '未判组'] += 1
        if not done:
            wrep['未判·%s组' % cat] += 1
        rows.append((bl, cat, '已判' if done else '未判', key, len(ids), ','.join(sorted(ids))))
    order = ['组', '条', '已判组', '未判组'] + [x for c in CATS for x in ('%s组' % c, '未判·%s组' % c)]
    order += ['%s·%s组' % (b, c) for b in BULEI + ('未分类',) for c in CATS]
    rep['W 同题组'] = {k: wrep[k] for k in order}
    detail['同题组'] = (('部类', '类别', '判定', '题名键', '条数', 'ids'), sorted(rows))

    # ── A 作者位
    arep = collections.Counter()
    for wid, (key, au) in works.items():
        if not au:
            arep['无责任者 Work'] += 1
            continue
        if not au[0].get('entity_id'):
            arep['首位无 entity_id 的 Work'] += 1
            if norm_name(au[0].get('name')) in ANONYMOUS:
                arep['  其中首位佚名'] += 1
        arep['作者位'] += len(au)
        arep['无 entity_id 作者位'] += sum(1 for a in au if not a.get('entity_id'))
    rep['A 作者位'] = dict(arep)

    # ── B 同 Work 重复 Book
    brep = collections.Counter()
    by_ed, by_fid, nlc_per_work = collections.defaultdict(list), collections.defaultdict(list), collections.Counter()
    for bid, wid, ed, fids in books:
        if wid and ed:
            by_ed[(wid, ed)].append(bid)
        for f in fids:
            by_fid[(wid, f)].append(bid)
        if fids:
            nlc_per_work[wid] += 1
    brows = []
    for (wid, ed), ids in by_ed.items():
        if len(ids) > 1:
            brep['同 Work 同版本名组'] += 1
            brep['  涉及 Book'] += len(ids)
            brows.append(('同版本名', wid, ed, ','.join(sorted(ids))))
    for (wid, f), ids in by_fid.items():
        if len(ids) > 1:
            brep['同 Work 同国图 fid 组'] += 1
            brows.append(('同国图fid', wid, f, ','.join(sorted(ids))))
    brep['有多个国图 Book 的 Work'] = sum(1 for n in nlc_per_work.values() if n > 1)
    rep['B 同 Work 重复 Book'] = dict(brep)
    detail['重复Book'] = (('类别', 'work_id', '键', 'book_ids'), sorted(brows))

    # ── E 人物重名
    erep = collections.Counter()
    by_name = collections.defaultdict(list)
    for eid, name in persons:
        if name:
            by_name[name].append(eid)
    erows = []
    for name, ids in by_name.items():
        if len(ids) > 1:
            cited = [i for i in ids if author_refs[i]]
            erep['同名组'] += 1
            if len(cited) > 1:
                erep['  其中两条以上被作者引用'] += 1
            erows.append((name, len(ids), len(cited), ','.join(sorted(ids))))
    rep['E 人物重名'] = dict(erep)
    detail['人物重名'] = (('主名键', '条数', '被引条数', 'ids'), sorted(erows))

    # ── R 待並條
    rrep = collections.Counter()
    rrep['带待並條链接的 Work'] = len({a for a, _ in pending})
    rrep['待並條链接'] = len(pending)
    rrep['  两端皆活'] = sum(1 for a, b in pending if b in meta and not meta[b][1])
    rep['R related 待並條'] = dict(rrep)
    detail['待並條'] = (('work_id', '指向', '指向状态'),
                      sorted((a, b, '缺' if b not in meta else '墓碑' if meta[b][1] else '活') for a, b in pending))

    # ── T 墓碑
    tomb = {i: m[1] for i, m in meta.items() if m[1]}
    trep, hrep = collections.Counter(), collections.Counter()
    trows = []
    for i, into in tomb.items():
        end, seen = into, {i}
        while end in tomb and end not in seen:
            seen.add(end)
            end = tomb[end]
        if end in seen:
            trep['成环'] += 1
            trows.append(('成环', meta[i][0], i, into, ''))
        elif into not in meta:
            trep['merged_into 悬空'] += 1
            trows.append(('悬空', meta[i][0], i, into, ''))
        elif end != into:
            trep['墓碑链（应改指链末）'] += 1
            trows.append(('链', meta[i][0], i, into, end))
        elif meta[i][0] in ('Work', 'Book', 'Entity') and i not in hist.get(end, ()):
            hrep[meta[i][0]] += 1
            trows.append(('无历史', meta[i][0], i, into, end))
    rep['T 墓碑'] = dict(trep)
    rep['H keeper 未记并入历史（多为立规前旧并，看数不拦）'] = dict(hrep)
    detail['墓碑'] = (('类别', '类型', '墓碑', 'merged_into', '链末'), sorted(trows))

    # ── L 引用墓碑
    lrep = collections.Counter()
    lrows = []
    for src, where, tgt in refs:
        if tgt in tomb:
            lrep[where] += 1
            lrows.append(('引用墓碑', where, src, tgt))
    for wid, rows_ in members.items():
        state = '缺' if wid not in meta else '墓碑' if wid in tomb else None
        if state:
            lrep['分类成员→%s' % state] += len(rows_)
            lrows.extend(('分类成员→' + state, '%s/%s' % r, wid, tomb.get(wid, '')) for r in rows_)
    for k, v in sorted(promos.items()):
        pid = v.get('production_id')
        state = '缺' if pid not in meta else '墓碑' if pid in tomb else None
        if state:
            lrep['promotions→%s' % state] += 1
            lrows.append(('promotions→' + state, k, pid, tomb.get(pid, '')))
    rep['L 引用墓碑'] = dict(lrep)
    detail['引用墓碑'] = (('类别', '处', '指者', '被指'), sorted(lrows))

    # ── D 草稿库
    if draft:
        drep, drows = collections.Counter(), []

        def walk(o, path, hits):
            if isinstance(o, dict):
                for k, v in o.items():
                    if isinstance(v, str) and k != 'id' and v in tomb:
                        hits.append((path + '.' + k, v))
                    else:
                        walk(v, path + '.' + k, hits)
            elif isinstance(o, list):
                for v in o:
                    if isinstance(v, str) and v in tomb:
                        hits.append((path + '[]', v))
                    else:
                        walk(v, path + '[]', hits)

        files = [p for t in backrefs.TYPES for p in backrefs.record_paths(draft, t)]
        files += glob.glob(os.path.join(draft, 'classification/*/members/*.json'))
        files += glob.glob(os.path.join(draft, 'promotions*.json')) + glob.glob(os.path.join(draft, 'promotions/*.json'))
        for p in files:
            try:
                d = load_json(p)
            except ValueError:
                continue
            drep['载入文件'] += 1
            hits = []
            walk(d, '', hits)
            for where, v in hits:
                drep[re.sub(r'^\.', '', re.sub(r'\.promotions\.[^.]+', '.promotions.*', where))] += 1
                drows.append((os.path.relpath(p, draft), where, v, tomb[v]))
        if not drep['载入文件']:
            sys.exit('草稿库载入 0 个文件：%s' % draft)
        rep['D 草稿库指向正式墓碑'] = dict(drep)
        detail['草稿库'] = (('文件', '字段', '正式墓碑', '其 merged_into'), sorted(drows))
    return rep, detail


def main(argv=None):
    ap = argparse.ArgumentParser(description='去重普查（只读）')
    ap.add_argument('--root', default=ROOT, help='正式库根（默认本仓）')
    ap.add_argument('--draft', help='草稿库根，给了才查 D')
    ap.add_argument('--whitelist', action='append', default=[],
                    help='已判分立／存疑对 TSV：每行前两列为两个 Work id（# 开头为注释）')
    ap.add_argument('--out', help='明细 TSV 与 census.json 写入此目录')
    ap.add_argument('--strict', action='store_true', help='T／L／D 任一非零则退出 1')
    a = ap.parse_args(argv)
    wl = []
    for f in a.whitelist:
        for line in open(f, encoding='utf-8'):
            cols = line.rstrip('\n').split('\t')
            if len(cols) >= 2 and not line.startswith('#'):
                wl.append((cols[0].strip(), cols[1].strip()))
    rep, detail = census(os.path.abspath(a.root), a.draft and os.path.abspath(a.draft), wl)
    for sec, kv in rep.items():
        print('【%s】' % sec)
        for k, v in kv.items():
            print('  %s\t%d' % (k, v))
    if a.out:
        os.makedirs(a.out, exist_ok=True)
        with open(os.path.join(a.out, 'census.json'), 'w', encoding='utf-8') as f:
            json.dump(rep, f, ensure_ascii=False, indent=2)
        for name, (head, rows) in detail.items():
            with open(os.path.join(a.out, name + '.tsv'), 'w', encoding='utf-8') as f:
                f.write('\t'.join(head) + '\n')
                f.writelines('\t'.join(map(str, r)) + '\n' for r in rows)
        print('明细写入 %s' % a.out, file=sys.stderr)
    bad = sum(sum(rep.get(s, {}).values()) for s in ('T 墓碑', 'L 引用墓碑'))
    bad += sum(v for k, v in rep.get('D 草稿库指向正式墓碑', {}).items() if k != '载入文件')
    return 1 if a.strict and bad else 0


if __name__ == '__main__':
    sys.exit(main())
