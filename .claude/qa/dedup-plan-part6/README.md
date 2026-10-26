# 去重方案部分 6：Collection（丛编）去重

方案：ai-team `domain/目录与资源/设计/2026-10-正式库全面去重方案/部分6-Collection丛书与文本迁移.md`（10-25 修订）。基线 main `0421b1ca72`。

## 口径
一个 `book_collection` ＝《中国古籍总目》一条丛书版本记录。只有**同一源记录**（`sources[].id`／ai_note「源記錄：」）被录成两个 Collection 才并；同题而版本、馆藏、卷种数、编者不同的是不同版次或不同藏本，不并。成员 Work 重合度不是重复证据（同一丛书不同版次收书本来一样）。

## schema
本 PR 先给 Collection 加墓碑：`merged_into`（墓碑）、`merged_from`（keeper），形状照 Book 墓碑，见 `schema/CHANGELOG.md` 2026-10-25。

## batch-01：同源记录重复 7 组（并）
| 案 | keeper | 被并 | 成员 Book |
|---|---|---|---|
| COL6-01 | 8rldonorf7cx 武英殿聚珍版書一百三十八種·清乾隆間浙江刻本 | 8rldoolynbpi | 149／66 |
| COL6-02 | 8rldonorf7cy 同·清同治十三年江西書局刻本 | 8rldoolynbpj | 149／66 |
| COL6-03 | 8rldonorf7cw 同·清乾隆間武英殿木活字印本 | 8rldoolynbph | 149／66 |
| COL6-04 | 8rldonor3yte 同·清乾隆四十二年福建刻道光同治間遞修光緒二十一年增刻本 | 8rldoolynbpg | 149／66 |
| COL6-05 | 8rldolb9c2rm 檀几叢書五十種二集五十種餘集四十七種附政十種·清蘇州掃葉山房翻刻本 | 8rldomtfn94w | 147／129 |
| COL6-06 | 8rldocewfl6o 合刻三志八十種·明末刻本 | 8rldobgkn282 | 81／79 |
| COL6-07 | 8rldomtfc0lc 陳太史重訂百川學海一百七種·明刻本 | 8rldolb9c2rl | 102／101 |

两档除 id 外字段全同（冲突字段 0）。keeper 取成员多者。555 个成员 Book 的 `contained_in` 改指 keeper（已同挂的去重；成员项属性冲突 0），revision 升 patch；promotions 2 个文件只改 `production_id`；`index/collections.json` 刷 7 条。
工具：`merge_collections.py`（乾跑默认）、`update_index.py`（同 163 案版，加 Collection）。台账 `batch-01/merges.json`。

## batch-02：同版本名、不同源记录 11 对（只互链）
`link_related.py`＋`batch-02/pairs.tsv`：按 V07 存 id 较小一侧，补 `related_collections`。含明抄本 4 对（抄本各自独一，不并）。

## 门禁
check_v2（569＋23 档）ERROR 0；check_schema ERROR 0；check-classification 0；check_promo_dup 0；check-duplicate-audit PASS；
`audit-merge-ledger --draft ../book-index-draft` T/L/P/R/D 全 0（本 PR 给该脚本加了 Collection 组的成员改指检查）。草稿库无指向被并者的引用，不需草稿库 PR。
回滚：revert 本 PR。

## 抽检（独立子 agent，10-25）
7/7 组全检：均为同一源记录除 id 外逐字相同，错并 0。并前挂被并者的 573 个成员全部核过：contained_in 恰一条 keeper、无重复、其余字段未变；promotions 只改 2 处 production_id；工作树里被并 id 只剩墓碑自身与 keeper 的 merged_from。

## batch-03：同一实物的总目条对手建条 2 组（并，10-26）
部分 5 线程查出、部分6 附件漏配（附件只把手建条和影印本配了对）。依据是同一实物：两套都是孤本写本，今藏臺北故宮。

| 案 | keeper（手建，引用多、带影像） | 被并（总目叢書线条） |
|---|---|---|
| COL6-08 | 8rlb6yi1ecqo 欽定四庫全書·文淵閣本 | 8rldp1yeqrk0 文淵閣四庫全書三千四百六十一種·清乾隆間内府寫本 |
| COL6-09 | 8rlb6yk66qdc 欽定四庫全書薈要·摛藻堂本 | 8rldo48qtsld 摛藻堂四庫全書薈要四百六十八種·清乾隆三十八年内府寫本 |

被并题名记入 keeper 的 additional_titles；总目的 indexed_by、sources、edition 并入；COL6-08 的 authors、publication_info 改取总目值（`prefer_loser`，原值在台账）；keeper 的 ai_note 记并条来历。3,797 个成员 Book 的 contained_in 改指 keeper，promotions 改 2 处。
与「拆回丛书版次错并的 Book」线程（dedup-split-series）对齐：它的 #1280 先合，本批从其后的 main 重跑；它的 split.py 已改为沿 Collection 墓碑走到 keeper。
门禁：check_v2（3,801 档）、check_schema、分类、升格、重出审计、audit-merge-ledger（--draft）T/L/P/R/D 全 0。
抽检（独立子 agent，全检）：2/2 组并对；3,797 个成员逐个比对，contained_in 只换 id、其余字段未变；无残留引用。据其意见补修：文淵閣 keeper 的 dating 随 publication_info 改为乾隆（basis 注明来历），ai_note 日期笔误更正。另报：并后同一 Work 在文淵閣下挂两个以上 Book 2,485 个、摛藻堂 297 个（总目子目 Book 与手建 Book 同一实物重复），交部分 5。
