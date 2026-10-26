"""回补：merge_books.py 早期版本只并入被并者的 contained_in/resources，漏了 sources/indexed_by/provenance。
从已合各批 merges.json 的 base 提交读出被并者原文，把这三栏缺的条目补进 keeper（keeper 已被再并则跳过）。
用法：python3 union_lost_fields.py <merges.json>... [--apply]"""
import argparse, json, os, subprocess, sys

ROOT = subprocess.check_output(['git', 'rev-parse', '--show-toplevel'], text=True).strip()
TODAY = '2026-10-25'
FIELDS = ('sources', 'indexed_by', 'provenance')


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('ledgers', nargs='+'); ap.add_argument('--apply', action='store_true')
    a = ap.parse_args()
    out = []
    for lg in a.ledgers:
        m = json.load(open(lg, encoding='utf-8'))
        for g in m['merges']:
            kp = g['preconditions'][0]['path']; assert g['preconditions'][0]['id'] == g['keeper']
            k = json.load(open(os.path.join(ROOT, kp), encoding='utf-8'))
            if k.get('merged_into'): print('跳过（keeper 已被并）', g['keeper'], file=sys.stderr); continue
            added = {}
            for p in g['preconditions'][1:]:
                d = json.loads(subprocess.check_output(['git', 'show', m['base'] + ':' + p['path']], cwd=ROOT))
                for f in FIELDS:
                    for x in d.get(f) or []:
                        if x not in (k.get(f) or []):
                            k.setdefault(f, []).append(x); added.setdefault(f, []).append(x)
            if not added: continue
            rev = '%d.0.0' % (int((k.get('revision') or '1.0.0').split('.')[0]) + 1)
            k.pop('revision', None); k.pop('revised_at', None); k['revision'] = rev; k['revised_at'] = TODAY
            if a.apply:
                open(os.path.join(ROOT, kp), 'w', encoding='utf-8').write(json.dumps(k, ensure_ascii=False, indent=2) + '\n')
            out.append({'ledger': os.path.relpath(lg, ROOT), 'keeper': g['keeper'], 'path': kp, 'added': added})
            print(g['keeper'], {f: len(v) for f, v in added.items()})
    print('补了', len(out), '个 keeper', file=sys.stderr)
    if a.apply:
        json.dump(out, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '回补清單.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)


if __name__ == '__main__':
    main()
