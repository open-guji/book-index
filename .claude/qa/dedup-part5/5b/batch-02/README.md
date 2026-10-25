# 去重方案部分 5b 第 2 批：故宫平圖号↔总目北平本、总目重复著录（2026-10-25）

基线 main 66fcf7619。来源：5b-研（ai-team 去重方案目录 5b-研/）给出的「北平平圖号可并子类」与「同馆同卷 78 对」。

- PT 159 组：故宫「平圖」号 Book（北平图书馆旧藏、今寄存台北故宫）＝总目「北平圖書館（藏臺圖）」Book，是同一部实物的两条著录。
  keeper＝总目 Book；被并者的 provenance（故宫馆藏、平圖号）并入 keeper，并在该条 notes 记「故宮著錄版本：…」（两边版本措辞不同时）；
  keeper 缺的单值栏（metadata.npm_item_id、physical_description、dating 等）从被并者补入，两边都有而不同的记入台账 loser_original_notes.conflicts。
- TG 20 组：总目重复著录／同源重复建档／早先并条遗留，keeper＝馆藏多、信息全者。
- 候选 181 对（候選.tsv），独立子 agent 逐条核 181 SAME（逐條核.tsv）；其中 2 对在本批开工前已被别的串并掉，实并 179 组 179 个被并者。

被并者留墓碑；sources／indexed_by／provenance／contained_in／resources 取并集；promotions 19 个文件改指 keeper。
门禁：check_v2 0；audit T/L/P/R/D 全 0；check-classification 0；check_promo_dup 0；check-duplicate-audit PASS；index/books 定点刷新。
