#!/usr/bin/env python3
"""新-同姓异名余 批次的 README 与互斥分类登记。用法：mkreadme.py <批次目录> <标题>"""
import json, subprocess, sys, pathlib
d = pathlib.Path(sys.argv[1]); L = json.load(open(d / 'merges.json'))
def rec(m, i):
    p = [x['path'] for x in m['preconditions'] if x['id'] == i][0]
    r = json.loads(subprocess.check_output(['git', 'show', 'origin/main:' + p]))
    a = '/'.join(str(x.get('name')) for x in (r.get('authors') or [])[:2]) or '—'
    return f"{r.get('title')}（{a}）"
rows, cls = [], []
for m in L['merges']:
    nconf = sum(len(x['fields']) for x in m['retained_alternatives'])
    rows.append(f"| {m['cluster_id']} | {rec(m, m['keeper'])} | {'、'.join(rec(m, l) for l in m['losers'])} | {nconf} | {len(m['classification_decisions'])} |")
    for n in m['classification_decisions']:
        cls.append(f"{m['cluster_id']}\t{m['keeper']}\t{n}")
(d / '分类互斥登记.tsv').write_text('\n'.join(cls) + ('\n' if cls else ''), encoding='utf-8')
(d / 'README.md').write_text(f"""# 去重第二轮细拆单元 新-同姓异名余：{sys.argv[2]}

基线 main `{L['base']}`。口径：`ai-team/domain/目录与资源/设计/2026-10-正式库全面去重方案/00-通用口径与门禁.md` Work 节 B 档、`细拆-20261026/README.md` 新-同姓异名余（未判「不同」组中同姓异名／别名可证／名互含，非子目非譜志；3b-0 口径：名／字／號异写、形近讹字、署名残缺可并，同姓异人登记 C），`.claude/qa/正式库并条审查规则.md`。
候选由 `cands.py`（改自 dedup-3b0，加标科举卷）对本单元 644 组两两配对生成 832 对，逐对人工判定，见 `判定.tsv`（S 同人并：名／字／號、避諱、异体、形近讹字、倒文、署名残缺或占位名；S2 原文同列并；D 存疑；X 分立）；判同人的依据：Entity 主名／alt_names、同一 Entity、《总目》等原文、CBDB（只作证据，不入库），或同题同卷数同朝代而署名仅一字形近／倒文／脱衍。成簇、keeper 由 `mkbatch.py`（规范名取 判定.tsv「规范名」栏：本名、正字；簇内卷数极差＞1 的不并），另经独立核验，见 `抽检.md`。
工具：`apply_txy.py`（包 `../dedup-confirmed-163/apply_batch.py`：著录并入、关系与引用改指、分类成员改指，被并者留墓碑、keeper 记 merged_in／merged_from）、`../dedup-confirmed-163/postfix_common.py`、`postfix_txy.py`（keeper 撰人补繫 entity；被并条的署名异写形补进该 Entity 的 alt_names，type 取 訛名／異體／避諱／別稱，泛称、误切、省称不补；原值存 `postfix_txy-原值.json`）、`update_index.py`、`fix_draft.py`（草稿库同步，另开草稿库 PR）。

冲突字段（两边都有且不同）一律保留 keeper 原值，被并值写入台账 `retained_alternatives`；被并者原 description／ai_note 存台账 `loser_original_notes`；互斥分类下被并者与 keeper 分属不同节点的，保留 keeper 的节点，被并者的节点登记在 `分类互斥登记.tsv`。判为分立／存疑的对登记在 `../dedup-judged/新-同姓异名余.tsv`。

| 组 | 保留 | 被并 | 保留冲突字段数 | 分类互斥处理 |
|---|---|---|---:|---:|
""" + '\n'.join(rows) + """

验证：audit-merge-ledger（--draft 草稿库已同步）T/L/P/R 全 0；check_v2、check-classification、check_promo_dup、check-duplicate-audit、build_derived --check-only 全 0。抽检见 `抽检.md`。回滚：revert 本 PR（及草稿库对应 PR）。
""", encoding='utf-8')
