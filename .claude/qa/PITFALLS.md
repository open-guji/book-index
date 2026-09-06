# qa-sweep 坑本（協調者維護，各道每批開工前重讀）

編號永不重用。每條：徵候 → 例 → 判準。來源標 [道名]。
skill 之 13 坑（`hanzhi-curation/SKILL.md`）不重抄，此處只記本輪新得。

## 1. 基準句與實錄相牴 [qin-han]
`period_basis` 作「據 authors[0].dynasty「漢」」而該欄已是「北周」——別道改了撰人之代而未改 period。
例：`d59f24lmz2f8` 七曜本起（→nanbeichao）、`d59f24loj954` 洛中記異（→song）。
判準：scan A 類。**正則錨句首**——後續訂正註記常引原句，不錨定全是假陽性。
實錄為「西漢／東漢」而基準稱「漢」者是分期之陳舊，period 不受影響，低優先；
實錄為他期者是真斷代錯；實錄無此鍵者是引不存在之值為據，改依著錄立據。

## 2. CBDB 卸除只卸其代不改其名 [qin-han]
2026-08-08「CBDB 配對卸除」把 pending_accept 之配對的代、生卒、字號卸了，`primary_name` 仍是那個
清人／明人之名，於是「以後代某人之名，載漢代某人之書」。
例：`hixhd2h9bmoe` 謝廸（明）名下是于吉《太平清領書》。
判準：scan F 類，撰人名不在 entity 之名／別名，且 entity `ai_note` 含「CBDB 配對卸除」。
若該 entity 名下唯本道之書 → 正名（先撞庫）；若庫中已有正主 → 改繫正主。

## 3. 別名單字唯一即繫 [qin-han]
`external_ids.cbdb_source: "minimal_altname_unique: '饒' is alt of '釋祖賢'"`——漢志「臣饒」被繫到
南宋僧。同類：「延年」「孔嘉」皆有明清人以之為字號。
判準：繫之之由若是**單字或二字別名**相合，且 entity 之代與書之代不相交 → 誤繫，解之。
漢志「臣＋單字名」之類本無可繫之人，空即是正解。

## 4. 同名二人共一 entity，回正之際一人隨另一人而移 [qin-han]
「代懸隔者訂正」據名下一書之代正 entity 之代，未察名下尚有他期之書。
例：`hixhd2h9bndu` 何英——明《詩經詳釋》＋漢《漢德春秋》，被整體改為 ming。
判準：scan L 類（孤雁）＋ C 類。動 entity 之代前，先看名下**全部** work 之期分布；
兩期各有據 → 是二人，解其一（哪一條解，看哪一條有 CBDB／生卒／官銜等硬據留下）。

## 5. 著錄語裡的朝代字不可機讀 [qin-han]
三型：姓氏（「秦再思」之秦）、簡稱歧義（五代後漢之「漢」）、抄撮之訛（國史經籍志「漢甄叔遵」）。
判準：凡自 `author_info` 剝朝代者，須以撰人 entity 之代或他志覆驗；單源不足以定代；
**《國史經籍志》尤不足據**（明焦竑抄撮舊目，秦代輪已立此判準）。

## 6. 直接建於 production 之新條，反向繫連寫成 draft 形式之 ID [qin-han]
`1ex…`／`11s…`／`1j9…` 出現在 production 記錄裡即是。
例：HBCC 第八輪（2026-08-27）六條之回指。
判準：scan B／K 類；先在 production 以題名找正主，正向繫連（新條→舊條）通常是對的，反向改繫之。
找不到者是真懸空，記 known-issues，不硬配。

## 7. 題名孤證繫 Book [qin-han]
再造善本 Book 以「題名唯一匹配」掛到已佚之漢書上（明萬曆刻本《古文奇字》掛東漢郭顯卿）。
判準：scan E 類（lost 而有 Book）。Book 之刻年晚於 Work 之亡佚，即同名異書。
歸「再造善本繫 Work 存疑」案，兩造記疑，不逕解。

## 8. 索引分片格式不一 [qin-han]
`index/works/*.json` 多為 indent=2＋末尾換行，但個別分片 indent=1 或無末尾換行。
用 `jio.update_index` 回寫（保留原格式），否則一改一整檔 diff，必撞衝突。

## 9. 合流之後必重掃 [18 號 坑 22]
本輪三度合流各帶進數十條新入之條，其中誤繫者多。每次 `git merge origin/main` 後跑 `verify.py`，
收工前對本道 `scan.py` 再掃一次。

## 10. 併條、改撰人之後，索引與人物回指要同步 [coordinator，合流所見]
2026-09-06 上游《內經》族併條、「C 層清賬」一批：改了 9 條記錄之 period／loss／撰人而索引未回寫，
併掉之 work 仍留在 entity.works 裡（懸空 58→70）。
判準：`verify.py` 之「索引漂移」必為 0；併條時 keeper 之 `merged_in` 要載被併者，
且被併者所繫之 entity.works 改指 keeper。本輪協調者已代修（索引 8 條、去重 2 條）。
另：`d59f28npetc4` 靈樞經記錄頂層 `dynasty` 仍作「唐」（王冰）而 authors[0] 已改史崧（南宋）——
頂層 dynasty 與 authors 相牴，索引取頂層，待該道自正。

