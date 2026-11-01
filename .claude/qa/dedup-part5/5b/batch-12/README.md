# U1-b：拆分后重跑 5a/5b/5d（2026-11-01，main 11c44b9c6d）

三个批次合在一个 PR：
- `5a/batch-03`：同 Work＋同源记录，字段仅 contained_in 不同的纯重复 2 对（點蒼山人詩鈔、頤道堂詩選），并入有 contained_in 的一侧。其余 8 组同源集合前次已判（不同责任者／版本项，或属不同丛书版次），不动。5d（双晋升）仍表现为同源重复，promotions 无一对多（check_promo_dup 0）。
- `5f-gugong/batch-02`：故宫同版遗留 62 组（脚本 5f-gugong/merge_volumes.py）。这些此前因 ai_note 带「GUJI-533 同版核对并入」被 batch-01 排除；按 00 文件第七节「Book＝版本」应并。
- `5b/batch-12`（本批，脚本 5c/merge_books.py）：拆分出的 Book（edition 已清空，版本项在 indexed_by[].summary 第三段）与同 Work 原有 Book 版本项相同的 137 组。

普查：全库 403,157 个 live Book；以版本项（indexed_by 摘要第三段）为键，含拆分 Book 的同版本项组 1,129。其中 468 组同源自一个原 Book（按丛书名＋版本项分得的，口径设计内不并）；mixed 的具体版本项 272 → 剔卷数／measure／题名／责任者矛盾 → 候选 177；故宫同版遗留 124。
复核：7 个独立子 agent 逐组读全文，SAME 232（故宫 73、拆分后 159）。独立盲检抽 70 组：62 SAME、8 UNSURE，均为只有年代无刊刻者、或只有堂号无年代的泛版本项（异质 11%，超 3%）→ 收紧口径：拆分后批只并「版本项含刊刻者＋年代」或「同名丛书本（四庫全書本除外）」，故宫批只并有具体年份的非抄稿本；剔除后重判的 8 组全部落在被剔除一侧，保留的 199 组其余未抽到异质。
不并（登记）：DIFF／UNSURE 及被口径剔除的共约 110 组，各子 agent 理由在 verdict 表（未入库，见 ai-team 记录）；Q1-010 等证据弱的 6 组、含 Book.lineage 的 欽定四庫全書總目 一组也不并。
门禁：check_v2 ERROR 0；check-classification 0；check_promo_dup 0；audit-merge-ledger T／L／R／D 0（P 项为三批互相改指，已核对均指向本批 keeper）；census --strict 退出 0。
