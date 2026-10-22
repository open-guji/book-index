#!/usr/bin/env python3
"""并条台账独立审计：不信台账自述，直接对比并前（--base）与并后（工作树）的数据。

用法（在 book-index 仓根，工作树已切到待审 PR 分支）：
    python3 scripts/audit-merge-ledger.py --ledger <merges.json> --base origin/main [--draft ../book-index-draft]

检查项（任一 ERROR 即退出码 1）：
  T 墓碑：被并者只剩 schema 允许的最小字段，merged_into 指向 keeper，keeper 不是墓碑，且有 merged_from/merged_in 历史
  L 无损：被并者的 contained_in／resources／indexed_by／authors 名，并后在 keeper 里仍找得到
  P 升格表：base→并后 promotions 里 production_id 的变化必须全部是 被并者→keeper，不得有别的变动
  R 引用：除墓碑自身 id、merged_*、index 外，活跃记录里不得再出现被并 ID
  D 草稿库（给 --draft 才查）：草稿库里指向被并 ID 的 work_id／merged_into／related_works／分类成员（须另开草稿库 PR 改指 keeper）
  Q 质量统计（WARN）：Work 组首位责任者不同、题名不同的组数；Book 组 edition／dating／title 不同的组数
"""
import argparse, collections, glob, json, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOMB_OK = {'schema_version', 'type', 'subtype', 'id', 'title', 'primary_name', 'work_id',
           'revision', 'revised_at', 'updated_at', 'merged_into'}
CLS = {'work': 'Work', 'book': 'Book', 'people': 'Entity'}


def git_batch(ref, paths):
    p = subprocess.Popen(['git', '-c', 'core.quotePath=false', 'cat-file', '--batch'],
                         stdin=subprocess.PIPE, stdout=subprocess.PIPE, cwd=ROOT)
    out = {}
    for path in paths:
        p.stdin.write(f'{ref}:{path}\n'.encode()); p.stdin.flush()
        head = p.stdout.readline().split()
        if head[-1] == b'missing':
            out[path] = None; continue
        body = p.stdout.read(int(head[2])); p.stdout.read(1)
        out[path] = json.loads(body)
    p.stdin.close(); p.wait()
    return out


