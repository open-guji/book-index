#!/usr/bin/env python3
"""Work 并条后的通用善后（对台账里每个 keeper）：
1. description 里「本書惟《某》一志著錄，別無他證。」之句并条后失实：删去该句，并把新并入著录的来源补进 description.sources；
2. keeper 的撰人与被并者同名同角色、keeper 无 entity_id 而被并者有：补上（台账 dropped_author_entities 里的项）。
原值写入 <batch>/postfix_common-原值.json。用法：postfix_common.py <batch 目录> [--apply]"""
import json, sys, os, glob, re, subprocess
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))
TODAY = '2026-10-25'
SENT = re.compile(r'本書惟《[^》]+》一志著錄，別無他證。')
TAIL = re.compile(r'《[^》]+》[^。《]*——本書之目賴之以存。')
def p(i): return glob.glob(f'{ROOT}/Work/{i[-3]}/{i[-2]}/{i[-1]}/{i}-*.json')[0]
def main():
    d = sys.argv[1]; apply = '--apply' in sys.argv
    L = json.load(open(os.path.join(d, 'merges.json'), encoding='utf-8'))
    orig, n = {}, 0
    for m in L['merges']:
        if m['type'] != 'work': continue
        f = p(m['keeper']); j = json.load(open(f, encoding='utf-8')); changed = []
        if j.get('merged_into'): continue
        desc = j.get('description')
        if isinstance(desc, dict) and SENT.search(desc.get('text') or ''):
            orig.setdefault(j['id'], {})['description'] = json.loads(json.dumps(desc))
            desc['text'] = TAIL.sub('', SENT.sub('', desc['text'])).strip()
            srcs = desc.setdefault('sources', [])
            for e in j.get('indexed_by') or []:
                s = e.get('source')
                if s and s not in srcs and isinstance(srcs, list) and all(isinstance(x, str) for x in srcs):
                    srcs.append(s)
            changed.append('description')
        for de in m.get('dropped_author_entities') or []:
            if not de.get('entity_id'): continue
            for a in j.get('authors') or []:
                if a.get('name') == de['name'] and not a.get('entity_id'):
                    orig.setdefault(j['id'], {}).setdefault('authors', json.loads(json.dumps(j['authors'])))
                    a['entity_id'] = de['entity_id']
                    a['name_basis'] = f'{TODAY} 並條善後：同書重出條 {de["loser"]} 之同名撰人已繫此 entity，今補繫（{m["cluster_id"]}）。'
                    changed.append('authors.entity_id'); break
        if changed:
            rel = os.path.relpath(f, ROOT)
            if not subprocess.run(['git', '-C', ROOT, 'diff', '--quiet', 'origin/main', '--', rel]).returncode:
                a, b, c = [int(x) for x in j.get('revision', '1.0.0').split('.')]   # 本 PR 未动过此 keeper：补一次 patch
                j['revision'] = f'{a}.{b}.{c+1}'; j['revised_at'] = TODAY
            n += 1
            print(m['cluster_id'], m['keeper'], changed)
            if apply: open(f, 'w', encoding='utf-8').write(json.dumps(j, ensure_ascii=False, indent=2) + '\n')
    if apply and orig:
        json.dump(orig, open(os.path.join(d, 'postfix_common-原值.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('keeper 改', n, '(乾跑)' if not apply else '')
if __name__ == '__main__': main()
