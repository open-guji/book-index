# 去重方案部分 5e：Book.contained_in 草稿 Collection ID 修复（2026-10-25）

- 范围：全库 live Book（385,113 个文件全扫）。contained_in 里仍写草稿 Collection ID 的，按 promotions（type=collection）换成正式 ID，换后同 ID 去重。只改 Book。
- 基线（main 045cbd8a06）：contained_in 项共 108,970 个；指向正式 Collection 108,959、草稿 ID 11、找不到的 0、指向 Collection 墓碑 0、同一 Book 内重复 0。Work/Collection 侧无草稿 ID。
- MR-022～024 已在 dedup-confirmed-163/batch-06（leftovers.py）修过，本批是同类全库扫描的余项。
- 结果：11 个 Book 改指 7 个正式 Collection（清單.tsv），原值存 原值.json，revision 补丁位 +1。
- 门禁：check_v2（11 檔）ERROR 0；check-classification 0 项；build_derived --check-only：dangling Book.contained_in 11→0，其余各项与改前一致。
- 复现：`python3 .claude/qa/dedup-part5/5e/fix_contained_in.py [--apply]`
