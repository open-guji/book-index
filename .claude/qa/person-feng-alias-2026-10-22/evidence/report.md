# 本名／字／號：20:00 新組逐案研究

固定主線 `c6dd8356d613fc5614beb88f0a61a3d04cfb069e`。本輪 **8 個新人物組：5 confirmed／3 separate／0 open；原生合併 0**。8 組均在 broad 候選中 `old_case_ids=[]`，不替代既有案件；`supersedes_case_id=null`。四個已在 PR #1216 實施的人物組未重作。舊1876映射未使用。只寫本目錄，未改原生資料、既有研究、git分支或提交。

讀過 PLAN、19:00 報告及 broad 候選／stats；正式並條規則取固定主線 Git blob，存於 `merge-rules.snapshot.md`。SQLite readonly `metadata.manifest.base` 與固定主線一致、errors空；100份選中人物與所繫Work原字節逐份通過 SHA256 及 Git blob SHA1。這是 current-main 快照校驗，不是舊 checkout 當作新資料。

## 結論

| 案 | 人物組 | 判定 | 直接身份證據及著作複核 |
|---|---|---|---|
| PNA-2000-001 | 任希古／任敬臣 | confirmed | 經義考卷十四引計敏夫，唐詩紀事原文再證字敬臣、棣州、弘文館／太子舍人；兩稱名下文集十卷相應。 |
| PNA-2000-002 | 倪思／倪正甫 | confirmed | 班馬異同總目明言字正甫、歸安、乾道二年進士；直齋稱倪思正父，兼山論著三十卷與宋志正甫兼山小集三十卷互證領域，縣志亦載兩題。 |
| PNA-2000-003 | 凌稚隆／凌以棟 | confirmed | 左傳評注測義總目明言字以棟、明烏程人；五車韻瑞同題160卷，明志署以棟、總目署稚隆。 |
| PNA-2000-004 | 馮時行／馮當可 | confirmed | 經義考易論同條明錄字當可及名／字倒置異說，號縉雲、蜀人；縉雲文集總目以壁山及紹興官歷相合。 |
| PNA-2000-005 | 高翥／高九萬 | confirmed，執行另核污染 | 總目明言字九萬、號菊磵、餘姚；宋志補及千頃堂署高九萬菊磵小集，集名、時代相合。 |
| PNA-2000-006 | 劉清之／劉子澄 | separate | 清之字子澄不等於玉淵劉子澄。養吾齋集直接稱玉淵劉公諱子澄字清叔，並記十三世紀官歷；後者兩Work均屬玉淵文稿。 |
| PNA-2000-007 | 劉兆／劉延世 | separate | 劉兆字延世是西晉經學家；另一Entity談圃作者為宋臨江人，記孫升元祐／紹聖事，非晉人。 |
| PNA-2000-008 | 黃雲／黃應龍 | separate | 明黃雲字應龍、崑山、弘治訓導；璧林文集黃應龍經千頃堂明標嘉熙間人，非同一。 |

上述 confirmed 是身份結論，不是已執行合併，也不連帶授權合併作品。每案 `cases.json` 都含完整成員ID、建議 keeper/loser、當前檔路徑雙散列、原目錄JSON指標及完整相關著錄。

## 三個反例的必要區分

劉子澄案的獨立原文是劉將孫《養吾齋集》卷二十六〈跋劉玉淵道州九嶷山虞帝廟碑藁後〉，明寫「玉淵先生劉公諱子澄字清叔」，並敘甲午入東京及乙丑登極赦，不只是現代CBDB欄位不合。劉清之現行籍貫與提要有差異、提要紹興二年進士與生年1134相衝，均需另核，不能拿其既有錯誤抹去玉淵身份。

劉延世案不以朝代空白當晉人。四庫《孫公談圃》提要有宋臨江、孫升官歷及延世父知長汀，與晉代劉兆的周易／春秋注書明確不同。

黃雲案另見既有混人：丹岩作者明崑山人、字應龍，Entity卻帶咸寧、字叔卿、生1508等CBDB信息。本案僅排除與宋璧林黃應龍相併；須另開元數據歸屬研究，不能順手用未核值重寫人物。清黃雲 `hixi8u5qhgso` 不在這一對。

## 馮時行組的完整擬改方案

`candidate-ledger.json` 有官方審計可讀的 `merges/cluster_id/type=people/preconditions` 結構，完整原值按原owner保存；`candidate-records.json` 為三份完整候選JSON，沒有apply操作。建議 keeper `hixhd2h9bfe9` ← loser `hixhd2h9bun9`。

