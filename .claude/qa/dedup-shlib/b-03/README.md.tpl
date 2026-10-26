# 去重细拆「上图-并」第 3 批：全国漢籍 S_MULTI 线索（@@N@@ 组）

基线 main `@@BASE@@`。线索来源：book_index_json `library_data/_匹配/全国漢籍/A5-研究-20261025/组级表.tsv` 中 top_code=S_MULTI 的 2,782 条组记录、729 个候选组合（全国漢籍 DB 同一题名＋责任者记录过闸对到正式库 2 个以上 Work）。在现库重算：729 组合对应 2,165 个在世 Work；剔除已判、已互链、方志、族谱、叢書子目（约 880 对）、4a/4b 候选、与 3a-2丁／3a-3／3b-0 等单元候选或台账同行出现的对，同著者同题（或仅异体）候选余 75 对，逐对过目后取 65 组。

本批口径：漢籍 DB 同一记录指向＋题名只差异体／俗字（㑹會、㫖旨、畧略、襍雜）／冠称（如「宋儒文肅公黃勉齋先生文集」即勉齋集，著录自注）＋首位责任者同一（同 entity 或录名脱字／字号）＋卷数相同、差≤1 或一侧缺。剔除：注箋与原书（水經注箋）、续编（四書釋地又續）、合刻全集（袁中郎十集）、著者不同（五車韻瑞 凌稚隆／凌以棟）、方志（衛藏通志，归方志-并）、多译者混记录（金剛般若）等，登记 `dedup-judged/上图-并.tsv`。

工具与第 1、2 批同（`../apply_shlib.py` → postfix_common → update_index → fix_draft ＋ `../fix_draft_related.py`，草稿库另开 PR）。

@@TABLE@@

抽检：见 `抽检.md`。

验证：audit-merge-ledger（--draft 草稿库已同步）T/L/P/R/D 全 0；check_v2（@@NF@@ 檔）、check-classification、check_promo_dup、check-duplicate-audit、build_derived --check-only 自检全 0。回滚：revert 本 PR 及草稿库对应 PR。
