#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""lane-e 的讀取小工具。只讀不寫；不動 scan.py（硬規矩一）。"""
import glob, json, os, sys
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))
_C = {}
def idx(fam):
    if fam not in _C:
        out = {}
        for f in glob.glob(os.path.join(ROOT, 'index', fam, '*.json')):
            out.update(json.load(open(f)))
        _C[fam] = out
    return _C[fam]
def rec(i):
    for fam in ('works', 'entities', 'books'):
        e = idx(fam).get(i)
        if e: return json.load(open(os.path.join(ROOT, e['path'])))
    raise KeyError(i)
def path(i):
    for fam in ('works', 'entities', 'books'):
        e = idx(fam).get(i)
        if e: return os.path.join(ROOT, e['path'])
    raise KeyError(i)
def save(i, obj):
    p = path(i)
    json.dump(obj, open(p, 'w'), ensure_ascii=False, indent=2)
    open(p, 'a').write('\n')
    return p
if __name__ == '__main__':
    for i in sys.argv[1:]:
        print(json.dumps(rec(i), ensure_ascii=False, indent=1))
