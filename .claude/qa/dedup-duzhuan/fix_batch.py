#!/usr/bin/env python3
"""第二轮抽检后修正已写批次：撤回他人酬赠/评论/唱和/条约类子目；劉鹹炘→劉咸炘；張英 明→清。
    python3 fix_batch.py BATCH_DIR"""
import json, os, re, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import jio  # noqa: E402
REVERT = re.compile(r'酬贈|投贈|贈答|評論|逸事|^附後$|條款|條約|倡和|唱和')
b = sys.argv[1]; L = json.load(open(os.path.join(b, 'applied.json'))); keep = []; nrev = nfix = 0
for x in L:
    d, fmt = jio.load(x['path'])
    if REVERT.search(d['title']):
        subprocess.run(['git', '-C', jio.ROOT, 'checkout', 'origin/main', '--', x['path']], check=True); nrev += 1; continue
    a = d['authors'][0]; ch = False
    if a['name'] == '劉鹹炘':
        a['original_name'] = a['name']; a['name'] = '劉咸炘'
        a['name_basis'] = '叢書著錄「劉鹹炘」係誤繁化，正作劉咸炘'; ch = True
    if a['name'] == '張英' and a.get('dynasty') == '明':
        a['dynasty'] = '清'; a['dynasty_basis'] = '叢書 authors 誤作明；叢書著錄 summary 題「清張英撰」'; ch = True
    if ch:
        d['ai_note'] = re.sub(r'撰者劉鹹炘', '撰者劉咸炘', d['ai_note']).replace('撰者張英（明）', '撰者張英（清）')
        jio.save(x['path'], d, fmt); x['author'] = a; nfix += 1
    keep.append(x)
json.dump(keep, open(os.path.join(b, 'applied.json'), 'w'), ensure_ascii=False, indent=1)
print(b, '撤回', nrev, '修正', nfix, '余', len(keep))
