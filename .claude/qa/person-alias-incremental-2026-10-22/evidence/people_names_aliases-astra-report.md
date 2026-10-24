# 本名／字／號：固定 main 複核及兩組小批方案

固定基線：`c6dd8356d613fc5614beb88f0a61a3d04cfb069e`。本輪只寫此研究目錄，原生資料、分支、提交均未改。已讀 main《正式庫並條審查規則》。

## 真實進度與計數

舊研究按 supersedes 去重為 **15 confirmed／2 separate／5 open，共22組**，涉及16個待併 loser。逐組檢查最新 main：**15組確認案全部尚未實施，16個 loser 均未有預定 merged_into**。本輪新實施合併 **0**，新確認人物 **0**；本輪選出的兩案仍是舊確認案的執行準備，不能重複加到15組上。

檢查22組涉及45份 Entity，以及所選兩案的11份既知 Work，共 **56個原檔**；固定 main 的 Git blob SHA1 與完整舊 checkout 原始字節計算值全部一致，且56份 SHA256 全部與既有研究一致，**已核路徑漂移0**。這一檢查直接對固定 main 的 tree object，比舊 checkout 的日期更可靠；只有字節身份相同者才讀作當前 main。`main-source-validation.json` 保存每條雙雜湊及結果，`main-coverage.json` 保存全部22組狀態。本輪沒有宣稱重做45位人物的全部文獻研究，也沒有宣稱完成全庫新增引用搜尋。

## 首選小批

| 本輪案／替代案 | 人物同一性 | 既知當前引用 | 已定位的改指 |
|---|---|---:|---|
| PNA-A001／PNA-R011 | 錢易是本名，希白是字；錢希白為姓連字別稱 | 6 Work | 《洞微志》1個 entity_id |
| PNA-A002／PNA-H002 | 喻樗是本名，子材／子才是字；喻子材為姓連字別稱 | 5 Work | 《豐公逸事》1個 entity_id |

兩側 loser 都沒有相衝突的外部標識或生卒欄；不是憑同字或同名硬併。對這兩組，現有全部**已知**責任者引用與宋人書目領域相合，未見另一朝代同名人的反證。11份當前原檔與4份人物原檔完整保存在 `selected-source-snapshots.json`；不是僅存摘要。

### 錢易／錢希白

保留 `hixhd2h9bhe7`，併入 `hixhd2h9blpt`。固定 main 的《南部新書》`Work/x/s/1/d59f2hu6wxs1-南部新書.json` 同條保留《四庫總目》明言字希白、《國史經籍志》題錢希白及《直齋書錄解題》稱錢易希白，將本名與字直接聯繫到同一著錄。外部重新打開[《南部新書》四庫提要及錢明逸序](https://zh.wikisource.org/wiki/南部新書)，第131行明載名與字，第140行將成書放在真宗祥符間。CBDB人物146搜尋索引列《洞微志》，直接打開只返回頁殼，僅記作輔證。

精確的已知改指為 `Work/9/1/f/d59f2hket91f-洞微志.json` 的 `/authors/0/entity_id`：`hixhd2h9blpt → hixhd2h9bhe7`。其餘五條已繫 keeper；《南部新書》不用因原著錄有錢希白而重複改指。姓名及 role 均保持原著錄。

字段處理：keeper 已有「希白／字」，只增「錢希白／別稱」；不添加未經此案核實的號。loser 沒有獨有傳記文字與外部標識，兩側管理字段有差異，必須按墓碑／merged_in規則保存原值。keeper 的 `dates.floruit=[969,969]` 源自 `cbdb:index_year`，不把它當本輪已證實的活動年、生年或人物同一性證據；保留既值並在台賬註明，不把外部網頁生年異說順手覆寫。

### 喻樗／喻子材

保留 `hixhd2h9bhcp`，併入 `hixhd2h9bppr`。外部重新打開[陸游《入蜀記》卷1](https://zh.wikisource.org/wiki/入蜀記/卷1)，乾道六年六月十二日、第152行稱「喻子材郎中樗」。固定 main 的 `Work/f/p/g/d59f2hdmefpg-易義.json`《經義考》引紹興府志稱喻樗字子才，姓名與官歷互證。這是同時代文獻直稱，並非由《豐公逸事》的題名推人。

精確的已知改指為 `Work/7/i/9/d59f2psls7i9-豐公逸事.json` 的 `/authors/0/entity_id`：`hixhd2h9bppr → hixhd2h9bhcp`。其餘四條《易義》《大學解》《四書性理窟》《論語學》已繫 keeper。

字段處理：保留子才、子材兩種字形和 keeper 原有湍石、玉泉兩號；只增喻子材為別稱。本輪沒有重新認定兩號、卒1180或籍貫等既有傳記值。loser `ai_note` 獨有「乙等建人、僅見《豐公逸事》、未定代」建檔歷史，必須完整進台賬並按原 owner 保留，不能因與新結論不一致而刪去歷史。本輪將它視作已被新證據補足的舊判斷，不當作另一人的證據。

## 未選入首批的元數據疑點

莊綽／莊季裕仍維持 confirmed，不計為新待核人物；但 keeper `dates.floruit=[1059,1059]` 僅據 `cbdb:index_year`，與《雞肋編》提要所記紹聖至紹興、紹興三年序不是同一種時間證據。[提要轉錄](https://zh.wikisource.org/zh-hant/雞肋編)已重新打開。這提示活動年字段來源須核，不足以證兩人不同，也不授權此輪改日期。本批優先採用上列引用較小、字段較單純兩組；詳 `metadata-risks.json`。

五個既有 open 保持原裁決：柳宗直／柳正夫、俞琰／俞玉吾、李杲／李東垣、汪仲洋／汪少海、朱敦儒／朱希真。俞琰含清代同名編者、李杲含王好古《此事難知》的污染門檻不因同名字號可靠而解除。沈束／沈宗約及李昭遘／李逢吉兩組仍分立，不得把別人的本名併成其字。

## 交付與剩餘執行門檻

`candidate-merge-plan.json` 是兩組的機器可讀候選台賬：固定 main SHA、前置 SHA256、keeper／loser、完整原值、別稱增補策略、兩處確切 JSON pointer 改指及後置門檻齊備；`apply_enabled=false` 明示只準備方案。兩個案例在 `cases.json` 用 supersedes 標示舊案，累計計數仍為15／2／5。

本輪把11個既知引用逐原檔重核，沒有重新全掃最新 main 的全部 Work／Book／Collection／Entity／分類／promotions，更沒有全掃草稿及 book-text。故「沒有新引用」與「跨庫殘留為零」均未宣稱。實施前須補全上述活躍型別引用搜尋，更新全部真引用；歷史台賬與 ai_note 中的舊 ID 不全域替換。發現新增引用即先核其責任者同一性，不可只盲改已列的兩處。

實施時還須保留 loser schema最小墓碑與 keeper merged_in、來源／舊註／關係聯集，核 promotions 只改 production_id，處理草稿及文本引用，然後跑 `audit-merge-ledger.py` 的 T/L/P/R、實際變更路徑 `check_v2.py --paths -`、分類檢查、builder。這些寫後門檻本輪未跑，不冒稱通過。人物合併不授權併任何 Work、Book 或改書名、卷數。
