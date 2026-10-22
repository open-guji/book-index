# 本名／字：20:22 四個新人物對

固定主線 `c6dd8356d613fc5614beb88f0a61a3d04cfb069e`；**4 新案，2 confirmed／2 separate／0 open，原生合併 0**。8 個人物均有原字節快照。與審計目錄各 `cases.json` 的完整成員對比，四對均無既有案件，不替代舊案。未觸碰 #1216 四組、馮時行實施、BOOK-0010 hold 或舊1876映射。

| 案 | 人物與完整 ID | 判定 | 要點 |
|---|---|---|---|
| PNA-2022-001 | 仇兆鰲 `hixhd2h9bf9t`／仇滄柱 `hixhd2h9bjaz` | confirmed | 杜詩詳注總目直稱兆鼇字滄柱、鄞縣、康熙乙丑進士；兩稱名下參同契集注二卷相接。建議 keeper 仇兆鰲。 |
| PNA-2022-002 | 龔昱 `hixhd2h9buzq`／龔立道 `hixhd2h9bm5v` | confirmed | 樂菴語錄提要與樂菴遺書總目均稱昱字立道、崑山、李衡門人；崑山雜詠同題同地域著述相合。建議 keeper 龔昱。 |
| PNA-2022-003 | 何澹 `hixhd2h9bosw`／何自然 `hixhd2h9bdqk` | separate | 宋史確有何澹字自然及何自然稱名；但現Entity的何自然是新唐書已著錄笑林三卷的作者，不能併給乾道二年進士。 |
| PNA-2022-004 | 何涉 `hixhd2h9bnw5`／何濟川 `hixi5fstaolq` | separate | 宋史何涉字濟川、范仲淹元昊時官歷及治道中術／春秋本旨；另一Entity的管窺圖說、溝洫圖說責任者明署清何濟川。 |

## 證據與不利材料

仇組的主要姓名橋是當前《杜詩詳注》`d59f2mi7ebk1` 的 `/indexed_by/0/summary`，不靠CBDB別名自證。清史稿《參同契集注》`d59f2nmpfsw0` 與古籍總目《古本周易參同契集注》`d59fxxr66fwh` 對應名／字和本體二卷；後者含補遺、附錄、圖說，且作者尚無entity_id，故不機械併Work或自動補鏈。[CiNii BB21230531](https://ci.nii.ac.jp/ncid/BB21230531) 實物著錄記封面「甬上仇滄柱輯」，權威作者繫仇兆鰲，作旁證。仇知幾另有Entity且所繫悟真篇集注有跨時代著錄污染；此輪未裁定仇知幾，也不把兩人案擴成三人執行。keeper的ambiguous_2、外部ID、1638–1717及上圖來源均完整保留，不宣稱本輪逐項重驗。

龔組獨立原文見[四庫樂菴語錄提要（合載於芻言頁）](https://zh.wikisource.org/zh-hant/芻言_(四庫全書本))，明言龔昱字立道、崑山及李衡門人，並引吳仁傑後序。當前樂菴遺書 `d59f2hsc45j4` 的總目也有姓名橋，但對文本真偽存疑，疑文已全保留；不以身份確認裁定傳本真假。崑山雜詠三卷與四卷的差別，可參俞允文二十八卷本 `d59f2ninzbwh` 提要追述龔昱原編三卷、續集一卷；這只解釋可能差異，未逐葉核範圍，不是Work合併許可。現有丘道、邱道等異字原值不刪。

何澹案讀到[宋史卷394](https://zh.wikisource.org/wiki/宋史/卷394)何澹傳，又實際開啟[新唐書卷59](https://zh.wikisource.org/wiki/新唐書/卷059)行1885「何自然笑林三卷」。這是確實存在的名／字橋與確實不能跨接的作者鏈並存。現何自然的CBDB來源已帶dy_mismatch_6及ambiguous_2；不能拿不可靠權威匹配推翻原著錄先後。題名《何澹小山雜著》無結構作者，另列線索；《何澹安醫案》是何遊，不因子串相同而認作何澹。

何涉案讀到[宋史卷432](https://zh.wikisource.org/wiki/宋史/卷432)行270–274，字濟川與北宋官歷、治道中術和春秋本旨可直接交叉核對。《經義考》`KR2n0011_WYG_188-6b` 引程端學的姓名橋亦保留。清何濟川兩部結構作者Work的總目責任者明署清，另《宮室圖說》`d59fxrbvycqq` 無entity_id，仍有清何濟川署名。嘉慶二十五年只是刻本年代，不能單獨當作者生存年代；本案使用責任者著錄與宋代人物原傳作區分。清人原序未讀、CBDB 582058唯一性未驗、南充／西充等異文全部保留。

## 覆核與執行門檻

`source-snapshots.json` 保存 **44 份原始記錄（8 Entity、36 Work）** 的完整raw、JSON、路徑、SHA256及Git blob SHA1；每份都重算雙散列並與實際Git blob字節比較一致。SQLite readonly manifest與固定主線一致、errors空。36 Work為選中ID或所列姓名異寫命中的全部活躍Work，含不利、題名子串和無entity_id著錄，並非全部都屬選中人物；具體全量原值在 `related-works.json`。結構作者所繫Work數依四案為3、3、2、5。

逐值掃描當前census活躍 **Entity 56,703＋Work 266,045**，找到選中人物ID的 **21 處引用／自身ID命中**，各有JSON pointer及完整原值，見 `reference-review.json`。其中8處是Entity自身ID，13處為Work作者。**沒有掃Book、Collection、分類、promotions、草稿或book-text，不能宣稱全引用審查通過。** 此輪也沒有候選改寫、完整字段合併台賬、schema、T/L/P/R/D、check_v2、分類或官方builder執行。

若實施兩個confirmed案，先刷新main及hash，完成逐字段無損台賬，保留每個owner原值、歷史與來源；再做正式／草稿／文本全引用掃描。保持作者原簽名及name_basis；墓碑最小字段和keeper merged_in、別稱須依正式規則逐項安排。人物同一不授權Work合併或污染元數據修正。實際寫後才可跑T/L/P/R/D、schema、changed-path check_v2、分類及帶有效text-index的官方builder基線比較，不能手工製索引。

`external-retrieval.json` 與 `external-primary-addendum.json` 保留外部回傳及失敗；第一次find不命中的宋史／新唐書後來以行號open取到實文，最終證據已更新。`cases.json` 有各案完整ID、paths/hashes、著錄指標、全部已知ID引用和未跑門檻；`validation.json` 明列有限通過項及未執行項。產物僅寫本目錄，無git／原生資料變更。