def refs_in(obj, targets, path=()):
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield from refs_in(v, targets, path + (k,))
    elif isinstance(obj, list):
        for v in obj:
            yield from refs_in(v, targets, path + ('[]',))
    elif isinstance(obj, str) and obj in targets:
        yield path, obj


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--ledger', type=Path, required=True)
    ap.add_argument('--base', default='origin/main')
    ap.add_argument('--draft', type=Path, help='book-index-draft 工作树（可选）')
    a = ap.parse_args()
    ledger = json.loads(a.ledger.read_text(encoding='utf-8'))['merges']
    mapping = {l: s['keeper'] for s in ledger for l in s['losers']}
    path_of = {p['id']: p['path'] for s in ledger for p in s['preconditions']}
    base = git_batch(a.base, list(path_of.values()))
    err = collections.Counter(); warn = collections.Counter(); ex = collections.defaultdict(list)

    def bad(code, msg):
        err[code] += 1
        if len(ex[code]) < 5: ex[code].append(msg)

    for s in ledger:
        keeper = json.loads((ROOT / path_of[s['keeper']]).read_text(encoding='utf-8'))
        kb = base[path_of[s['keeper']]]
        if keeper.get('merged_into'): bad('T', f"{s['cluster_id']} keeper 是墓碑")
        hist = keeper.get('merged_from') or keeper.get('merged_in') or []
        hist_ids = {h.get('id') if isinstance(h, dict) else h for h in hist}
        for l in s['losers']:
            tomb = json.loads((ROOT / path_of[l]).read_text(encoding='utf-8'))
            lb = base[path_of[l]]
            if tomb.get('merged_into') != s['keeper']: bad('T', f"{l} merged_into 不对")
            if set(tomb) - TOMB_OK: bad('T', f"{l} 墓碑多余字段 {sorted(set(tomb) - TOMB_OK)}")
            if l not in hist_ids: bad('T', f"{l} 未入 keeper 并条历史")
            if s['type'] == 'book':
                kc = [(w.get('id') if isinstance(w, dict) else w) for w in keeper.get('contained_in') or []]
                for w in lb.get('contained_in') or []:
                    if (w.get('id') if isinstance(w, dict) else w) not in kc: bad('L', f"{l} 丢 contained_in {w}")
                kr = json.dumps(keeper.get('resources'), ensure_ascii=False)
                for r in lb.get('resources') or []:
                    if str(r.get('url') or r.get('id') or r) not in kr: bad('L', f"{l} 丢 resource {str(r)[:80]}")
                for f in ('edition', 'dating', 'title'):
                    if kb.get(f) != lb.get(f): warn['Q:book.' + f] += 1
            if s['type'] == 'work':
                ks = {(i.get('source'), i.get('source_bid')) for i in keeper.get('indexed_by') or []}
                for i in lb.get('indexed_by') or []:
                    if (i.get('source'), i.get('source_bid')) not in ks: bad('L', f"{l} 丢 indexed_by {i.get('source')}")
                kj = json.dumps(keeper, ensure_ascii=False)
                for au in lb.get('authors') or []:
                    if str(au.get('name')) not in kj: bad('L', f"{l} 丢作者 {au.get('name')}")
                first = lambda r: [(x.get('name'), x.get('entity_id')) for x in r.get('authors') or []][:1]
                if first(kb) != first(lb): warn['Q:work.首位责任者不同'] += 1
                if kb.get('title') != lb.get('title'): warn['Q:work.题名不同'] += 1
                for f in ('description', 'ai_note'):
                    if lb.get(f) and str(lb[f]) not in kj: warn['Q:work.被并者' + f + '未保留'] += 1

    # P 升格表
    for f in sorted(glob.glob(str(ROOT / 'promotions/*.json'))):
        rel = str(Path(f).relative_to(ROOT))
        old = json.loads(subprocess.check_output(['git', 'show', f'{a.base}:{rel}'], cwd=ROOT))['promotions']
        new = json.loads(Path(f).read_text(encoding='utf-8'))['promotions']
        for k in set(old) | set(new):
            o = (old.get(k) or {}).get('production_id'); n = (new.get(k) or {}).get('production_id')
            if o != n and mapping.get(o) != n: bad('P', f'{rel} {k}: {o} -> {n}')
            elif o == n and old.get(k) != new.get(k): bad('P', f'{rel} {k}: 其它字段被改')

    # R 引用
    targets = set(mapping)
    listing = subprocess.run(['rg', '-l', '-F', '-f', '/dev/stdin', '--glob', '*.json', 'Work', 'Book', 'Collection',
                              'Entity', 'classification', 'promotions', 'curation', 'recommended.json'],
                             input='\n'.join(targets) + '\n', cwd=ROOT, text=True, capture_output=True).stdout.split()
    for f in listing:
        for p, v in refs_in(json.loads((ROOT / f).read_text(encoding='utf-8')), targets):
            if p == ('id',) or p == ('merged_into',) or p[0] in ('merged_from', 'merged_in'): continue
            bad('R', f'{f[-70:]} {"/".join(p)}={v}')

    # D 草稿库
    if a.draft:
        dl = subprocess.run(['rg', '-l', '-F', '-f', '/dev/stdin', '--glob', '*.json', '--glob', '!index/**', '.'],
                            input='\n'.join(targets) + '\n', cwd=a.draft, text=True, capture_output=True).stdout.split()
        for f in dl:
            for p, v in refs_in(json.loads((a.draft / f).read_text(encoding='utf-8')), targets):
                if p == ('id',): continue
                err['D'] += 1
                warn['D.' + p[0]] += 1
                if len(ex['D']) < 5: ex['D'].append(f'{f[-60:]} {"/".join(p)}={v}')

    print(f'台账 {len(ledger)} 组，被并 {len(mapping)} 条')
    for c in 'TLPRD':
        print(f'[{c}] ERROR {err[c]}')
        for m in ex[c]: print('    ', m)
    for k, v in sorted(warn.items()): print(f'[WARN] {k}: {v}')
    sys.exit(1 if err else 0)


if __name__ == '__main__':
    main()
