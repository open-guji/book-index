# 已确认重复记录合并（2026-10-22）

本批依据六个并行审计分工的确认结论，合并同一人物、同一作品及同一版本的重复记录。只有已确认组进入执行清单；同名异人、原书与注释、不同馆藏/版本及未决组未合并。

| 类型 | 合并组 | 原记录 | 新增墓碑 | 活跃记录净减少 |
|---|---:|---:|---:|---:|
| Entity / people | 19 | 39 | 20 | 20 |
| Work | 452 | 910 | 458 | 458 |
| Book | 1,398 | 2,796 | 1,398 | 1,398 |
| 合计 | 1,869 | 3,745 | 1,876 | 1,876 |

审计原始基线为 `4d6e3219417ac0f2217548b7c241e098c4d39815`，执行前在 `302c4a8e85fc59e951a36feee8725afbe809396a` 复核全部合并记录。机器证据重新计算通过：439 组 Work、1,391 组 Book，0 例外；其余组经过逐案审读和字段裁决；不据此声称历史批次由人工操作。

## 审阅入口

- `merge-map.csv`：逐个被并 ID、保留 ID、题名、路径，便于筛选复查。
- `merge-map.json`：1,876 个旧 ID 到保留 ID 的映射。
- `merge-plan.json.gz`：逐组依据、字段裁决、原文件 SHA256、执行顺序。
- `merge-before.json.gz`：全部 3,745 条原始记录。
- `changed-before.json.gz` / `merge-after.json.gz`：全部 3,897 个源文件的合并前后投影，含旧分类行及相关引用。
- `evidence.json.gz`：审计证据、判准和原始来源引用（包含未决/保留组；执行范围以 merge-plan 为准）。

压缩 JSON 使用标准 gzip，可用 `gzip -dc merge-plan.json.gz` 查看。原始字段即使未进入保留条，也完整留存在前快照；冲突的 CBDB/Wikidata 配号没有被自动提升成可信的备用编号。

## 处理约定

保留原 ID 的最小 `merged_into` 墓碑，不删除记录文件。人物和 Work 继承 `merged_in`；Book 合并 `merged_from`。既有墓碑若指向本批被并条则改为直达最终保留条。实际命中的作者、Work、关联作品、分类成员等存储侧引用同步改指；原始著录、历史 ID 和来源文本不作全局字符串替换。Book 墓碑的 work_id 与保留 Book 一致。

保留馆藏、资源、来源以及完整丛书成员对象。548 组 Book 涉及 7 对重复 Collection；Collection 尚无墓碑约定，本次不合并它们，两个 Collection 关系都保留。111 组 Book 原来一侧引用不存在的旧 Work ID，本次仅按同组有效记录修正，不推广修改其他悬空条目。

《瀧岡阡表》仅合并两个相同来源及馆藏标识的 Book，沿用保留条现有 E3 批次挂接，两个 Work 不合并；E3 不被表述为未经证实的人工裁决。《菜根譚》既有屠隆署名尚待核，不因并条擅删。不同外部 authority 配号、胡訥/唐固存佚等未决事项保留在裁决中。

三个互斥分类冲突另有来源裁决：王定保《唐摭言》保留子部/小说类/文言之属；《古今治平略》按总目取史部/政书类/通制之属；《西吳裏語》按总目取史部/地理类/杂志之属。旧分类行完整归档；同一节点的多项依据并入一行。

按照 schema/common.md，人物/Work 内容合并升 minor，Book 并条升 major；纯跨记录 ID 改写不升 revision。promotions 的历史映射不改写，1,114 个受影响映射的正式目标仍存在并可沿墓碑到达保留条。

## 验证

- 修改记录 schema：3,886 条，ERROR 0 / WARN 0；1 条允许长期保留的旧式 comment INFO。
- `check_v2`：3,886 条，ERROR / WARN / INFO 均为 0。
- 全库分类检查：0 问题。
- 独立写后核验：全部 3,897 个文件与审阅投影一致；1,876 个墓碑形状和目标正确；全库精确 ID 扫描只剩墓碑自身 ID 与明确的历史账，不残留有效引用。
- 分类型独立复核：人物及 13 个人工 Work 组通过；1,398 个 Book 组全部来源/馆藏/资源/著录和历史保留，含 2,783 份原 ai_note。
- 现有 builder 定向测试：7 passed，覆盖 Book 墓碑、merged_into、文本索引、索引格式。
- 使用真实 book-text 文本索引（提交 `c76c233eda8aa3bd46a6689e6e0f17cfe461848f`），文本悬空 0；本批被并 ID 无 book-text 条目。没有修改 book-text 仓库。

索引用官方 `Build` / `build_index` API 比较合并前后派生结果，只写本批产生的变化。44 个主索引文件、1,902 个派生条目更新（Book 1,480 / Entity 20 / Work 402）。另重建 5 个印章反查索引文件，避免重复 Book 仍计入钤印册数；反查漂移为 0。主分支既有索引缺项不在本次批量重建范围；相关基线漂移、前后悬空计数见 build-before/after.json。Book.work_id 悬空从 2,475 降至 2,364；未引入新的悬空目标。

完整 verify 在执行前已有失败：4,953 条历史 merged_in 缺对应墓碑、10 个墓碑目标异常；本批写后复跑计数仍为 4,953 与 10，未新增失败；印章反查漂移已归零，前后完整输出随附。不能将本批报告误读为全库已经零缺陷。

## 重跑

在 PR 最终树运行独立校验：

```bash
python .claude/qa/confirmed-duplicate-audit-2026-10-22/verify_applied_merges.py --root .
python schema/check_schema.py --paths .claude/qa/confirmed-duplicate-audit-2026-10-22/merge-changed-paths.txt
python .claude/qa/check_v2.py --paths @.claude/qa/confirmed-duplicate-audit-2026-10-22/merge-changed-paths.txt --summary
python scripts/check-classification.py .
python .claude/qa/verify.py --base 302c4a8e85fc59e951a36feee8725afbe809396a
```

`apply_confirmed_merges.py --root .` 默认只预演；`--apply` 才写入，并会在任何写入前校验原文件 SHA256。它用于在执行基线复现本批，已合并树上会拒绝重复执行。`rebuild_index.py before|after --root . --text-index /path/to/book-text/index/texts --state-dir /tmp/book-index-merge-state` 可在执行前后保存及比较官方派生索引；禁止传空的文本索引占位。