## 11. 改撰人名（authors[0].name）要回寫索引之 author [coordinator，合流所見]
索引 works 分片除 period／loss_status／title／subtype 外還載 `author`／`dynasty`／`role`
（取 authors[0]）。改了撰人名而未回寫，`verify.py` 報「works 索引漂移 … author」。
例：`d59f6ep6cf0h` 千金寶鑑 雷伯→雷伯宗。用 `jio.update_index('works', wid, lambda e: e.update({'author': 新名}))`。

## 12. 併書後照 merge_history 改 Entity.works，不看 target 之 authors 指誰，會留單向邊 [entity-cbdb]
source 併入 target 後，把人物之邊改繫 target——若那書併後撰人歸了別人，就成「人指書、書不指人」。
懸空 0、索引漂移 0，verify 照樣綠。例：葉文→《菉竹堂書目》（撰人實葉盛）、丁丙藏→《八千卷樓書目》。
判準：改繫前看 target 之 `authors[].entity_id` 有無本人；有則改繫，已有則去重，無則**摘**並記 ai_note。
`verify.py` 今已加「單向邊」一數，`scan.py` K 類已含此向。

## 13. 「名下之 work 分居兩代之桶」是磁鐵之徵候，不是跨代之證 [ming]
2026-08-25 L5 以「其人名下之 work 同時分居 ming／liao-jin-yuan 諸桶」為確證，把 28 個 entity 之
dynasty 改作「元末明初」——循環論據。例：馮復京（1573–1622）因名下掛了元大德間《昌國州圖志》
（實潼川馮福京撰）而被判元末明初。判準：scan O 類；凡以桶之分布立據者，須以生卒／著錄之字里官歷覆驗。

## 14. 朝代比對不要比字串 [entity-cbdb]
本庫 dynasty 102 種寫法、CBDB 85 個碼位，粒度與寫法俱異（南朝宋／宋(劉)、東漢／後漢）。
按字串比，491 條「衝突」三分之二是假。用 `overview/scripts/cbdb-sync/probe_offline.py` 之
`dynasty_relation`（DYNASTY_SPAN 區間：交疊不報、相隔 60 年內另列、60 年以上才是信號）。
三個名字會騙人的 CBDB 碼位：**dy=52「後漢」是五代後漢**（非東漢）、dy=77「周」是武周、dy=9「吳」是楊吳。

## 15. 繁簡異體不可用 opencc 自動轉 [entity-cbdb]
地名會被過度轉換：范陽→範陽、浮梁→浮樑、鳳台→鳳臺、餘干→餘幹、咸陽→鹹陽。只用顯式表
（`probe_offline.py` 之 ORTHODOX 可寫盤、CHAR_VARIANTS 只作比對）；朴、范、岳兼作姓氏，不收。

## 16. 以 Collection 為著錄來源者本無 source_bid [undated]
國立故宮博物院善本舊籍、二十五史藝文經籍志考補萃編、中國明朝檔案總匯、中華再造善本四者
在庫中只有 Collection 記錄（`8rl…`），無對應之目錄書 Work，故其 220 條 indexed_by 無 bid 是體例非漏填。
`scan.py` N 類已豁免（source 名見於 collections 之 title 者）。資料不動。

## 17. 索引之 dynasty 取記錄頂層 `dynasty`，無則取 authors[0].dynasty [coordinator，覆驗 nanbeichao 所報]
nanbeichao 道以 authors[0].dynasty 比索引得 2,989 條「不符」，其中 2,7xx 條記錄有頂層 `dynasty`
（如《補南北史藝文志》新入之 `d59f9c*` 一族），索引正取自彼，非漂移；真漂移 240 條係
頂層 dynasty 改了而索引未回寫，協調者已以 `reindex.py` 回寫。`verify.py`／`scan.py` M 類今照此規則
比 author／dynasty／role 三欄。改撰人名、改頂層 dynasty 皆須回寫索引（坑 11 之推廣）。

## 18. 《補南北史藝文志》「深覈」寫進 ai_note 的「同指一人」多是假的 [nanbeichao]
2026-09-05 該志入庫之「深覈」步在 163 條 work 之 ai_note 末追加「撰人異稱——本志作「X」而庫中作「Y」，
同指一人」，X 與 Y 全無共字者 102（陸澄／沈約、吴均／蕭方等、蕭巋／沈文阿——末者還編出一段偽考證）。
徵候：X 是該志同類目中鄰行之撰人，像是逐行比對錯了行而把不合寫成「異稱」。同批之「卷數異文」
「撰人跨代」註亦須疑。**害在賬不在數據**：authors／period 多仍對，壞的是留下假的身分斷言，後手據之併
entity 即把兩人併成一人。判準：scan P 類（全庫只此一志有，152 nanbeichao、12 sui-tang）。
處置：不刪原文，於同段後另起一段書其誤並標「作廢」；真者（元帝／蕭繹、蕭統／昭明太子）留。
凡 ai_note 裡他人所寫之「同一人」斷言，併 entity 前一律不採，須自證。

