#!/usr/bin/env python3
"""部分 4 批次的 README 与互斥分类登记。用法：mkreadme.py <批次目录> <标题>"""
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
(d / 'README.md').write_text(f"""# 去重方案部分 4：{sys.argv[2]}

基线 main `{L['base']}`。口径：`ai-team/domain/目录与资源/设计/2026-10-正式库全面去重方案/部分4-Work层无责任者与弱证据.md`（4a-α 修订节）、00 文件 Work 节 A 档、`.claude/qa/正式库并条审查规则.md`。

**4a-α 规则**（候选脚本 `../cand_alpha.py`）：同题组（`scripts/dedup-census.py` 口径：去括注、异体归一）里，无责任者一侧是叢書线（GUJI-526）新建的叢書子目 Work——《總目》叢書部獨撰類著录子目时不重复撰人，所以「無責任者」只是著录省略；其 Book 所属 Collection 的首位撰者（角色撰／撰輯／著等）与组内**唯一**一条有责任者 Work 的首位责任者同名、朝代相容；卷数相同、一侧缺或差≤1；单行本自身卷数不齐（差>1）的组跳过；同一叢書内有两条同题子目的组跳过（疑异篇）；有责任者多于 1 条的组留给 3a。子目 Work 并入单行本 Work，子目 Book 随之改挂。

工具：`apply_4.py`（包装 `../dedup-confirmed-163/apply_batch.py`，复用 mergework：著录并入、Book.work_id 与引用改指、分类成员改指，被并者留墓碑、keeper 记 merged_in／merged_from）、`postfix_common.py`、`update_index.py`、`fix_draft.py`。冲突字段保留 keeper 原值，被并值入台账 `retained_alternatives`；被并者原 ai_note／description 存 `loser_original_notes`；互斥分类登记见 `分类互斥登记.tsv`。

善后提示：并后 keeper 下可能同时有 F 道「某某叢書本」Book 与叢書线子目 Book（同丛书不同著录），属部分 5 同 Work 同版本 Book，留给部分 5。

| 组 | 保留（单行本） | 并入子目条数 | 保留冲突字段数 | 分类互斥处理 |
|---|---|---:|---:|---:|
""" + '\n'.join(rows) + """

验证：audit-merge-ledger（--draft 草稿库已同步）T/L/P/R/D 全 0；check_v2、check-classification、check_promo_dup、check-duplicate-audit、build_derived --check-only 全 0。抽检见 `抽检.md`。回滚：revert 本 PR。
""", encoding='utf-8')
