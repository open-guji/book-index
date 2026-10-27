# 新-子目甲余：同名叢書異版次子目余量（全部部類）

第二輪細拆單元（ai-team `domain/目录与资源/设计/2026-10-正式库全面去重方案/细拆-20261026/README.md`），口徑同子目-甲2。

- `cand.py`：子目-甲2 `cand.py` 改為全部部類；`NOAX=1` 不再跳過舊 4a-α 候選清單（4a-α 各部類已收口，餘下未並者可按子目-甲口徑判）。用法：`P4WORK=<目录> python3 ../dedup-part4/load.py`，`scripts/dedup-census.py --whitelist …（全部 dedup-judged） --out $P4WORK/census`，再 `NOAX=1 P4WORK=… python3 cand.py`。
- 基線 main `18969516b0`＋子目异名-經第 2 批：同名叢書子目簇 110；可並 18 簇（A 檔，丛书撰者相同、卷數不矛盾）並入 20 條（`b-01/`，結果 `cand-result.json`）；存疑 466 對登 `../dedup-judged/新-子目甲余.tsv`（同一叢書記錄內同題兩條 56 簇、單字泛稱題名 23、國朝典故朱當㴐／鄧士龍異編 7、卷數差>1 4、首位責任者疑誤字 2）。
- 18 簇逐條人工看過（獨撰類叢書兩版次各一條子目；國朝典故三記錄編者皆朱當㴐）。
- 實施：`mkbatch.py <cand-result.json> b-01 --n 100`、`apply_jiayu.py b-01/batch.json --apply`，善後門禁同 `../dedup-subitem/post.sh`。
