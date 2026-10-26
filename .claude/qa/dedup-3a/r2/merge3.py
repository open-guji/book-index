#!/usr/bin/env python3
"""合并 main 时 Work/Book JSON 冲突的三方逐键合并。用法：merge3.py <base 提交> <冲突文件>...
逐顶层键：一侧未改取另一侧；两侧都改：ai_note 取对方全文再接本侧新增段；merged_in／merged_from 取并集；
dict/list 递归同法（list 按元素并集，仅当两侧都是在 base 上追加时）；其余报真冲突、不写。对方已成墓碑者报出。"""
import json, subprocess, sys

base_ref = sys.argv[1]


def show(ref, p):
    try:
        return json.loads(subprocess.check_output(['git', 'show', f'{ref}:{p}'], stderr=subprocess.DEVNULL))
    except subprocess.CalledProcessError:
        return None


class Conflict(Exception):
    pass


def m(b, o, t, key=''):
    if o == t:
        return o
    if o == b:
        return t
    if t == b:
        return o
    if isinstance(o, dict) and isinstance(t, dict):
        b = b if isinstance(b, dict) else {}
        out = {}
        for k in list(t.keys()) + [k for k in o if k not in t]:
            out[k] = m(b.get(k), o.get(k), t.get(k), k)
        return {k: v for k, v in out.items() if v is not None or (k in o and o[k] is None)}
    if key == 'ai_note' and isinstance(o, str) and isinstance(t, str) and isinstance(b, str) and o.startswith(b) and t.startswith(b):
        return t + o[len(b):]
    if isinstance(o, list) and isinstance(t, list) and isinstance(b, list) and o[:len(b)] == b and t[:len(b)] == b:
        return t + [x for x in o[len(b):] if x not in t]
    if isinstance(o, list) and isinstance(t, list) and isinstance(b, list) and len(o) == len(t) == len(b):
        return [m(x, y, z, key) for x, y, z in zip(b, o, t)]
    raise Conflict(key)


bad = []
for p in sys.argv[2:]:
    b, o, t = show(base_ref, p), show(':2', p), show(':3', p)
    if t and t.get('merged_into'):
        bad.append((p, '对方已成墓碑')); continue
    try:
        r = m(b, o, t)
    except Conflict as e:
        bad.append((p, '真冲突:' + str(e))); continue
    open(p, 'w', encoding='utf-8').write(json.dumps(r, ensure_ascii=False, indent=2) + '\n')
    subprocess.run(['git', 'add', p])
for x in bad:
    print('\t'.join(x))
print('解决', len(sys.argv) - 2 - len(bad), '未解', len(bad), file=sys.stderr)
