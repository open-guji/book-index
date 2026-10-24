# 四組人物執行後獨立審閱

結論：已審範圍未見實質缺陷，可繼續等待官方 after-builder。只讀審閱 merges.json、apply.py、verify_fields.py、11條原生diff及2索引diff；未改原生資料或重跑全庫測試。

11份前置SHA256與before均直接匹配固定base Git原檔，after逐檔匹配工作樹；8位人物原值均在台賬按原owner完整保留，119行字段台賬前後與最終records一致。喻子材獨有長ai_note保留於原owner台賬；菩提流志的ai_note及斷代依據帶owner聯集，CBDB未匹配狀態沒有冒充人物ID；釋篆玉保留既有來源。墓碑保留舊ID與姓名，keeper含別稱及merged_in。

三處Work只有authors.entity_id映射變更，其餘JSON值完全相同，題名、姓名、角色、歷史name_basis及來源均保留。錢／喻兩組索引無變化；另外兩墓碑使index/entities/0、9各刪朝代／period，符合官方投影；墓碑索引條目未刪。

apply.py先對全部11檔作前置雜湊及before校驗，再寫after，可從乾淨指定base重放；索引另由官方builder生成。已套用工作樹不可直接重跑，是前置保護。跨11檔寫入不是整體檔案系統事務，中斷需從base及台賬恢復重放。verify_fields.py為本批窄域斷言，不能替代未來任意合併的通用審核；本輪另獨立驗了before與Git base。

三庫掃描與官方schema／分類／builder由根代理保管，未在此擴域重跑；after-builder仍須通過。
