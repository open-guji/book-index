#!/usr/bin/env python3
"""新-无责任者余 批次的 README 与互斥分类登记。用法：mkreadme.py <批次目录> <标题>"""
import json, subprocess, sys, pathlib
d = pathlib.Path(sys.argv[1]); L = json.load(open(d / 'merges.json'))
def rec(m, i):
    p = [x['path'] for x in m['preconditions'] if x['id'] == i][0]
    r = json.loads(subprocess.check_output(['git', 'show', 'origin/main:' + p]))
    a = '/'.join(str(x.get('name')) for x in (r.get('authors') or [])[:2]) or '無責任者'
    return f"{r.get('title')}（{a}）"
rows, cls = [], []
for m in L['merges']:
    nconf = sum(len(x['fields']) for x in m['retained_alternatives'])
    rows.append(f"| {m['cluster_id']} | {rec(m, m['keeper'])} | {len(m['losers'])} | {nconf} | {len(m['classification_decisions'])} |")
    for n in m['classification_decisions']:
        cls.append(f"{m['cluster_id']}\t{m['keeper']}\t{n}")
(d / '分类互斥登记.tsv').write_text('\n'.join(cls) + ('\n' if cls else ''), encoding='utf-8')
(d / 'README.md').write_text(f"""# 去重细拆单元 新-无责任者余：{sys.argv[2]}

基线 main `{L['base']}`。口径：`ai-team/domain/目录与资源/设计/2026-10-正式库全面去重方案/部分4-Work层无责任者与弱证据.md`（4a-B 节）、`细拆-20261026/README.md`、00 文件 Work 节 A 档、`.claude/qa/正式库并条审查规则.md`。

**规则**（`mkbatch_nr.py`）：细拆单元「新-无责任者余」是普查同题组里、非叢書子目、非譜志、至少一侧无责任者的组（一侧有一侧无、全无两类）。每对由子 agent 逐条读 Work／Book 著录判定，只收「同书」且卷数相合、证据属严格清单者：同源（同一源记录、同一目录同一条、同一叢書同一子目）、版本馆藏（同版本名且馆藏重合）、原文自证、辑佚同本、题含作者。脚本再加严：有责任者一侧含編／輯類责任者（证据非辑佚同本）、无责任者一侧有缺字责任者、两侧卷数不合、一条无责任者 Work 判与多处同书、全无组传递不一致，一律改存疑不并。一侧有一侧无：无责任者并入有责任者；全无：并入挂 Book 最多的一条。分立／存疑登记在 `.claude/qa/dedup-judged/新-无责任者余.tsv`。

工具：`apply_4.py`（`../dedup-part4/`，包装 mergework：著录并入、Book.work_id 与引用改指、分类成员改指，被并者留墓碑、keeper 记 merged_in／merged_from）、`postfix_common.py`、`fix_intra.py`、`update_index.py`、`fix_draft.py`。冲突字段保留 keeper 原值，被并值入台账 `retained_alternatives`；被并者原 ai_note／description 存 `loser_original_notes`；互斥分类登记见 `分类互斥登记.tsv`。

| 组 | 保留 | 并入条数 | 保留冲突字段数 | 分类互斥处理 |
|---|---|---:|---:|---:|
""" + '\n'.join(rows) + """

验证：audit-merge-ledger（--draft 草稿库已同步）T/L/P/R/D 全 0；check_v2、check-classification、check_promo_dup、check-duplicate-audit、build_derived --check-only 全 0。抽检见 `抽检.md`。回滚：revert 本 PR。
""", encoding='utf-8')
