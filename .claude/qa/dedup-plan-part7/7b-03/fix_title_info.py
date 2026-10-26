#!/usr/bin/env python3
"""merged_in／merged_from 項之 title_info 寫成了陣列（schema 要 string）：以「；」連成一串，空陣列則刪該鍵。
來源是 dedup-confirmed-163/apply_batch.py 舊寫法（已一併改為寫字串）。乾跑默認，--apply 才寫；--max N 一批至多改 N 檔（默認 500）。
    python3 .claude/qa/dedup-plan-part7/7b-03/fix_title_info.py [--apply] [--max 500]
"""
import json, os, subprocess, sys
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../..'))
apply = '--apply' in sys.argv
cap = int(sys.argv[sys.argv.index('--max') + 1]) if '--max' in sys.argv else 500
files = subprocess.run(['rg', '-l', '"title_info": \\[', 'Work', 'Book', 'Entity', 'Collection'], cwd=ROOT,
                       capture_output=True, text=True).stdout.split()
print('候选檔', len(files))
done = 0
for rel in sorted(files):
    p = os.path.join(ROOT, rel)
    raw = open(p, encoding='utf-8').read()
    d = json.loads(raw)
    n = 0
    for k in ('merged_in', 'merged_from'):
        for m in d.get(k) or []:
            if isinstance(m, dict) and isinstance(m.get('title_info'), list):
                v = '；'.join(x for x in m['title_info'] if isinstance(x, str) and x)
                if v:
                    m['title_info'] = v
                else:
                    del m['title_info']
                n += 1
    if not n:
        continue
    nl = '\n' if raw.endswith('\n') else ''
    if json.dumps(json.loads(raw), ensure_ascii=False, indent=2) + nl != raw:
        print('跳过(格式不可无损往返):', rel)
        continue
    if done >= cap:
        break
    done += 1
    if apply:
        open(p, 'w', encoding='utf-8').write(json.dumps(d, ensure_ascii=False, indent=2) + nl)
print('%s 文件 %d' % ('已写' if apply else '乾跑', done))
