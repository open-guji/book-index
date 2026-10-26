# 去重方案部分 5b 第 1 批：总目同版本分条（2026-10-25）

基线（main 3c74b45）：同 Work 同版本名（归一彙／匯、註／注）5,180 组 12,049 个 Book。分档：
抄本稿本等 1,408 组（不同馆抄本是不同书，不并）；宽泛名（清刻本、明刻本、某叢書本）815 组（不并）；有年份刻本 1,544 组。
有年份刻本里再剔：丛书归属不同 608、物理描述不同 190、measure_info 不同 176、分立依據 105、卷数不同 101、题名不同 51、责任者不同 1；
余 312 组中故宫／国图「一部一条」藏本记录 277 组（是否并为一个版本待用户定口径，本批不碰），总目来源 35 组，再剔地望前缀不同的族谱 5 组 → 30 组候选（候選.tsv）。
独立子 agent 逐条核（逐條核.tsv）：SAME 27、UNSURE 3（均为故宫藏本记录，按上条不并）。

结果：27 组，keeper＝馆藏多、信息全者，sources／indexed_by／provenance 取并集，27 个被并者留墓碑；promotions 改指；草稿库 1 处 merged_into 改指 keeper（book-index-draft 同名分支 PR）。
门禁（与 5a 合并台账审）：audit T/L/P/R/D 全 0；check_v2 0；check-classification 0；check_promo_dup 0；check-duplicate-audit PASS；index/books 定点刷新。

注：当时脚本实际漏并 sources／indexed_by／provenance，已在 ../../backfill/ 回补。
