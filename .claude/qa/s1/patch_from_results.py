#!/usr/bin/env python3
"""按 out/results.json 与磁盘现状之差，只改动有差异的 Work 档（小说归属修订用）。
不同于 build_classification.py 的 write()（对已有 classification 者跳过），
本脚本专用于「规则改了，需要覆写已写过的值」的场合。"""
import glob, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
OUT = os.path.join(HERE, 'out')


def _fmt_of(raw, d):
    for ind in (2, 1, 4):
        for nl in ('\n', ''):
            if raw == json.dumps(d, ensure_ascii=False, indent=ind) + nl:
                return ind, nl
    return 2, '\n'


def main():
    results = json.load(open(os.path.join(OUT, 'results.json'), encoding='utf-8'))
    changed, added, removed = 0, 0, 0
    touched_ids = []
    for fp in glob.glob(os.path.join(ROOT, 'Work/*/*/*/*.json')):
        raw = open(fp, encoding='utf-8').read()
        d = json.loads(raw)
        wid = d.get('id')
        cur = d.get('classification')
        want = results.get(wid)
        new_val = None
        if want:
            new_val = {'l1': want['l1'], 'l2': want['l2'], 'l3': want['l3'], 'l4': '',
                       'basis': want['basis'], 'source': want['source']}
        if cur == new_val:
            continue
        if new_val is None and cur is not None:
            del d['classification']
            removed += 1
        elif cur is None and new_val is not None:
            d['classification'] = new_val
            added += 1
        else:
            d['classification'] = new_val
            changed += 1
        fmt = _fmt_of(raw, json.loads(raw))
        open(fp, 'w', encoding='utf-8').write(json.dumps(d, ensure_ascii=False, indent=fmt[0]) + fmt[1])
        touched_ids.append(wid)
    print(f'改值 {changed}，新增 {added}，撤销 {removed}，合计触碰 {len(touched_ids)} 档')
    json.dump(touched_ids, open(os.path.join(OUT, 'patched_ids.json'), 'w', encoding='utf-8'), ensure_ascii=False)


if __name__ == '__main__':
    main()