- keeper 保留所有原值，包括外部ID、description.sources上圖URL、ai_note、籍貫、1163卒年及原basis；僅加 `馮當可/別稱`、一條 `merged_in`、候選 `revised_at`。原值保留不等於本輪重驗。
- loser墓碑嚴限8鍵：schema_version、id、type、subtype、primary_name、revision、revised_at、merged_into。其獨有長ai_note、period_basis、updated_at等全值入台賬，不只靠git歷史。
- 唯一已知結構作者引用為 `Work/y/2/o/d59f2heaqy2o-易論.json` 的 `/authors/0/entity_id`，由 loser 改 keeper；保留原簽名馮當可、name_basis、原文各種名字倒置說、卷數與其他字段。僅另改候選revised_at。
- `field-ledger.json` 47行覆蓋三份記錄每個頂層字段的before/after及鍵存在性，巢狀值完整保留。兩人物所有字段即使相同也列出。生成器斷言墓碑8鍵、keeper來源／外部ID／ai_note不變、Work作者名／著錄不變。
- 既有 `entity_merge.py` 不會自動把loser.primary_name加為別稱，執行必須明做此動作。日期和執行者標記屆時刷新，原字段revision目前保留待實施政策決定。原生Entity不添works/_works。

`reference-review.json` 逐值掃SQLite現行 **Entity＋Work**，發現馮當可自身 `/id` 及上述作者引用，無其他整值／子串命中；自身 `/id` 不是改指目標。**本庫快照不含Book／Collection／分類／promotions，也未掃draft或book-text；故不能宣稱R/D/P或全庫引用通過。** 必須由實施者完成正式／草稿／文本全引用審查、來源hash新鮮度、T/L/P/R/D、changed-path check_v2、分類與官方builder（含有效`--text-index`，先write-index再check-only）。人物最小墓碑會移除loser既有period，索引增量須由官方builder得出，不假定等於0，不手造索引。

## 暫不選作執行候選的已確認組

高翥與高九萬的不同上圖URI在description.sources中，須保留兩來源，未驗證為同一權威URI；keeper CBDB欄位標記 ambiguous_2、floruit1137本輪未重驗。此外，現高翥名下《疏寮小集》`d59f2hgnyqdd`的提要自己明言是高似孫，屬附刻範圍污染。身份可確認，但不因姓＋字就把這些錯誤全部視為正確。凌稚隆keeper既有淩稚隆merged_in必須留存；其五車韻瑞作者別名分裂造成的兩Work另交集／子部研究，不在本人物案合併。

## 來源與交付

1. [唐詩紀事・任希古](https://www.shidianguji.com/book/HY0764/chapter/1klftq1rij293)：字敬臣、棣州與官歷。
2. [歸安縣志卷二十](https://www.shidianguji.com/book/NLG312001070845/chapter/1li7pjjvy2k2u)：倪思著述段連載兼山兩題（OCR版本，作旁證）。
3. [養吾齋集卷26](https://wk.100ke.info/wiki/養吾齋集_(四庫全書本)/卷26)：上述跋文；另可定位漢籍庫 `KR4d0456_WYG_026-15b–16a`。
4. [孫公談圃總目提要](https://www.shidianguji.com/zh/mid-page/7479176550866059274)：宋臨江劉延世、元祐紹聖背景。
5. [千頃堂書目卷29](https://zh.wikisource.org/wiki/千頃堂書目_(四庫全書本)/卷29)：黃應龍璧林先生文集嘉熙間人、高九萬菊磵小集一卷。
6. 經義考本庫明確影像頁碼：任希古 `KR2n0011_WYG_014-9a`；馮當可易論 `KR2n0011_WYG_025-4b`；劉兆 `KR2n0011_WYG_011-2b`及`174-3a`。完整原著錄及source_bid均在cases與snapshots。

`external-opened-sources.json` 保存五個實際開啟的原文回傳；`external-retrieval.json` 保留輔助搜尋上下文，搜尋摘要不單獨充作身份證明。`source-snapshots.json` 保留100原檔raw原字節、解析JSON、原路徑與兩散列；`related-works.json` 保存16人全部所繫Work作者，包含不利及污染材料。`validation.json` 明列有限斷言與未跑門檻。沒有宣稱完整schema或全庫測試通過。
