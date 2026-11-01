#!/usr/bin/env python3
"""清除正式库并条墓碑（只删 Work/Book/Entity/Collection 里带 merged_into 的文件）。

  python3 .claude/qa/purge-tombstones/purge.py --book-text ../book-text --out /tmp/purge          # 干跑，出清单
  python3 .claude/qa/purge-tombstones/purge.py --book-text ../book-text --out /tmp/purge --apply  # 真删

保留（不删）三类，原因写进 <out>/保留.tsv：
  T 全文挂在墓碑 id 下：book-text 的 index/texts 键，或 Work/ Book/ 下有该 id 的目录。须先在 book-text 改名到留存 id。
  C 墓碑上带的著录/资源（indexed_by、resources、related_works、sources、additional_titles）在留存条（链末）里找不到。
  R 活记录里有字符串值恰等于墓碑 id（并条账 merged_in／merged_from／merge_history／merged_basis 与文本说明除外）。
被保留的墓碑下一轮清理再试。--apply 会先把「旧 id → 终点」写进 ledger/purge-<日期>.tsv（要提交，verify.py 靠它认并掉的 id）。
--apply 之后：从 index/ 里摘掉被删 id 的条目（不要整体重建，会带进无关漂移），再跑 dedup-census --strict、verify.py。
"""
import argparse, collections, glob, json, os, sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
TYPES = ('Work', 'Book', 'Entity', 'Collection')
# 这些字段里的 id 只是并条留痕/说明，不算引用
HIST_KEYS = {'merged_in', 'merged_from', 'merge_history', 'merged_basis', 'ai_note', 'note', 'why', 'reason',
             'name_basis', 'dynasty_basis', 'period_basis', 'role_basis', 'basis', 'description', 'loss_status_note',
             'alt_names'}
CONTENT_FIELDS = ('indexed_by', 'resources', 'resource_groups', 'related_works', 'sources', 'additional_titles', 'emendated_by')


def rd(p):
    with open(p, encoding='utf-8') as f:
        return json.load(f)


def record_paths(t):
    return sorted(glob.glob(os.path.join(ROOT, t, '*', '*', '*', '*.json')))


