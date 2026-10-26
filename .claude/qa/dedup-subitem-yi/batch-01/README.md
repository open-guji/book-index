# 去重方案子目-乙-并：第 1 批（A／B 档前 100 簇）

基线 main `329cfc54`。判定表 `../judged-07fc66fc.tsv`（子目-乙研究，判据见 ai-team `domain/目录与资源/设计/2026-10-正式库全面去重方案/子目-乙-跨丛书同题子目判据.md`）中 A（同撰人／同源丛书家族／纬书辑者）381 对、B（证据可并）76 对，剔除一侧已被并（4a-α乙 把子目并入单行本、3b-0 等）的对，按对连通后当前余 287 簇；main 并条频繁，分三段提交，本批取按 id 排序的前 **100 簇，并入 116 条**。

- 生成：`../mkbatch_yi.py ../judged-07fc66fc.tsv batch-01 --levels A B --keeper d59fy1cvlc00 d59fyh7uiaki d59fyh7zi39d --first 100`。keeper 取有撰人、indexed_by 多、资源多、id 早者；撰人一侧为误字（晁輔之、孫宗澤）或次位责任者（廖宗濬）的簇强定正字／主撰一侧为 keeper。
- 实施：`../apply_yi.py batch.json --apply`（包装 `../../dedup-confirmed-163/apply_batch.py`：著录并入、Book 改挂、引用与分类成员改指，被并者留墓碑；冲突字段保留 keeper 值，被并值记 `retained_alternatives`；被并者原 ai_note／description 记 `loser_original_notes`）。
- 撰人善后（`postfix-authors.json`）：河南程氏粹言补回程頤、程顥撰；息園舊德錄 胡念修 补挂既有人物。
- 人物：部分 2.3 據误字所建、并后无引用的人物并入正字人物（墓碑）：晁輔之→晁補之、胡念萱→胡念修。黝山紀遊 keeper 撰人汪淮、被并者作江淮（必有一误），保留 keeper，2.3 所建「江淮」人物暂留待核。蘭譜奧法 被并者误作丛书辑者周履靖，保留 keeper 趙時庚。
- 3a 第二轮已剔除本表 815 个 Work（与该串 10-26 约定）。

验证：audit-merge-ledger（--draft）T/L/P/R/D 全 0（Q：被并者 ai_note 未保留 116，原文在台账；首位责任者不同 48，多为一侧缺撰人）；check_v2（336 档）、check-classification、check_promo_dup、check-duplicate-audit、build_derived --check-only 全 0；草稿库无引用。index 定点刷新，跳过既有漂移 22 条。
抽检：此前整批 287 簇版本由独立子 agent 抽 40 簇，同书 40/40、并后数据 40/40 正确（#1435 评论）。

回滚：revert 本 PR。
