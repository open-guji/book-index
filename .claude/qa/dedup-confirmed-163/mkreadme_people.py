#!/usr/bin/env python3
"""人物批的 README：朝代复核表。用法：mkreadme_people.py <batch 目录> <标题>"""
import json, subprocess, sys, pathlib
d = pathlib.Path(sys.argv[1]); L = json.load(open(d / 'merges.json'))
def dyn(m, i):
    p = [x['path'] for x in m['preconditions'] if x['id'] == i][0]
    r = json.loads(subprocess.check_output(['git', 'show', 'origin/main:' + p]))
    return f"{r.get('primary_name')}（{r.get('dynasty') or '—'}）"
rows = [f"| {m['cluster_id']} | {dyn(m, m['keeper'])} | {'、'.join(dyn(m, l) for l in m['losers'])} |" for m in L['merges']]
(d / 'README.md').write_text(f"""# 去重确认案实施：{sys.argv[2]}

基线 main `{L['base']}`。依据：`/mnt/project-files/总目/去重研究/expanded-duplicate-audit-2026-10-22/` 确认案，口径见 `.claude/qa/正式库并条审查规则.md`。工具 `../apply_batch.py`（复用 entity_merge）、`../update_index.py`；台账 `merges.json`。

朝代复核（朝代不同的组，证据见案内：僧人跨代、避讳、前缀等）：

| 案 | 保留 | 被并 |
|---|---|---|
""" + '\n'.join(rows) + """

验证：audit-merge-ledger（--draft）T/L/P/R/D 全 0；check_v2、check-classification、check_promo_dup 全 0。只改作者 entity_id 与人物档。
""", encoding='utf-8')
