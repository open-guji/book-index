# 拆回-二：E／F／G 道 Book 跨版次多挂拆分

方案与研究：ai-team `domain/目录与资源/设计/2026-10-正式库全面去重方案/拆回二/研究报告-20261025.md`（细拆单元「拆回-二」）。

## 成因
E／F／G 道（总目自动录入）按「Work＋总目子目版本标注」聚簇，把同一子目在各丛书版次、各丛书里的总目实例记录并成一个 Book，再挂到所有对应 Collection；provenance 是各记录馆藏的拼接。一个 Book 是一个具体版本，应拆。

## 依据
open-guji-core/book_index_json `library_data/上海圖書館古籍聯合目錄（中國古籍總目）/parsed/`：每条实例的 `series.series_id`（所属丛书实例，＝Collection.sources[].id）与 `holdings[].item_uri`（＝provenance[].source 的 item id），可把每条源记录、每条馆藏逐条分回版次。

## 口径
见 `split_efg.py` 文档字符串。要点：按 series_id→已挂 Collection 分组，每组一个 Book，provenance 最多的一组保留原 id（revision 升 major），其余铸新 id（MachineID 2035）；无丛书的「××本」子目著录（0 馆藏）移出 sources、记 ai_note；版本以 Collection 为准，`edition` 置空、去 edition_type／publication_info／dating（原值取自聚簇代表记录）；indexed_by summary 按本组重写。存疑不拆：目标丛书已有同 Work 的 Book、源记录所属丛书未建 Collection、无丛书记录带馆藏。拆回串（部分 6 附）第一阶段 keeper 用 `--exclude` 排除。

## 工具
`split_efg.py --parsed <parsed 目录> --exclude <keepers-all.txt> [--only 文件] [--limit N] --out <批目录> [--apply]`。乾跑默认；PR 只入 `splits.json`（台账）与 `存疑.tsv`，`plan.json` 不入库。

## 规模（main 6311595 重算）
范围 526 个；可拆 467 个、新建 1,112 个 Book；存疑 53（已有同 Work Book 13、丛书未建 Collection 36、无丛书记录带馆藏 4）；拆回串 keeper 6。

## 批次
- batch-01（样本）：20 个原 Book，新建 83 个。门禁：build_derived --check-only fatal 0（dangling Book.work_id 4 为 main 既有，非本批）；check_v2 103 档 ERROR 0；check_schema 无 book 类 ERROR（Work／Entity 既有）；check-classification 0；check_promo_dup 0；check-duplicate-audit PASS。
  抽检（独立子 agent，全检 20 个原 Book／103 档）：拆错、归错 Collection、provenance 分错、字段误改、索引错均 0；拆后每个（Work, Collection）只一个 Book。小瑕 6 处已改工具后重落：新档文件名只用题名（不带旧版本名）、ai_note 区分「各源記錄標注一致」与「聚簇代表記錄」、滤掉总目解析杂质「磧砂延聖院刻」。待议：子目版本标注与所挂版次相合时是否保留 edition_type／publication_info（现一律去、记 ai_note）。
- batch-02：225 个原 Book，新建 538 个（main 026eda1）。门禁：check_v2 763 档 ERROR 0；check_schema 无 book 类 ERROR；check-classification 0；check_promo_dup 0；check-duplicate-audit PASS；build_derived --check-only fatal 0、dangling 0。
