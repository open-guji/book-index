# wake-c：和刻本日本馆藏专项（shard2，178 條）

- 範圍：shard2.json（178 個日本刻本／鈔本 Book，135 個 Work）。
- 方法：NDL Search OpenSearch 以題名查「和古書・漢籍」及 1912 前記錄，取記錄頁出版者／年／索書號；CiNii 書頁（NCID）取所藏館。同版判準＝同題＋同責任者＋同刊年／刊者；僅題名或僅年份相合不補挂。
- 結果：補挂 30 條（機構 33 項 provenance，皆追加，未改動原有中國館藏；revision patch+1，ai_note 追加依據）；新建 4 條（論語集解箕林山房聚珍版、易簡方文化十四年本與安永七年本、明朝紀事本末弘化三年本）；存疑 16；無對應 132。
- 台賬：`ledger.tsv`；待辦：`TODO.tsv`；腳本：`ndl.py`（帶 429 退避與緩存）、`detail.py`、`ncid.py`、`apply.py`（資料表＋寫檔）。`cache/` 為請求緩存。
- 門禁：`schema/check_schema.py --paths -` ERROR 0。
