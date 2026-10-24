# 去重确认案实施 第 1 批：22 组人物（本名／字／号／异写）

基线 main `7d51c87f32ae5e5b2fb8809bb14d0744f4572cbd`。依据：`/mnt/project-files/总目/去重研究/expanded-duplicate-audit-2026-10-22/` 的确认案（163 案，累计口径见 current-rollup.json），逐案证据见各路 cases.json；判同口径见 `.claude/qa/正式库并条审查规则.md`。

做法：`../apply_batch.py batch.json --apply`（复用 `entity_merge.py`：作者引用改指 keeper、别称并入、被并者留墓碑、keeper 记 `merged_in`；另把被并者名补进 keeper 别称）；`../update_index.py` 只刷新受影响条目的 index 分片。台账 `merges.json`（含前置 sha256）。

朝代复核（人物并条须过朝代＋著作领域；著作领域见各案证据）：

| 案 | 保留 | 被并（朝代） |
|---|---|---|
| PNA-R001 | 吳任臣（清） | 吳志伊（清） |
| PNA-R002 | 金人瑞（清） | 金聖嘆（清）、金聖歎（清） |
| PNA-R003 | 李寶嘉（清） | 李伯元（清） |
| PNA-R004 | 范梈（元） | 范德機（元） |
| PNA-R005 | 劉知幾（唐） | 劉子玄（唐） |
| PNA-R006 | 李攀龍（明） | 李于鱗（明） |
| PNA-R007 | 惲格（清） | 惲壽平（清） |
| PNA-R008 | 程大約（明） | 程君房（明） |
| PNA-R009 | 夏侯尚玄（元） | 夏侯文卿（元） |
| PNA-R012 | 莊綽（北宋） | 莊季裕（趙宋） |
| PNA-R013 | 史堪（北宋） | 史載之（趙宋） |
| PNA-R014 | 陸德明（隋唐） | 陸元朗（唐） |
| PRV-R001 | 僧叡（東晉） | 姚秦釋僧叡（晉）、釋僧叡（晉） |
| PRV-R002 | 支遁（東晉） | 釋支遁（東晉） |
| PRV-R003 | 釋契嵩（北宋） | 契嵩（—）、僧契嵩（—） |
| PRV-R004 | 釋宗泐（明） | 宗泐（明） |
| PRV-R005 | 義淨（唐） | 釋義淨（唐） |
| PRV-R006 | 釋皎然（唐） | 皎然（唐） |
| PRV-R007 | 徐弘祖（明） | 徐宏祖（明） |
| PRV-R008 | 陳致虛（元） | 陳觀吾（元） |
| PRV-R009 | 釋袾宏（明） | 祩宏（明）、釋祩宏（明）、袾宏（明） |
| PRV-R010 | 張三丰（明） | 張全一（明） |

验证：`scripts/audit-merge-ledger.py --draft ../book-index-draft` T/L/P/R/D 全 0；`check_v2.py` ERROR 0；`check-classification.py` 0；`check_promo_dup.py` 0。本批不改 Work 内容，只改作者 entity_id 指向。
