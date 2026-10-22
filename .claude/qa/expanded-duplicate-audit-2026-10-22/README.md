# 扩大去重研究检查点（2026-10-22）

本批只提交研究证据、有效裁决索引、验证和续接队列，**原生 Entity/Work/Book/Collection、墓碑及派生索引均未修改**。confirmed 指文献身份已确认，不能等同于已实施或所有执行门槛均通过。旧报告是各批历史记录；当前计数以 checkpoint-validation.json 和 STATUS.json 为准。

## 审阅入口

1. 六路 `report.md` 是恢复批次，`hourly-20261022/report.md` 是本轮31案增量。
2. 僧道旧案只读 `cases-all.json` 一次，其他路读 `cases.json`。随后读各路 `hourly-20261022/cases.json`，按 `supersedes_case_id` 或 `supersedes` 替换旧案，不可重复计数。有效ID列表已写入 checkpoint-validation.json。
3. `classics_titles/hourly-20261022/existing-case-risks.json` 对 JC-001 施加执行暂停：来源摘要混入《归藏》，同一性未推翻，但须修复或标注污染。
4. `first-batch-reconciliation.json` 对照第一批 PR #1213 与已合入 main 的 #1209。

## 本轮与累计

表中顺序均为 **确认 / 分立 / 待核**；待核包括仅候选筛查的旧史部条目，不可宣称已逐案深入研究。

| 分道 | 本轮 | 去重后的累计 |
|---|---:|---:|
| 经部 | 2 / 1 / 4 | 13 / 1 / 6 |
| 史部 | 1 / 0 / 3 | 8 / 3 / 102 |
| 子部 | 3 / 0 / 2 | 25 / 6 / 25 |
| 集部 | 3 / 1 / 1 | 24 / 4 / 10 |
| 本名／字／号 | 2 / 1 / 2 | 15 / 2 / 5 |
| 僧道／帝王／异体人名 | 1 / 1 / 3 | 33 / 6 / 10 |

本轮31案中10案替代旧裁决，其余21案新增；12项确认里5项从旧待核升级、7项为新案。累计118确认、22分立、158待核。实际新增合并0。

主要进展包括：郑玄／康成两种目录、喻樗／喻子材、蔡卞／蔡元度、唐菩提流志称谓重出；《辨中边论颂》《幼科指南》《丛桂堂集验良方》异题；陈宜甫、王若虚、佘翔相关诗集的定点责任者修正方案。明确保留元陈宜甫与清章成义、北魏菩提流支与唐菩提流志等异人。每项证据、反证、卷数或版本风险在相应案件内。

## 验证与执行门槛

- 对恢复批次与增量案件引用的808个不同源文件重算 SHA256，无不符；各分道另存完整引用与关联Book快照。确认组成员无重叠。
- 研究证据基线 `bfaf3cfb3b9b0475fc9fd8d2ce216c291ebc9cca`；本PR建立于最新 main `bc2bb3fcda98a30781b46ddca8b7783dd58a7d97`。比较发现2个Work及2个分类文件在main上变化（6条案件引用），均列入 upstream_drift；任何执行先重读最新原档。
- 已获取 book-text 完整Git目录树 `c76c233eda8aa3bd46a6689e6e0f17cfe461848f`，发现19个拟被并ID实际拥有文本或辑佚资产（经部4、集部15），已逐路径列出。不能在未迁移资产时先写墓碑。
- 目录树检查不等于正文／元数据全引用检查。book-text内部引用、草稿库指向正式库的引用、promotions及官方派生索引检查仍需在实际数据批次完成。
- 本批不涉及原生数据，未运行或宣称通过原生写后schema、分类及builder门槛；这些是后续实际合并必须执行的检查。

## 第一批 PR 的真实状态

[PR #1213](https://github.com/open-guji/book-index/pull/1213) 仍开放未合并。最新main已通过 [PR #1209](https://github.com/open-guji/book-index/pull/1209) 实施重叠批次，merge-tree检出3767处冲突。1876条旧合并关系中591条方向相同，1284条等价但保留ID选择不同，1条关系尚未覆盖：`993avdq3up → 9954l761oh`。这是台账关系比对，不代表字段无损等价已经通过。

**不得把整份旧合并映射再应用到main，不得统一选ours/theirs消冲突。** 先逐字段比较来源、历史、馆藏和资源，核查唯一残留关系及promotions/草稿同步，再决定替代或更新旧PR。本研究PR直接基于main，避免再次带入旧数据提交。

## 续接次序

1. 在最新main核查上述唯一残留Book关系；比较两个批次的无损保留差异，决定#1213如何收束。
2. 选不带文本资产且无来源污染的少量人物组，读取全部真实引用及草稿／文本元数据引用，逐字段合并并保留墓碑、来源和历史。新建小批数据PR，按main现行《正式库并条审查规则》完成全部检查。
3. 集部15个和经部4个文本资产组先准备book-text联动迁移。JC-001、沈钦韩混赵汸、李杲混王好古等污染案单独修复，禁止因名字相同整组硬并。
4. 余下队列继续逐案取证；本轮已裁案件只有新增证据或执行门槛变化时才复核。不要将候选数量当完成量。

## 重跑与快照

`audit_checkpoint.py` 仅做只读哈希、main漂移、同组重叠及文本资产路径检查。以研究基线完整checkout为 `--root`，先fetch最新main，文本库为 `--text-root`：

```bash
python .claude/qa/expanded-duplicate-audit-2026-10-22/audit_checkpoint.py --root /path/to/research-baseline --upstream origin/main --text-root /path/to/book-text --text-ref FETCH_HEAD --output /tmp/checkpoint-validation.json
```

部分历史生成脚本记录旧工作区绝对路径，仅作为可追溯生成逻辑；复跑前需调整路径并使用原基线。两个大型原始扫描快照仅提交等字节gzip：`history_titles/rows.json.gz`、`masters_titles/candidate-snapshots.json.gz`。需要历史脚本输入时先解压为同目录去掉.gz的文件，原字节SHA256见packaging.json。其余证据和快照全部保留。`artifact-manifest.json` 校验交付文件字节（不含自身）。
