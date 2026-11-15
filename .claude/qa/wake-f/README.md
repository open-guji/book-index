# wake-f（shard5，和刻本日本館藏專項）
- 範圍：shard5.json 144 條，涉 116 個題名。NDL OpenSearch 題名檢索 → 逐條抓 NDL 書目頁／CiNii NCID 頁取館藏與索書號 → `apply.py` 寫入。
- 結果：補挂 29 條（provenance 追加日本館藏，不動原有中國館藏）；新建 14 條日本刊本 Book；1 條互鏈（99524ke9ds，疑同版但另立）；其餘見 ledger.tsv（無對應／存疑）。
- 判準：同題＋同責任者＋同刊年（＋刊者）。刊者未寫者只憑刊年，已在 ai_note 說明（988g23w2rs、988g1ztzpg 較弱）。
- 經驗：NDL OpenSearch 對書名多的作品 cnt=40 截斷；R100000136=CiNii 古籍記錄（每 NCID 通常一館），R100000002=國會漢籍，R000000050=早大；CiNii 頁取「大学図書館所蔵」段即得館與索書號。並發多車道時 NDL 易 429。
