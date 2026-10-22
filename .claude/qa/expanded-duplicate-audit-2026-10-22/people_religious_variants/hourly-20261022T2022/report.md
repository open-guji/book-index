# 僧名前綴、異體及跨代同名：PRV-2022 四組新案

固定 main `c6dd8356d613fc5614beb88f0a61a3d04cfb069e`。新增 **4組：confirmed 3、separate 1、open 0；原生並條0**。全部候選均無 inherited prior_case_ids，另遍查本審計既有 cases*.json，八個人物ID均未見已有案件。本輪沒有重做明皇、#1216四人物或冯时行，未使用舊1876映射；BOOK-0010仍延期。

| 案號 | 候選與完整成員ID | 結論 | 新證據與風險 |
|---|---|---|---|
| PRV-2022-001 | C11961 釋道誠 `hixhd2h9bikf`／僧道誠 `hixhd2h9boyw` | confirmed | 《釋氏要覽》自序署錢唐月輪山釋道誠、天禧紀年；宋志兩書同署僧道誠；DILA明接慧悟大師、《尼蒙求》及當前CBDB53758/Wikidata Q45679936。較適合下一批低引用人物候選。 |
| PRV-2022-002 | C11981 通復 `hixhd2h9biq8`／釋通復 `hixhd2h9bk0g` | confirmed | 《清史稿》方外《冬關詩鈔》六卷通復，四庫提要釋通複字文可，卷首嘉禾釋通復文可與盛遠輯互證。通復唯一Work卻被改題《傳經室賦》，必須分開處理題名污染。 |
| PRV-2022-003 | C11992 清釋行海 `hixhd2h9bj3o`／宋釋行海 `hixi8u605tnq` | separate | 《金山志略》緣起自署康熙二十年、臨濟圜祖第二十一代；宋《佛祖統紀》列雪岑行海為佛光照法嗣，DILA與CiNii連至南宋《雪岑和尚續集》。年代、師承、著作均不同。 |
| PRV-2022-004 | C12760 曇曜 `hixhjhaw7y0y`／釋曇曜 `hixhjhaxs4qo` | confirmed | 《開元錄》卷六同一沙門釋曇曜條列《大吉義神咒經》二卷或四卷、《浄度三昧經》一卷，接和平三年北臺譯事。現role「撰」及卷數差異不能隨人物並條抹平。 |

## 已完成的可覆核內容

readonly SQLite的manifest固定base與無errors狀態已核對。本輪8份Entity、10份相關Work共18份檔案，不僅核SHA256和Git blob SHA1，還逐份以固定main的 `git show BASE:path` 原始bytes比較完全相同；原bytes獨立保存於 `snapshots/<id>.json`。`source-snapshots.json`含原路徑、兩種hash、解析值和census manifest。`validation.json`記錄每檔精確比較結果及既有案件排查清單。

全量讀取該census的Entity/Work字串引用，`known-references.json`將exact JSON pointer與embedded_text分開；此次10個相關Work各有一條當前作者入邊，其中keep側引用也在內，不能把10當作待改指數。`field-ledger.json`留存八人物93行top-level原值，這是寫前保留台帳，**沒有執行後值或已過無損合併驗證的宣稱**。

11項來源分別保存URL、原典/機構規範類別、已讀定位、短摘錄及摘錄SHA256於 `sources.json` 和 `sources/`。原典使用已開啟的轉錄；不是原書影像全量歸檔。雪岑集的NDL影像未取到，因此沒有聲稱直接讀過其自序；其宋代身份由宋代法嗣名目、機構規範與作品書目串聯。刻本的寬文五年（1665）不是作者年代。

## 三個確認組的執行邊界

**道誠可優先，但尚未完成全庫門檻。** 候選保留 `hixhd2h9bikf`，併入 `hixhd2h9boyw`。已知待改僅《釋氏須知》`d59f2px3sd1e`及《釋氏要覽》`d59f2pvz7im9`的 `/authors/0/entity_id`；《尼蒙求》`d59f2ogc2136`已指keep側。保留慧悟大師、外部ID、CBDB manual/pending_accept原來源、錢塘地名ID、原ai_note和所有歷史著錄；《須知》與《要覽》不因同作者而併書，原author.name及name_basis中的歷史舊ID不直接改寫。「撰」與自序「編集」的責任表述另行校核。

**通復的題名污染先拆清。** 候選保留 `hixhd2h9bk0g`，併入 `hixhd2h9biq8`。唯一loser作者邊為 `d59f2nukva4h /authors/0/entity_id`；其 `/indexed_by/0/title_info`仍為冬關詩鈔，`/indexed_by/0/summary`仍為六卷通復撰，`/title`卻是傳經室賦，`/ai_note`聲稱修正解析截取錯誤。現已讀原《清史稿》方外段明確支持冬關詩鈔；下步必須查這次錯改的來源/歷史及所有相關引用，再決定書名恢復與Work去重。不可把清史稿錯改名稱當通復另一著作。`d59fxrulkd8g`《冬關詩草》為不分卷稿本，與六卷詩鈔之範圍未證相同，仍不併書。四庫通複與原集通復並存形式要署源保留。

**曇曜身份明確，作品責任仍有獨立問題。** 候選保留 `hixhjhaxs4qo`，併入 `hixhjhaw7y0y`。已知待改《大吉義神咒經》`d59f9bl4z950 /authors/0/entity_id`一處。《淨度三昧經》`d59f9bl687b5`已指keep側。兩書現role「撰」，而原錄、補魏書建檔說明及上圖責任均支持譯事；應單獨、有來源地處置。大吉義二卷/或四卷可共存於來源，不抹除四卷著錄。《淨度》一卷第四譯闕本不能與其他譯者二、三卷本或《北台淨度三昧經》機械相併；吉迦夜與曇曜合作譯事也不等於兩人同一。

## 下一道共同門檻（本輪未運行）

原生執行前重驗當時main及每檔hash，查完整原生型別、分類、promotions、草稿庫、book-text全16非空分片引用；定實際保留字段/來源/alias/merged_in、合規墓碑及版本日期；改當前引用而保留歷史ID；再對實際改後路徑跑schema、check_v2、classification、官方索引/builder及獨立T/L/P/R與人物無損台帳驗證，分離基線既有失敗。官方L不覆蓋人物全字段，不能代替此台帳。這些執行驗證均未運行，本輪沒有原生修改、git index/branch變更或任何併條操作。
