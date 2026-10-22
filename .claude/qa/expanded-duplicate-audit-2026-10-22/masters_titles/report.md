# 子部近題與版本重出恢復研究（2026-10-22）

基線：`bfaf3cfb3b9b0475fc9fd8d2ce216c291ebc9cca`。本分道僅提交研究案卷，未改原生資料，未建立 PR。

重讀全庫 266,045 個活 Work；其中原始著錄 section 明列子部的 36,833 條。獲得 5 組完整 indexed_by 同源重出及 98 組同作者題名/異名交集候選，候選不等於確證。全掃 381,716 個 Book 檔，保存 122 個相關活 Book 原始快照；最終確證 Work 涉及 115 本。

**目前 51 案：19 組 Work、3 組 Book 可合併；23 組 Work 待核；6 組應分立。** 所有原檔 SHA-256 重新驗證通過，確證群組 ID 不重疊。

## 可合併案

| 案號 | 類型 | 書名 | keeper ← loser | 理據 |
|---|---|---|---|---|
| MR-001 | Work | 新雕洞靈真經 | d59fydyduha8 ← d59fyfkh8f7k | 完整 indexed_by 相同，均同一上圖源記錄 t5fdt5mvl7kspg0x；差異是一次晉升前補作者，何粲注在兩條原文均明示。 |
| MR-002 | Work | 修行捷徑 | d59fy2maxnnk ← d59fy6kgwm4g | 完整 indexed_by 相同、源記錄 drwyyz2b2gg0i5fi 相同；一側佚名為漏錄，原文清雲龕道人等撰已於keeper補入。 |
| MR-003 | Work | 大藏治病藥 | d59fydh8f1fm ← d59fydxeknwg | 同一總目著錄、同一組8源版本；完整 indexed_by 相同，差異僅漏錄輯者黃秩模。 |
| MR-004 | Work | 龍瑞觀禹穴陽明洞天圖經 | d59fydxphyww ← d59fyfkj3ugx | 完整兩條 indexed_by 相同，來源 mn24bl1ybmaouwyn 及歷史合併帳相同；差異僅漏錄撰者葉樞。 |
| MR-005 | Work | 佛說希有校量功德經 | d59fy9ep4ikg ← d59fydymwd1c | 完整三條 indexed_by 及歷史合併帳相同；同一譯本同一導入源 wjj7a2f4dl1egcfr，另一側authors被清空。保留闍那崛多譯；不是把不同譯者同名經合併。 |
| MR-007 | Work | 青囊序 | d59fy11nzk76 ← d59fxt2urrwi | 原題明列青囊敍為異名；曾文辿、一卷完全相同，序/敍為題名異寫，非增訂注本。 |
| MR-008 | Work | 經驗痘疹不求人方論 | d59fxsvhg2de ← d59fy0708flt | 原題明列新刊/新刻題為版本冠詞；同一朱棟隆、一卷方論，責任者無增注差異。 |
| MR-009 | Work | 圖像水黃牛經合併大全 | d59fy1h3aqkh ← d59fxquuwc8y | 總目明列圖像水黃牛經大全異名；喻仁與喻傑二人、二卷相同，刻本/石印本分留Book。 |
| MR-010 | Work | 牛痘要法 | d59fxzeyfqbm ← d59fxrtp3v29 | 原題明列刺種牛痘要法異名；同一余楙一卷、無增注責任者，叢編子目是同書收入不同載體。 |
| MR-011 | Work | 延陵弟子紀畧 | d59fxxqdgmwx ← d59fxxqe3400 | 紀畧/紀要在原題明列異名；兩側 author_info 均曹存心撰、吳元善輯，相同二重責任，非另一作者醫案。 |
| MR-012 | Work | 張仲景金匱要畧編注 | d59fxziflw5e ← d59fxunlrzeo | 原題明列沈注金匱要畧為異名，沈明宗、二十四卷同；合併的是同一注本，並非張仲景原典。 |
| MR-013 | Work | 陸清獻公宰嘉訓俗 | d59fxu2cpbsw ← d59fy1xu1zia | 原題明列宰嘉訓俗為異名；同一陸隴其、一卷，差異為作者諡號冠詞。 |
| MR-014 | Work | 張千里醫案 | d59fy0gziku9 ← d59fxtzh2jnk | 原題明列千里醫案異名；張千里、五卷同，沒有另編者或增注層。 |
| MR-015 | Work | 外科百效全書 | d59fxzgh29ds ← d59fxzhaekg0 | 新刻祕授為題名冠詞，原題列為異名；龔居中、四卷及外科內容一致。 |
| MR-016 | Work | 小兒痘疹要訣 | d59fxxc8z20w ← d59fxyp2ocu8 | 原題明列東園痘症要訣異名；吳子揚輯、二卷同，保產痘症合編本僅為收入載體。 |
| MR-017 | Work | 釋音精嚴集 | d59fyexmq5fk ← d59fyew6lipu | 同一釋處觀三卷音義書，原題明列紹興重雕大藏音異名，無異譯者之別。 |
| MR-018 | Work | 外治壽世方初編 | d59fxxa3k7b4 ← d59fy06um5tt | 原題明列外治壽世方異名，鄒存淦輯、四卷同，初編未與續編相混。 |
| MR-020 | Work | 周慎齋三書 | d59fxyoc56o0 ← d59fxyode4u8 | 同一周子幹三卷合輯，先生敬稱有無不改範圍；不是將某一子書併進三書。 |
| MR-021 | Work | 含飴堂知醫必辨 | d59fxsjywwzk ← d59fy0h6p1c0 | 原題明列知醫必辨異名；含飴堂冠詞有無，責任者均李文榮，無續補或注本層。 |
| MR-022 | Book | 大藏治病藥 | 993wfb6juo ← 993wunomps | 同一上圖 instance ID、同一逐項館藏 item、卷數/附錄/版本及全部業務欄位完全相同；僅id、已確認重複work_id、草稿Collection晉升ID不同。 |
| MR-023 | Book | 大藏治病藥 | 993wi5ke0w ← 993wult7gh | 同一上圖 instance ID、同一逐項館藏 item、卷數/附錄/版本及全部業務欄位完全相同；僅id、已確認重複work_id、草稿Collection晉升ID不同。 |
| MR-024 | Book | 新雕洞靈真經 | 993wvk5b7l ← 993yiwhfcx | 同一上圖 instance ID、同一逐項館藏 item、卷數/附錄/版本及全部業務欄位完全相同；僅id、已確認重複work_id、草稿Collection晉升ID不同。 |

