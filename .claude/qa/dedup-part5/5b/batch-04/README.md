# 去重方案 5b-乙 第 4 批起：文淵閣／摛藻堂子目重复 Book（2026-10-26）

来由：book-index#1357（部分 6）把总目叢書线的文淵閣、摛藻堂 Collection 并入手建 Collection 后，同一 Work 在
`8rlb6yi1ecqo`（欽定四庫全書·文淵閣本）下挂两个以上 Book 2,486 个、`8rlb6yk66qdc`（摛藻堂薈要）下 297 个。两套都是今藏台北故宫的唯一写本，
同 Work 下的手建 Book（故宫「故庫…」号、影像）与总目子目 Book（卷数、责任者、总目 instance）记的是同一部书。

- 从 main（#1357 合入后）重算：2,783 个 Work，其中手建 1 对总目 1 的 2,690 对；其余 93 组（总目对总目 71、手建多条等）不机械并，登记于 `不並登記.tsv`。
- 核对：题名归一后不同的 328 对全部、题名相同的随机 120 对，由独立子 agent 逐对核（`核對清單.tsv`→`逐條核.tsv`）：SAME 438、存疑 10（异质 2.2%）。
  存疑 10 对不并（总目条覆盖前后续别集而手建只一集、手建错挂另一书等，见逐條核）。
- keeper＝手建 Book（旧 id、影像、可能被 book-text 引用）；`copy_missing` 把总目条的卷数、责任者等 keeper 缺的单值栏补入，两边都有而不同的（edition／dating）记台账 conflicts。
  子 agent 指出 7 个手建题名本身有误（三經附義→十三經義疑等），这 7 对 keeper 改取总目条。
- 共 2,680 组，按 Work id 排序每 500 组一批（每批 1,000 个 Book），全部组见 `全部組.json`。
- `merge_books.py` 本批修两处：contained_in 同一 Collection 不重复挂；TODAY 取当天日期。

本目录是第 1 批（第 1–500 组），之后各批在 batch-05… 目录，只放 batch.json／merges.json／index-update.json。
门禁：check_v2 0；check-classification 0；check_promo_dup 0；audit-merge-ledger T/L/P/R/D 全 0（WARN edition／dating 为两边版本措辞不同，已入台账）；check-duplicate-audit PASS；index/books 不在本批刷新（index 分片人人都改，冲突太多；6 批合完后单独一个 PR 定点刷新）。
