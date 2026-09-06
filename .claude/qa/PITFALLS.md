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
