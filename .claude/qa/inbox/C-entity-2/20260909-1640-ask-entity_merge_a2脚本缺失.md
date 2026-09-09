# ask：`entity_merge_a2.py` / `entity_merge_a2_report.json` 不在 overview main 上

任务书 §八「下一道要读什么」第 3 条点名的
`overview/scripts/qa/entity_merge_a2.py` 与
`overview/scripts/qa/entity_merge_a2_report.json`，本道 clone `overview`
main（commit `78c64a4`）后**实测都不存在**：

```
find overview/scripts/qa -iname "*entity_merge_a2*"   # 无结果
```

`overview/scripts/qa/reports/20260909/` 目录下只有：
`batch4-A1A2执行清单与批次方案.md`、`entity_a1a2a3.json`、
`entity_dup_triage.json`、`entity_206_profile.json`、
`qa_entity_draft_full.json`、`qa_entity_official_full.json`——
均无脚本与本批专属 report。推测前一道这两份档只在其本地工作区生成，
未曾提交（其环境对 `book-index-draft` 读写全封，但当时对 `overview`
应仍可写；本道未深究是否也一并卡住，只如实记录"main 上没有"这一事实）。

## 本道怎么绕过的

没有重放脚本，改用**已落 main 的 production 侧数据反推**：
`book-index` 的 77 条 Entity 的 `merge_history` 里 `reason` 含"併條"字样的
条目，直接给出 `merged_from`（draft id）与该条目自身 id（production id）
的完整映射，77 条，与任务书数字一致。这份映射比脚本重放更可信——它是
**已过四道闸、已在 main 上的事实**，不必再验证脚本本身有没有 bug。

## 是否需要协调者处理

不必特别处理，仅记录在案。若日后要复核"当初脚本判定的 77 条是否等于
production 侧实际记录的 77 条"，可用本单这条反推法交叉核对（结果应恒等，
因为 production 侧数据本身就是那份脚本跑出来的）。
