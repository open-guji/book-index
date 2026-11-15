# wake-d：和刻本日本館藏專項（shard3，156 Book／113 Work）

用 NDL Search OpenSearch 與 CiNii Books 為 `shard3.json` 的 156 個日本刻本／鈔本 Book 補日本館藏、並補建庫內缺的日本刊本。

- 補挂：20 個既有 Book（`provenance` 追加日本所藏館，不動原中國館藏；revision patch+1，ai_note 追加依據）。
- 新建：13 個 Book（醫法明鑑 5、孝經刊誤 3、易學啓蒙 5），同 Work 並列另立者在 ai_note 互記 id。機器號 wake-d＝1939。
- 台賬 `ledger.tsv`（156 行＋新建 13 行）；未建候選見 `TODO.tsv`。
- 判準：題名（異體字歸一）＋責任者＋刊年＋刊者／書肆／刊記（CiNii 注記或見返）俱合才補挂；年份合而刊者缺載者（大戴禮記正德六年本、大戴禮記補注）在 ai_note 註明。所藏館與索書號錄自 CiNii 書誌頁；NDL 自藏（R100000002）、早稻田（R000000050）記錄取自 NDL Search。
- 不補：1912 後影印／排印本；日本鈔本無法確認同一抄本者；已有日本館藏者；題名同而刊者年份對不上者。
- 腳本：`ndl.py`（查詢）、`survey_d.py`（批量檢索，結果 `cache_d.json`）、`view.py`（審閱）、`hold.py`（所藏館解析）、`decisions_d.py`（決策）、`build_d.py`（寫檔）。
