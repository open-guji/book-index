# 当前续接计划（2026-10-22）

替代研究PR #1215已打开，旧#1213已关闭。最新权威入口：README.md当前状态、STATUS.json、current-rollup.json及六路astra-review-20261022/report.md。六个Astra/high子会话已完成本轮13案复核；当前无待续跑的旧子会话。累计119确认/22分立/157待核，实际新增数据合并0。旧checkpoint-validation.json是上一批源证据校验，不包含Astra新案替代计数。

下一轮从远端研究分支codex/expanded-duplicate-research-20261022恢复检查点，fetch最新main，避免重复计数和重提main已完成数据。所有子会话使用gpt-6-astra、reasoning_effort=high、fork_turns=none并提供充分上下文；小时任务已同步。

1. 从两路人物候选方案挑最小批次，读最新原档，完成正式库所有型别引用、promotions、草稿库及book-text引用扫描，生成逐字段无损台账，再动数据。不得把已知1处引用当全库只有1处。
2. 先读史部H-C010/H-C082两份已知漂移正文。子部MR-046责任者污染、MR-050串案说明已定位；集部此山/敬业堂与经部左传补注保持待核与污染修复边界。
3. 19个旧拟并ID带文本资产，先做book-text联动迁移。维持JC-001污染执行暂停及JC-007组内关联改指自边风险暂停以及瀧岡阡表BOOK-0010明确defer。
4. 实际数据批次按main现行正式库并条审查规则跑台账审计、schema、分类和官方builder；分批PR，不自动合main。

资料库大且是partial clone，避免六路同时全库git grep或逐blob懒取；优先共享固定main树与旧原档blob双散列证明，确有漂移才定点读。旧脚本含历史绝对路径者仅为可追溯逻辑，复跑先对齐路径。资料记录中的claimed确认仅指身份，不代表所有执行门槛通过。
