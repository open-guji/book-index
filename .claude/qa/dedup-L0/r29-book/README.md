# L0 第二十九轮：同叢書 Book 卷数不合

2026-11-15，L0 去重车道。账本 `merges.json`：87 组，并掉 87 条 Book。

## 候选
第二十八轮合入后，在 main 上重扫「同一 Work、同一叢書 Collection 下两条以上 Book」，取卷数归一后仍不相容的组（主卷数不同 253、附卷不成前缀 97），去掉两条独立馆藏、节录残缺字样的，余 320 组。

## 复核
两道独立复核，两道皆「同」才并，共 83 组。判同的依据是卷数差异能用记法解释：附卷名目不同（補遺／拾遺、續／續編）、首末卷与附卷计不计入、合计记法（一卷＋外编一卷＝二卷）、脱字衍字。卷数取复核所定较详者，原卷数记入 ai_note。
另 4 组三条中两条是重出、第三条另是一本（两道都点出同一对），只并那一对。
主卷数真不同、刻次或印次不同、增补本、残本、不分卷对多卷一律不并（约 230 组）。

## 关卡
check_v2、check_schema 0 ERROR；audit-merge-ledger T/L/P/R/D 0 ERROR；check-classification 0；check_promo_dup 0；check-duplicate-audit PASS；census --strict 墓碑链 0、引用墓碑 0。promotions 改指 82 个文件。草稿仓无指针。