def walk(o, path, hit, tomb):
    if isinstance(o, dict):
        for k, v in o.items():
            if k in HIST_KEYS:   # 并条留痕/说明字段整段跳过（任意层）
                continue
            walk(v, path + (k,), hit, tomb)
    elif isinstance(o, list):
        for v in o:
            walk(v, path + ('[]',), hit, tomb)
    elif isinstance(o, str) and o in tomb:
        hit('.'.join(path), o)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--book-text', required=True, help='book-text 仓根（读 index/texts 和 Work/ Book/ 目录）')
    ap.add_argument('--out', required=True)
    ap.add_argument('--apply', action='store_true')
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)

    tomb, recs = {}, {}          # id -> (type, relpath, doc)
    for t in TYPES:
        for p in record_paths(t):
            try:
                d = rd(p)
            except ValueError:
                continue
            if not isinstance(d, dict) or not isinstance(d.get('id'), str):
                continue
            rel = os.path.relpath(p, ROOT)
            recs[d['id']] = (t, rel, d)
            if d.get('merged_into'):
                tomb[d['id']] = (t, rel, d)
    if not tomb or not recs:
        sys.exit('没读到记录，停')
    print('墓碑', collections.Counter(v[0] for v in tomb.values()), '全部记录', len(recs))
    keep = {}                    # id -> (类, 原因)

    # T 全文
    n_idx = 0
    for f in glob.glob(os.path.join(a.book_text, 'index', 'texts', '*.json')):
        n_idx += 1
        for k in rd(f):
            if k in tomb:
                keep.setdefault(k, ('T', 'book-text index/texts 有键'))
    if n_idx != 16:
        sys.exit('book-text index/texts 分片不是 16 个：%d' % n_idx)
    for t in ('Work', 'Book'):
        for p in glob.glob(os.path.join(a.book_text, t, '*', '*', '*', '*')):
            i = os.path.basename(p)
            if i in tomb:
                keep.setdefault(i, ('T', 'book-text/%s 下有目录' % t))

    # C 著录/资源未并到留存条
    def end_of(i):
        seen = 0
        while recs[i][2].get('merged_into') and seen < 30:
            nxt = recs[i][2]['merged_into']
            if nxt not in recs:
                return None
            i = nxt; seen += 1
        return recs[i][2]
    for i, (t, rel, d) in tomb.items():
        if not any(d.get(f) for f in CONTENT_FIELDS):
            continue
        k = end_of(i)
        if k is None:
            keep.setdefault(i, ('C', '链末不存在'))
            continue
        kj = json.dumps(k, ensure_ascii=False, sort_keys=True)
        for f in CONTENT_FIELDS:
            for e in d.get(f) or []:
                # 墓碑指向留存条自己（或自己）的 related_works：并掉后成了自指，不用补
                if f == 'related_works' and isinstance(e, dict) and e.get('id') in recs:
                    t = e['id']
                    for _ in range(30):
                        if not recs[t][2].get('merged_into') or recs[t][2]['merged_into'] not in recs:
                            break
                        t = recs[t][2]['merged_into']
                    if t == k.get('id') or t == i:
                        continue
                    # 留存条已有同目标同关系的条目（只是 note 不同）：不重复补
                    if any(isinstance(x, dict) and x.get('id') == t and x.get('relation') == e.get('relation')
                           for x in k.get('related_works') or []):
                        continue
                s = json.dumps(e, ensure_ascii=False, sort_keys=True)
                if s in kj:
                    continue
                key = e.get('source_bid') or e.get('source') or e.get('id') or e.get('group') if isinstance(e, dict) else e
                if key and str(key) in kj and f in ('indexed_by', 'additional_titles', 'sources'):
                    continue
                keep.setdefault(i, ('C', '%s 有条目未见于留存条：%s' % (f, s[:60])))

    # R 活引用（全部 JSON：四类记录 + 分类 + promotions + curation + 顶层 json）
    refs = collections.defaultdict(list)
    files = [(rel, d) for (_, rel, d) in recs.values() if not d.get('merged_into')]
    for sub in ('classification', 'promotions', 'curation'):
        for p in glob.glob(os.path.join(ROOT, sub, '**', '*.json'), recursive=True):
            files.append((os.path.relpath(p, ROOT), rd(p)))
    for p in glob.glob(os.path.join(ROOT, '*.json')):
        if os.path.basename(p) != 'index.json':
            files.append((os.path.relpath(p, ROOT), rd(p)))
    for rel, d in files:
        walk(d, (), lambda where, i, rel=rel: refs[i].append((rel, where)), tomb)
    for i, rows in refs.items():
        keep.setdefault(i, ('R', '被 %s 的 %s 引用（共 %d 处）' % (rows[0][0], rows[0][1], len(rows))))

    delete = sorted(i for i in tomb if i not in keep)
    cnt = lambda ids: dict(collections.Counter(tomb[i][0] for i in ids))
    print('保留', collections.Counter(v[0] for v in keep.values()), cnt(keep))
    print('将删', len(delete), cnt(delete))
    with open(os.path.join(a.out, '保留.tsv'), 'w', encoding='utf-8') as f:
        f.write('id\t类型\t类\t原因\t文件\n')
        for i, (c, why) in sorted(keep.items()):
            f.write('%s\t%s\t%s\t%s\t%s\n' % (i, tomb[i][0], c, why, tomb[i][1]))
    with open(os.path.join(a.out, '删除.tsv'), 'w', encoding='utf-8') as f:
        f.write('id\t类型\tmerged_into\t文件\n')
        for i in delete:
            f.write('%s\t%s\t%s\t%s\n' % (i, tomb[i][0], tomb[i][2]['merged_into'], tomb[i][1]))
    if a.apply:
        # 先留对照台账（旧 id → 终点），再删文件；verify.py 靠它认「消失的 id 是并掉的，不是误删」
        import datetime
        led = os.path.join(ROOT, '.claude/qa/purge-tombstones/ledger')
        os.makedirs(led, exist_ok=True)
        base = 'purge-%s' % datetime.date.today().strftime('%Y%m%d')
        lp, n = os.path.join(led, base + '.tsv'), 2
        while os.path.exists(lp):   # 同一天清第二次：不覆盖已有台账，加序号
            lp = os.path.join(led, '%s-%d.tsv' % (base, n)); n += 1
        with open(lp, 'w', encoding='utf-8') as f:
            f.write('id\ttype\ttitle\tmerged_into\tfinal_keeper\n')
            for i in delete:
                t, rel, d = tomb[i]
                ti = (d.get('title') or d.get('primary_name') or '').replace('\t', ' ').replace('\n', ' ')
                k = i
                for _ in range(30):
                    n = recs[k][2].get('merged_into')
                    if not n or n not in recs:
                        break
                    k = n
                f.write('\t'.join([i, t, ti, d['merged_into'], recs[k][2]['id'] if not recs[k][2].get('merged_into') else d['merged_into']]) + '\n')
        for i in delete:
            os.remove(os.path.join(ROOT, tomb[i][1]))
        print('已删', len(delete))
        gone = set(delete)
        removed = 0
        for f in sorted(glob.glob(os.path.join(ROOT, 'index', '**', '*.json'), recursive=True)):
            with open(f, encoding='utf-8') as fh:
                raw = fh.read()
            d = json.loads(raw)
            if not isinstance(d, dict):
                continue
            ind = next((x for x in (1, 2) if json.dumps(d, ensure_ascii=False, indent=x).rstrip('\n') == raw.rstrip('\n')), None)
            hit = [k for k in d if k in gone]
            if not hit:
                continue
            if ind is None:
                sys.exit('index 分片缩进认不出，停：' + f)
            for k in hit:
                del d[k]
            removed += len(hit)
            with open(f, 'w', encoding='utf-8') as fh:
                fh.write(json.dumps(d, ensure_ascii=False, indent=ind) + ('\n' if raw.endswith('\n') else ''))
        print('index 摘掉条目', removed)


if __name__ == '__main__':
    main()
