#!/usr/bin/env python3
"""子目-甲2 批次的 README 与互斥分类登记。用法：mkreadme.py <批次目录> <标题>"""
import json, subprocess, sys, pathlib
d = pathlib.Path(sys.argv[1]); L = json.load(open(d / 'merges.json'))
def rec(m, i):
    p = [x['path'] for x in m['preconditions'] if x['id'] == i][0]
    r = json.loads(subprocess.check_output(['git', 'show', 'origin/main:' + p]))
    a = '/'.join(str(x.get('name')) for x in (r.get('authors') or [])[:2]) or '無責任者'
    return f"{r.get('title')}（{a}）"
B = {g['cluster_id']: g for g in json.load(open(d / 'batch.json'))['groups']}
rows, cls = [], []
for m in L['merges']:
    nconf = sum(len(x['fields']) for x in m['retained_alternatives'])
    cs = B[m['cluster_id']]['evidence'].split('》不同版次')[0].replace('同名丛书《', '')
    rows.append(f"| {m['cluster_id']} | {rec(m, m['keeper'])} | {cs} | {len(m['losers'])} | {nconf} | {len(m['classification_decisions'])} |")
    for n in m['classification_decisions']:
        cls.append(f"{m['cluster_id']}\t{m['keeper']}\t{n}")
(d / '分类互斥登记.tsv').write_text('\n'.join(cls) + ('\n' if cls else ''), encoding='utf-8')
(d / 'README.md').write_text(f"""# 去重细拆单元子目-甲2：{sys.argv[2]}

基线 main `{L['base']}`。口径：`ai-team/domain/目录与资源/设计/2026-10-正式库全面去重方案/细拆-并行单元-20261025.md`（子目-甲2 行）、00 文件 Work 节 A 档、`.claude/qa/正式库并条审查规则.md`。

**规则**（候选脚本 `../cand.py`）：叢書线（GUJI-526）按《總目》丛书版本记录各建一条子目 Work，同一丛书几个版次里的同一子目被建成多条。同题组（`scripts/dedup-census.py` 口径：去括注、异体归一）里，`ai_note`「所屬叢書記錄 X（丛书题名）」的丛书题名去卷数、种数后相同、而丛书记录不同的子目 Work 互并。另须：Book 所属 Collection 的首位撰者一致（不一致的丛书撰者写法不同簇另行逐条核，不在本批）；簇内首位责任者不矛盾（至多一种）、朝代不矛盾、卷数差≤1 或缺；同一丛书记录内同题两条的簇（疑异篇）、单字泛称题名（首／序／跋等，多为卷首卷末）不并，登记于 `../../dedup-judged/子目-甲2.tsv`；**跳过** 4a-α 清单（`../dedup-part4/候选/4a-alpha-*.json`）里的 Work，那些簇由 4a-α 并入同作者单行本。keeper：有责任者＞Book 多＞有非叢書部著录＞id 早。

工具：`apply_jia2.py`（包装 `../dedup-confirmed-163/apply_batch.py`，复用 mergework：著录并入、Book.work_id 与引用改指、分类成员改指，被并者留墓碑、keeper 记 merged_in／merged_from）、`postfix_common.py`、`update_index.py`、`fix_draft.py`。冲突字段保留 keeper 原值，被并值入台账 `retained_alternatives`；被并者原 ai_note／description 存 `loser_original_notes`；互斥分类登记见 `分类互斥登记.tsv`。

| 组 | 保留 | 丛书 | 并入条数 | 保留冲突字段数 | 分类互斥处理 |
|---|---|---|---:|---:|---:|
""" + '\n'.join(rows) + """

验证：audit-merge-ledger（--draft 草稿库已同步）T/L/P/R/D 全 0；check_v2、check-classification、check_promo_dup、check-duplicate-audit、build_derived --check-only 全 0。抽检见 `抽检.md`。回滚：revert 本 PR。
""", encoding='utf-8')
