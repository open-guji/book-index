#!/usr/bin/env python3
"""GUJI-124：朝代字「魏」被拆出姓氏的残留。
 - 作者「元曠」(魏) → 魏元曠（清，entity hixi5h83ndqa）
 - 作者「胡思敬」朝代「魏」→ 清（entity hixhd2h9bdkp，缺则补）
只动 authors 里命中的行；revision 小版本 +1，ai_note 追加一行。默认干跑，--apply 写入。"""
import json, glob, sys
APPLY = '--apply' in sys.argv
E_WEI, E_HU = 'hixi5h83ndqa', 'hixhd2h9bdkp'
NOTE = '\nGUJI-124：作者朝代字「魏」曾被拆出姓氏，已还原（元曠→魏元曠；胡思敬朝代魏→清），原值：{}'
def bump(r):
    p = (r or '1.0.0').split('.')
    p[-1] = str(int(p[-1]) + 1); return '.'.join(p)
n = {}
for t in ('Book', 'Work'):
    for f in sorted(glob.glob(f'{t}/*/*/*/*.json')):
        raw = open(f, encoding='utf-8').read()
        d = json.loads(raw); olds = []
        for a in d.get('authors') or []:
            if not isinstance(a, dict): continue
            if a.get('name') == '元曠' and a.get('dynasty') == '魏':
                olds.append('元曠/魏'); a['name'] = '魏元曠'; a['dynasty'] = '清'; a['entity_id'] = E_WEI
            elif a.get('name') == '胡思敬' and a.get('dynasty') == '魏' and a.get('entity_id') in (None, E_HU):
                olds.append('胡思敬/魏'); a['dynasty'] = '清'; a['entity_id'] = E_HU
        if not olds: continue
        d['ai_note'] = (d.get('ai_note') or '') + NOTE.format('、'.join(sorted(set(olds))))
        d['revision'] = bump(d.get('revision'))
        n[t] = n.get(t, 0) + 1
        if APPLY:
            ind = 2 if raw.startswith('{\n') else None
            open(f, 'w', encoding='utf-8').write(json.dumps(d, ensure_ascii=False, indent=ind) + ('\n' if raw.endswith('\n') else ''))
print(n)