## 19. F 類之容：異體可容、帝號後綴不可容 [coordinator，裁 nanbeichao 所求]
scan F 今以正俗異體表歸一後再比（温／溫、云／雲、舍／捨、冲／沖、吴／吳、隠／隱、禇／褚；只作比對，
禁寫盤，坑 15）。**不容**「著錄名為別名之後綴」（「文帝」之於「宋文帝」）——nanbeichao 道本輪正是
靠不容而抓出五條「文帝」實為簡文帝之誤繫；容之即隱之。帝號、號之屬改走 PROTOCOL 三之 2(d)：
車道在三條件下可為 entity 只增 alt_names，F 自然消。primary_name 之誤（夫裴松之、碌鸞→甄鸞）屬
entity-cbdb 道。

## 20. 撰人 `name` 一律剝役字，役入 `role`，著錄原形入 `name_basis` [coordinator，裁 ming 所求]
2026-08-24「待覈之名逐條裁定」225 名採「name 存著錄原形（陳鐸撰）而 entity 用剝過之名」，
與 skill〈姓名的四種黏連〉「一律剝離」相左，scan H 之 role 一則遂永報之。**今定以 skill 為準**：
`name` 存剝過之名，役（撰／注／編／輯／纂／等）入 `role`，著錄原形寫進 `authors[].name_basis`。
各道自理本期之份（改 name 須回寫索引之 author，坑 11／17）。
邊界：名末之字若本可為名（歐陽**修**、郭慶**傳**、曾異**撰**、王弘**撰**、蕭方**等**）不剝，
先讀著錄原文；剝不準者記 known-issues。scan H 之 role 則已收窄為「撰注編輯纂等」與「上人／居士／道人」。

## 21. 「釋／僧」前綴與名中排行字是常態，不是缺陷 [coordinator，裁 ming／song 所報]
scan H 原以數字一則掃中 1,100 餘條，其中明清人排行字（楊一清、劉三吾、黃式三、尹會一）與
僧道之「釋道安」「僧肇」皆常態，假陽性逾九成。今 H 收窄：數字只報「名以數字起」或「長逾四字」者；
前綴只報著錄語黏連之身分（西洋人／泰西／大學士／太監／官銜）與帝號，不報釋／僧／道士。
全庫 H 1,106 → 298。**教訓**：機械判準立時先抽 30 條看假陽性率，逾五成即須收窄；
掃出之數大不等於缺陷多。

## 22. 「L5 斷代歸一」之「確證」是循環的（entity 側之坑 13） [liaojinyuan]
2026-08-25 遼金元輪把 56 個 entity 之 dynasty 改為「宋末元初」「元末明初」，其 dynasty_basis
末句「確證：其人名下之 work 同時分居 liao-jin-yuan×N 諸桶」——`×N` 是**一桶之內的條數**，
不是分居諸桶。實測 56 個中 28 個名下之 work 只落一桶，確證不成立。已修二例：郭茂倩（北宋
1041–1099，四庫／直齋／書目答問三源作宋，作元者唯《國史經籍志》）、趙順孫（1215–1276，卒於宋亡前）。
判準：scan T 類。**《國史經籍志》《補遼金元藝文志》《元史藝文志》例收宋末諸家入元，其代不足與四庫相抗**
（坑 5 之推廣）。

## 23. period_upper 之 catalog_bound，所引之志須先驗其在 indexed_by 且撰人相及 [liaojinyuan]
兩型：(a) 所引之志根本不在本條 indexed_by（scan S，全庫 5 條）；(b) 志條之撰人與本條撰人判然不同
（同題異書之志條被取作界），例《忠孝錄》元志「元汪逢辰」而界取宋志「趙世繁」。
又一型留了自白：period_basis 稱「上限 X 覆驗不相斥」而 X 實早於 period（scan R，全庫 5 條，
無一假陽性——覆驗方向反了）。

## 24. 宣稱已清而未清 [liaojinyuan]
ai_note 自陳「birth_year=1445 為 CBDB 誤配，清除」而該欄實仍在。**宣稱已做而未做，比沒做更礙事**
——後手讀 ai_note 以為已清，遂據殘值立論。scan W 類。

## 25. 新整理一部志書而未撞題，同一書遂成二條 [weijin]
《補南北史藝文志》一批四見。凡整理新志書入庫，建條之前必以題名（正規化後）撞既有之 work；
撞到者當是補其著錄，不是新建。此與 skill〈改名前先撞庫〉同理，只是方向在「建」而非「改」。
