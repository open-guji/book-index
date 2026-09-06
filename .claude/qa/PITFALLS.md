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
