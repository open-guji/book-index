# 去重方案部分 5e：Book.contained_in 草稿 Collection ID 修复（2026-10-25）

- 范围：全库 live Book（385,113 个文件全扫）。contained_in 里仍写草稿 Collection ID 的，按 promotions（type=collection）换成正式 ID，换后同 ID 去重。只改 Book。
- 基线（main 045cbd8a06）：contained_in 项共 108,970 个；指向正式 Collection 108,959、草稿 ID 11、找不到的 0、指向 Collection 墓碑 0、同一 Book 内重复 0。Work/Collection 侧无草稿 ID。
- MR-022～024 已在 dedup-confirmed-163/batch-06（leftovers.py）修过，本批是同类全库扫描的余项。
- 结果：11 个 Book 改指 7 个正式 Collection（清單.tsv），原值存 原值.json，revision 补丁位 +1。
- 门禁：check_v2（11 檔）ERROR 0；check-classification 0 项；build_derived --check-only：dangling Book.contained_in 11→0，其余各项与改前一致。
- 复现：`python3 .claude/qa/dedup-part5/5e/fix_contained_in.py [--apply]`

## 补：Book.work_id 仍写草稿 Work ID（2026-10-25 同日发现）
- build_derived 报 dangling Book.work_id 2,364：其中 2,360 个是活 Book，work_id 写的是草稿 Work ID（1exo…，F 道 1,283／G 道 1,075／E 道 2 自动录入批次），正式库无此文件，作品页上看不到这些版本。另 4 个是 Book 墓碑，不改。
- 处理（`fix_work_id.py`）：promotions（type=work）有晉升記錄的 2,353 个改指 production_id；其余 7 个（3 个草稿 Work）在草稿库已是墓碑，merged_into 直接指正式活 Work，改指之。目标全部核为正式库现存、非墓碑。
- 题名核对（work_id-清單.tsv）：2,340 全同；20 个只差异体字（敎／教、陁／陀、註／注），逐条看过无异书。
- 原值 work_id-原值.json；index/books 受影响条目用 dedup-confirmed-163/update_index.py 定点刷新（2,360 条，16 个分片，跳过 0）。
- 门禁：check_v2（2,360 檔）ERROR 0；check-classification 0 项；build_derived --check-only：dangling Book.work_id 2,364→4（余 4 个为 Book 墓碑），index 欄 work_id 漂移 0，self_check 0；check-duplicate-audit 见 PR 描述。
