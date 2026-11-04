#!/usr/bin/env python3
"""第12组 S2-T 验收：Book 的 index 条目里 additional_titles／attached_texts（build_derived._titles_split）迁移前后须逐字相同。
  python3 .claude/qa/extra_titles_equiv.py dump --root . --out /tmp/a.json
  python3 .claude/qa/extra_titles_equiv.py diff /tmp/a.json /tmp/b.json
"""
import glob, json, os, sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'build'))


def main():
    if sys.argv[1] == 'dump':
        import build_derived as bd
        root = sys.argv[sys.argv.index('--root') + 1] if '--root' in sys.argv else '.'
        out = sys.argv[sys.argv.index('--out') + 1]
        res = {}
        for f in sorted(glob.glob(os.path.join(root, 'Book/*/*/*/*.json'))):
            d = json.load(open(f, encoding='utf-8'))
            a, b = bd._titles_split(d)
            if a or b:
                res[d['id']] = [a, b]
        json.dump(res, open(out, 'w', encoding='utf-8'), ensure_ascii=False, sort_keys=True)
        print('books with extra titles', len(res))
    else:
        a, b = (json.load(open(p, encoding='utf-8')) for p in sys.argv[2:4])
        bad = [k for k in set(a) | set(b) if a.get(k) != b.get(k)]
        print('differences', len(bad))
        for k in sorted(bad)[:10]:
            print(k, a.get(k), b.get(k))
        sys.exit(1 if bad else 0)


main()
