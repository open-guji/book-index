# 重复记录合并（2026-10-21）

本批是对实际元数据的修改，依据用户提供的 `book-index-duplicate-audit-2026-10-21.zip`，不是仅归档报告。接收基线：`open-guji/book-index@3c544058d4f8af98d4c1c08547c977ef07805657`；原审计快照：`4d6e3219417ac0f2217548b7c241e098c4d39815`。

## 已执行

| 类型 | 合并组 | 留墓碑的被并记录 |
|---|---:|---:|
| 人物 | 19 | 20 |
| Work | 452 | 458 |
| Book | 1,397 | 1,397 |
| 合计 | 1,868 | 1,875 |

所有候选在接收基线上重新读取；439 组 Work 做非管理字段全相等检查，同源 Book 做全字段核对（仅排除身份、Work 指向与管理字段）。涉及父丛编的 Book 额外核对父 Collection 去自身 ID 后的全部字段及非空来源。其余逐组使用审计中的人工证据和当前完整记录裁定，不将 probable、unresolved、retain 当作确认。

- 保留者写并条账，被并者只留 schema 允许的墓碑；旧 ID 仍能解析。
- 改写 Work、Book、Collection、Entity 存储侧引用、分类成员及 promotions 的正式 ID；历史并条账中的旧 ID 不改写。对称关系仍按 ID 大小存储，删除合并造成的自指。
- 来源、著录、资源、卷册与丛编关系合并；完全相同的跨记录内容去重，同一原记录的著录重复次数和顺序保留。冲突字段不盲目覆盖：保留值、被并值、逐组依据和原文件 SHA-256 均见 [merges.json](merges.json)。未重新访问审计所引外部文献。
- 人物别名合并；梅瑴成彙改为梅瑴成，原文「彙編」恢复为责任方式。刘苍条的 CBDB 来源明称西汉，不把该疑似错误外部号和籍贯灌入东汉东平王条，原值记于 `suppressed_imports`。
- 《詩集傳通釋》保留劉瑾与朱熹集传的不同责任层次；《澳門記略》不继承明代同名張汝霖；《夢溪筆談》补回沈括。其余异写保留在题名、异名、原始著录或差异账中，不直接拼接冲突作者。
- 三处互斥分类冲突沿用保留 Work 的原分类，原书目 section 和被移除成员行留存可考；细目见 `classification_decisions`。
- 以 `book-text@c76c233eda8aa3bd46a6689e6e0f17cfe461848f` 的全部 16 份文本索引分片核对：8,791 个文本 ID，无一作为本批被并方。保留《唐摭言》《夢溪筆談》原文本承载 ID。
- 全量构建生成 `_build/`（不入库），仓内 `index/` 只更新本批受影响记录与印章反查表，避免混入基线已缺的 78,437 个无关索引项。机械引用改指不 bump revision；保留者的内容合并按 schema bump，Book 合并用 major。

## 暂留

1. `BOOK-0010`《歐陽文忠公瀧岡阡表》两条 Book 同源，但分别指文章 Work 与书法／碑刻 Work。先裁定作品建模及唯一 work_id，避免仅凭同源把不同知识对象强并。
2. 7 对父 Collection 本身未并：现有 Collection schema 未定义墓碑。548 组相关 Book 已归一，但其两侧 `contained_in` 位置、卷次等全部保留；不得靠删除父丛编破坏旧引用。
3. 审计中仅 probable／unresolved 的候选、明确 retain 的异人异本及无关旧数据不动。原 Work 或人物外部标识的异说记账待考，不把异号擅自宣布为已核定的备用号。

## 验证方法

在仓根运行（`--text-index` 必须是完整、真实的 book-text 文本索引，不接受空目录）：

```sh
python3 scripts/check-duplicate-audit.py --text-index /path/to/book-text/index/texts
python3 scripts/check-classification.py
python3 build/build_derived.py --check-only --text-index /path/to/book-text/index/texts
python3 -m pytest -q tests/test_duplicate_audit_merges.py
```

审数据改动另跑 `schema/check_schema.py --paths` 和 `.claude/qa/check_v2.py --paths -`；路径须是未转义的真实路径（Git 命令加 `-c core.quotePath=false`）。全库测试与 `.claude/qa/verify.py` 须和原基线比对，不能把既有失败描述为本批通过。

基线已知问题：pytest 有 3 项既有失败（Collection 数量常量过时、旧 reindex 口径与现索引不一致、Collection 索引不齐）；verify 有 4,953 项旧并条账缺墓碑、10 项旧墓碑目标异常、18 项既有 V07 关系方向错误。本批不以删除断言、修改校验脚本或大批补造旧墓碑使其转绿。

## 本批运行结果

- 修改的 3,890 条记录通过 schema 校验：ERROR 0、WARN 0、INFO 1（原有长期保留写法）；581 份分类／promotions 文件另验 ERROR 0。
- `check_v2` 覆盖 3,890 条修改记录，ERROR 0、WARN 0。
- 独立引用检查：1,868 个保留者、1,875 个墓碑；活跃源引用、分类成员、升格目标无一仍指向本批被并 ID。8,791 个文本 ID 未受损。
- 全量构建：709,943 条派生 entry，self-check 0、fatal 0。Book.work_id 悬空数由 2,475 降至 2,364；Work.indexed_by.source_bid 悬空数由 142,534 降至 142,095；其余构建悬空项不变。
- 互斥分类与成员排序已修复：200,216 个有分类 Work，问题 0。
- 新增回归测试 6 项全部通过；干净提交上的全库测试为 **321 passed、3 failed、2 skipped**，失败项与原基线完全相同。两项跳过分别需要完整 book-text manifest 与可选 opencc。
- 修复成员排序后，全库 `verify.py` 的完整输出与修改前基线逐字一致；仍因上述既有问题返回 FAIL，没有新增校验项或数量回退。
