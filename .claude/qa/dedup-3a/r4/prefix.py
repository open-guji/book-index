#!/usr/bin/env python3
"""3a 第四轮并条前清理：d59f27y30k5e《集議孝經》（荀昶）误挂的丁志「東陽太守袁宏」著录。
该节属袁宏《集議孝經》，袁宏条 d59f27ycowzl 已有同一丁志著录，故从荀昶条删去，并在 ai_note 记一笔。"""
import glob, json, os
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))
p = glob.glob(os.path.join(ROOT, 'Work', 'k', '5', 'e', 'd59f27y30k5e-*.json'))[0]
d = json.load(open(p, encoding='utf-8'))
ib = d['indexed_by']
keep = [x for x in ib if not ((x.get('summary') or '').startswith('東陽太守袁宏') and '丁國鈞' in (x.get('source') or ''))]
if len(keep) == len(ib) - 1:
    d['indexed_by'] = keep
    d['ai_note'] = ((d.get('ai_note') or '') + '\n\n3a第四轮（2026-10-26）：删去误挂的補晉書藝文志（丁國鈞）「東陽太守袁宏」一节——该节属袁宏《集議孝經》，已见于 d59f27ycowzl。').strip()
    open(p, 'w', encoding='utf-8').write(json.dumps(d, ensure_ascii=False, indent=2) + '\n')
    print('prefix: 删 1 节')
else:
    print('prefix: 未匹配，跳过（%d→%d）' % (len(ib), len(keep)))
