#!/usr/bin/env python3
"""第12组 S2-T 步3：Book.attached_texts[{book_title}] 并入 additional_titles，成 {book_title, type:"附刻"}。
additional_titles 原有字符串（异名）保持在前，附刻之书接在后；删除 attached_texts。可重复运行；--apply 才写盘；
--rollback tsv 写出被动文件原值（path / additional_titles / attached_texts）。
"""
import argparse, glob, json, os


def migrate(d):
    if 'attached_texts' not in d:
        return False
    at = d.pop('attached_texts')
    add = d.get('additional_titles')
    add = list(add) if isinstance(add, list) else []
    for x in at if isinstance(at, list) else []:
        t = x.get('book_title') if isinstance(x, dict) else x
        if t:
            add.append({'book_title': t, 'type': '附刻'})
    if add:
        # 保持 additional_titles 在原位：重建键序
        out = {}
        placed = False
        for k, v in d.items():
            if k == 'additional_titles':
                out[k] = add; placed = True
            else:
                out[k] = v
        if not placed:
            out['additional_titles'] = add
        d.clear(); d.update(out)
    return True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--root', default='.')
    ap.add_argument('--apply', action='store_true')
    ap.add_argument('--rollback')
    a = ap.parse_args()
    n = 0; rb = []
    for p in sorted(glob.glob(os.path.join(a.root, 'Book/**/*.json'), recursive=True)):
        d = json.load(open(p, encoding='utf-8'))
        if 'attached_texts' not in d:
            continue
        rb.append((os.path.relpath(p, a.root), json.dumps(d.get('additional_titles'), ensure_ascii=False), json.dumps(d['attached_texts'], ensure_ascii=False)))
        migrate(d); n += 1
        if a.apply:
            with open(p, 'w', encoding='utf-8') as f:
                f.write(json.dumps(d, indent=2, ensure_ascii=False) + '\n')
    print(f'{"已改" if a.apply else "将改"} {n} 本')
    if a.apply and a.rollback:
        with open(a.rollback, 'w', encoding='utf-8') as f:
            for r in rb:
                f.write('\t'.join(r) + '\n')


if __name__ == '__main__':
    main()
