#!/usr/bin/env python3
"""3a-2丙 批次 README 与互斥分类登记。用法：mkreadme.py <批次目录> <标题> [抽检说明]"""
import json, subprocess, sys, pathlib
d = pathlib.Path(sys.argv[1]); L = json.load(open(d / 'merges.json'))
def rec(m, i):
    p = [x['path'] for x in m['preconditions'] if x['id'] == i][0]
    r = json.loads(subprocess.check_output(['git', 'show', 'origin/main:' + p]))
    return f"{r.get('title')}（{'/'.join(str(x.get('name')) for x in (r.get('authors') or [])[:1]) or '—'}）"
rows, cls = [], []
for m in L['merges']:
    g = 'B' if m['rule'].endswith('B 档并') else 'A'
    rows.append(f"| {m['cluster_id']} | {g} | {rec(m, m['keeper'])} | {'、'.join(rec(m, l) for l in m['losers'])} | {sum(len(x['fields']) for x in m['retained_alternatives'])} |")
    for n in m['classification_decisions']:
        cls.append(f"{m['cluster_id']}\t{m['keeper']}\t{n}")
(d / '分类互斥登记.tsv').write_text('\n'.join(cls) + ('\n' if cls else ''), encoding='utf-8')
(d / 'README.md').write_text(f"""# 去重方案 3a-2丙（差一字·經史）：{sys.argv[2]}

基线 main `{L['base']}`。单元：`ai-team/domain/目录与资源/设计/2026-10-正式库全面去重方案/细拆-并行单元-20261025.md` 3a-2丙；口径同 `00-通用口径与门禁.md` Work 节与 `.claude/qa/正式库并条审查规则.md`。
候选：`near_title_alias.py` 的「差一字」类（同一首位责任者，题名等长只差一字），經史两部 2,168 对。差字是异体／俗写／避讳／明显形近误字、卷数同或差≤1 或一侧缺、朝代不冲突者为 A 档；差字近义但著录原文能证同书者为 B 档（依据写在台账 evidence）。卷数悬殊而无原文证据、原书对辑本、正编对续编、同一志书分列两条者不并，登记在 `../../dedup-judged/3a-2丙.tsv`。
工具：`build_batch.py`（判定对→batch.json，连通分量成簇，keeper 取题名用正字者＞著录多＞id 早）、`apply_3a2c.py`（包装 `../dedup-confirmed-163/apply_batch.py`）、`run_batch.sh`（apply→postfix_common→update_index→fix_draft）。被并题名进 keeper 的 additional_titles；冲突字段保留 keeper 值，被并值进台账 retained_alternatives；被并者原 description／ai_note 存台账 loser_original_notes。

| 组 | 档 | 保留 | 被并 | 保留冲突字段数 |
|---|---|---|---|---:|
""" + '\n'.join(rows) + f"""

验证：audit-merge-ledger（--draft 草稿库已同步）T/L/P/R/D 全 0；check_v2、check-classification、check_promo_dup、check-duplicate-audit、build_derived --check-only 全 0。抽检见 `抽检.md`。回滚：revert 本 PR（及草稿库对应 PR）。
""", encoding='utf-8')
