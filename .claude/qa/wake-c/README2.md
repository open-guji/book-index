# wake-c 第二輪：和刻本專項新建線（shard2，135 個 Work）

- 做法：對 shard2 全部 135 個 Work 以題名（`title=` ＋ `until=1911`，分頁 3 次）檢索 NDL OpenSearch，取 `publicationPlace=JP` 且 1912 前的記錄（harvest.py → harvest.json）；與 origin/main 全庫該 Work 下既有 Book（books.json）比版本／刊年／刊者查重（cand.py、cand2.py）；候選逐條取 NDL 記錄頁、CiNii NCID 頁核對題名、刊者、年、館藏（detail.py、ncid.py、info.py）；建 Book 用 build2.py（數據在 items2.py）。
- 結果：新建 22 條（初版 24 條，復抽後撤出腳氣方論、後漢書各 1，腳氣方論館藏併入 988g36a9l9） Book（台賬 ledger2.tsv），每條皆有 NDL 或 CiNii 實際館藏與索書號；不確定項進 TODO2.tsv。
- 判準：題名＋刊年＋刊者（書肆）俱見於目錄頁才建；僅年份或書肆為推定（目錄以 [] 標示）的不建；與既有 Book 刊年刊者不同、但可能為同板後印者另立並在 description 互參；影印／排印、近現代人著作不建。
- 門禁：`schema/check_schema.py --paths -` ERROR 0。
- 限制：論語、孟子、詩經等通用大題 NDL 單題名檢索被叢書／國字解淹沒，未深查（見 TODO2.tsv）。