## 反證複查與保留

- 《楊忠愍公遺訓／楊椒山先生遺訓》原題同卷，初判可併；追查 Book `9951cgevwg` 發現額外「張承燮輯」且來源 contMap 與題名行不一致，降為待核。
- 《薛氏醫案／薛生白醫案》初判同一薛雪一卷；Book `993j2647i9` 卻有「吳金壽編」而 Work 著錄漏此層，降為待核，先查是否另一選編。
- 《大乘唯識論》《因明正理門論》都有不同漢譯者，不因原作者和題名相同而併。
- 《黃氏畫譜／六言唐詩畫譜》《十竹齋書畫譜／書畫册》是整部與組成部分；括號中的名稱不能一律抽為別名。
- 《集驗良方拔萃》含續補、《性理會通續編》42卷、《焦氏喉科枕祕》附十藥神書、《吳又可瘟疫論》含補遺，均保留待核。

## 整合條件與欄位保留

- `cases.json` 提供 ID、路徑、SHA-256、完整著錄證據、逐欄位裁定和 `machine_decision.set_fields`。各案不可只讀 status 後盲併，須滿足 `apply_prerequisites`。
- indexed_by/emendated_by 要依原順序追加，不能按字串相同去掉一條來源。所有 sources、resources、resource_groups、舊別名、歷史合併帳和原註記須保留；本案原始快照另存 gzip。
- 作者漏項按原始 author_info 補回：何粲、雲龕道人、黃秩模、葉樞、闍那崛多、吳元善。喻傑來源 URL 由另一側有值的 Source 補全，不丟失。
- Book 的三組只在同 instance、全部版本業務欄位一致且 Collection 晉升映射有明文時合；原刻與影印不得合。《新雕洞靈真經》何粲在 Work 作宋、Book 作唐，保留原值並記待核，未據此擅改時代。
- `classification-decisions.json` 指定唯一分類，醫書的叢編載體分類與作品專門內容衝突時採後者，完整來源 section 不刪。
- 已在本地 `book-text-ref/index/texts` 檢查確證 Work 自有文本，沒有命中；但沒有完整 book-text 整理本/輯佚檔快照，**跨庫引用閘未完成，不能聲稱可立即無條件套用**。

## 公開書目交叉參考（輔證，並非每案均有獨立書影）

- [CiNii 經騐四種 BB18166900](https://ci.nii.ac.jp/ncid/BB18166900)：子目列朱棟隆著述的新刋經騐痘疹不求人方論，支持新刊題與經驗四種收入關係。
- [CiNii 四庫術數類叢書 BN08820976](https://ci.nii.ac.jp/ncid/BN08820976?l=en)：第六冊列曾文辿《青囊序》，僅作作者與書名輔證；序/敍異名仍據本庫保存的原始總目著錄。
- [東京大學《吳郡寶翰樓書目》](https://repository.dl.itc.u-tokyo.ac.jp/record/26860/files/ioc164007.pdf)：列喻仁、喻傑《圖像水黃牛經合併大全》二卷，作者與卷數輔證。

## 重跑與續接

1. `scan.py` 產生全庫子部來源快照及同源候選；`candidate-alias.json` 為額外的題名/異名交集候選隊列。
2. `build_cases.py` 重建人工核定案；`check_links.py` 掃全 Book 及本地文本索引；`finalize_review.py` 套用關聯 Book 反證降級、驗 hash、更新統計。
3. 未裁候選繼續按責任者/篇卷/正文起訖逐案研究；不以完成數取代文獻證據。
