# 去重方案部分 5：故宫／国图同版本分册并为一个 Book（2026-10-28，main d8c48fa810b）

口径：用户 2026-10-28 定「Book＝版本，不是册；分册绝不拆，同版多册合一 Book」（ai-team 去重方案 00-通用口径 第七节）。此前「故宫一号一条不并」作废。
范围：同 Work＋同版本名＋同为故宫（ai_note 为空）或国图重配（精确年份）记录的 Book，共 633 组（含 5b-研「不并·故宫一部一条」档）。国图泛年代（「清[1644-1911]」）62 组仍按 5c 不并。

分档：
- T1 450 组：版本名具体（含刊刻者／堂号），题名、责任者、行数、版框高（差≤1cm）无矛盾 → 直接并。
- T2 183 组：泛称版本名（明刊本、清抄本等）、仅有年份无刊者、或有疑点 → 5 个子 agent 逐组读摘要判簇，可并 141 簇；29 组有疑问的 Book 不并，登记 不並登記.tsv。
结果：591 簇、被并 821 个 Book（永樂大典 54 册合一 Book 等）。脚本 ../merge_volumes.py：各号 provenance 并集（被并者「存缺」写入对应条 notes）；resources 并集，每条加 note「故宮藏本：<索书号>」／「國圖藏本：fid …」；被并者 physical_description／metadata 等记入 merges.json 的 loser_original_notes；被并者留墓碑；指向被并者的 related_books 改指 keeper（并按 V07 搬到小 id 一侧）。
抽检（独立子 agent 读并前全文）：T1 45 簇 SAME 45；T2 43 簇 SAME 43；异质 0。唯一提醒：5F-NLC-400 国图两条责任者著录不同（许慎、高诱撰／刘安撰），keeper 仅留首条，另一条在台账；5F-GG-563 的 commons 资源无索书号可标，文件名已含册号。
门禁：check_v2 ERROR 0；check-classification 0；audit-merge-ledger T/L/P/R/D 全 0；check_promo_dup 0；check-duplicate-audit PASS（book-text 无引用）。草稿库无引用。
