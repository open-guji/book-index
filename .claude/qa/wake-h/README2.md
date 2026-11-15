# wake-h 第二輪：補庫內缺失的日本版本（shard7，136 個 Work）

方法：對分片內 136 個 Work 逐一以 NDL OpenSearch（`title=`＋首位責任者，`until=1912`，cnt=50）查日本館藏目錄，僅取「題名與 Work 題名等同（異體字歸一）、1868 年以前、有出版者與刊年」的記錄（`cand2.py`），再與庫內該 Work 下已有 Book 的版本名逐一比對查重；入選條目取 NDL 書目頁（`pg.py`）確認出版者、年、刊寫性質，並用 CiNii Books（`ci.py`）取同版各校館藏與索書號。新建由 `build2.py` 生成（鑄號用 `mintid` 車道 wake-h）。

- 新建 Book 15 條（見 ledger2.tsv），每條附 NDL／CiNii 書目頁為 sources 與 provenance.source。
- 未建者及原因見 TODO2.tsv（疑同版、弱證、通名 Work 噪聲過大等）。
- 口徑：edition 只寫頁面載明的事實；NDL/CiNii 未明言活字或整版者不填 edition_type；以序跋年繫年者 dating.certainty 記 inferred。
- 疑似重複 Work：「齊家寶要」(d59fxw2fw9og) 與「重定齊家寶要」(d59f2malyfpd)，本輪新建的齊家寶要兩條掛在前者（庫內既有日本版也在前者）。
