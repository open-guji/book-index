# 經部五組新增研究（2026-10-22T2022）

固定主線 `c6dd8356d613fc5614beb88f0a61a3d04cfb069e`。本輪 **5新確認／0分立／0待核**，共10條active Work；**原生合併0、execution_ready=false**。確認只限作品身份，不等於可執行、人物已合或藏本已核。所選是 broad 候選索引47、48、63、69、74；對本路全部既有cases檢查，兩側ID交集為0，supersedes均空。候選相似度與共用entity不作身份證明。

| 案號 | 作品 | 兩側ID | 直接證據及邊界 |
|---|---|---|---|
| JC-2022-001 | 尚書要略 | d59f2gcv7h1e / d59f2gidf5z4 | 四庫提要明列吾丘衍又稱吾衍，並列此書；非尚書原典 |
| JC-2022-002 | 卦爻象占分類 | d59f2gcybugx / d59f6eryjldy | 經義考及周易集說提要指俞琰字玉吾，另著此書；不吞讀易須知／周易集說 |
| JC-2022-003 | 論語解 | d59f2he2mry8 / d59f2hlnrf9e | 郡齋書目「謝顯道論語解十卷」直接連接經義考良佐十卷；焦志二卷留原值 |
| JC-2022-004 | 毛詩名物解 | d59f2hrbldz4 / d59f2hs0vlz7 | 經義考蔡卞元度同條；早稻田通志堂本題蔡元度而作者欄蔡卞 |
| JC-2022-005 | 古韻通說 | d59f2mrsy0w2 / d59f2nbi5728 | 清史稿本傳連接啟瑞、翰臣、古韻通說二十卷；藝文志四卷留原值 |

## 三組較清楚的名／字重出

**尚書要略。** [經義考卷86](https://zh.wikisource.org/zh-hant/經義考_(四庫全書本)/卷086) 明列吾丘氏衍；[竹素山房詩集提要](https://zh.wikisource.org/wiki/竹素山房詩集_(四庫全書本)/全覽) 在同一段明說其名或稱吾衍，又列此書，[附錄王禕本傳](https://zh.wikisource.org/zh-hant/竹素山房詩集_(四庫全書本)/附録)亦有著述目。這比庫內先合人物更直接。d59f2gidf5z4已收尚書要畧歷史墓碑d59f6eoatg5i，該項不重算；經義考「未見」仍是朱彝尊見聞，不提升為全佚。現存contains_text_of邊與其古今文範圍未另核，實施時保留且核查，不能趁合併改指。

**卦爻象占分類。** [經義考卷40](https://zh.wikisource.org/zh-hant/經義考_(四庫全書本)/卷040)引吳中人物誌明言俞琰字玉吾，並列此書；[周易集說提要](https://zh.wikisource.org/zh-hant/周易集説_(四庫全書本))亦列為另著，說舊附集說。這一點恰好阻止把附刊關係誤作同一作品：本輪只合兩個《卦爻象占分類》書目對象，不改既有《讀易須知》分拆，不吸收《周易集說》或《周易》原典。千頃堂側author_info的「缺」保留為來源原語，不作人名或全佚判斷。元史藝文志是後人補志，不能當元代獨立成書上限。

**毛詩名物解。** [經義考卷105](https://zh.wikisource.org/zh-hant/經義考_(四庫全書本)/卷105)同條稱蔡卞元度；[早稻田館藏原目錄](https://www.wul.waseda.ac.jp/kotenseki/html/ro12/ro12_03609/index.html)題蔡元度集解、成德校訂，而作者權威欄為蔡卞，版為通志堂康熙十五年序。本路故宮來源Work亦二十卷通志堂本，可確認作品同一。**未讀故宮贈善023662原始館藏頁，也未判Book重複。** 故宮側juan_count二十卷、measure_info二十卷卻measures冊20，屬待核欄位衝突；早稻田此實物1冊不可套在故宮本。蔡元度集解／蔡卞撰、各藏本及四庫資源全部保留。

## 兩組卷數歧異：確認身份，保存未決原因

依固定main `schema/cataloging-rules.md` III.1，二條分見二志而卷數異，**不作二書之證**；同一志內各有完整獨立著錄才須懷疑二書。本輪有直接人書連接，不是僅憑同人同題猜合；但沒有將卷差原因宣告為已解。

**謝良佐／謝顯道《論語解》。** [宋史卷428](https://zh.wikisource.org/zh-hant/宋史/卷428)證明字顯道；[郡齋讀書志卷四](https://zh.wikisource.org/zh-hant/郡齋讀書志/卷四)以顯道列同題十卷，[經義考卷214](https://zh.wikisource.org/zh-hant/經義考_(四庫全書本)/卷214)以良佐列同題十卷並載自序。焦志二卷讀法也見[古今圖書集成卷267轉引](https://zh.wikisource.org/zh-hant/欽定古今圖書集成/理學彙編/經籍典/第267卷)，因此不能把庫內二卷一筆改稱OCR。暫無證據說它是另編或節抄；合併台帳應逐源保留兩卷／十卷，實物若另顯改編則先分流。宋史傳末作《論語說》，本輪只以本傳證人名，不把所有《論語說》擴入。原有誤題《范祖禹論語解》之歷史記錄完整封存，不再算新成功。

**龍啓瑞／龍翰臣《古韻通說》。** [清史稿卷482本傳](https://www.shidianguji.com/book/LS0025/chapter/1kt95z2ebilhb)把本名、字翰臣、書題及二十卷連在一起，並述本音、通韻、轉音內容；[卷145藝文志](https://zh.wikisource.org/zh-hant/清史稿/卷145)以字列四卷。這是志與傳異數，不是同一志內兩條完整同題書。二十卷同治六年版為另一側具體來源，四卷原因尚未證。**不得臆稱四冊誤作四卷、殘本或縮編，也不得改寫藝文志引文。** 書名與責任身份可確認，實際序目與Book範圍仍是執行門檻。清史稿兩個網頁轉錄不當兩個獨立古代證人；翰臣之字／號說也不藉此強行統一所有人物來源。

## 保存與驗證

- `cases.json`：5案含case_id/status/ids、固定main路徑及SHA1/SHA256、精確JSON pointers、14項外證對應、逐案門檻；每案execution_ready=false、machine_merge_mapping=null。
- `main-records.json.gz`：10條完整data及逐字raw_utf8，原有作者、引用、描述、note、歷史併條與矛盾欄位全存。
- `references.json`：14項原典轉錄／館藏機構目錄，卷節及定位，短引文和證據限度；未核刻本影像。經義考、圖書集成及重複轉錄不冒稱獨立古代證人。
- `validation.json`：readonly SQLite manifest base相合、tree SHA256相合；10條逐一讀git blob重算Git SHA1及字節SHA256，與SQLite parsed值相合且active；所有指標可解，既有本路case ID交集0。
- `build_checkpoint.py`：只在本目錄重建產物，無Git寫操作；已實際運行成功。

未跑全庫型別入邊／Book實物／promotions／草稿／book-text審計，未建可執行逐字段合併台帳，未做寫後T/L/P/R、schema/check_v2、分類、官方索引及builder比較。這些沒有假稱通過。不同Person entity是後續獨立審計事項，不隨Work確認而合併。

僅寫 `classics_titles/hourly-20261022T2022/`。JC-001／JC-007繼續hold，BOOK-0010繼續defer，未重用1876映射，未觸冯時行驗證及PR1216人物；無原生資料修改、提交、分支或共用STATUS修改。
