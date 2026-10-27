# 去重细拆单元 新-无责任者余：第3批

基线 main `c59c6e7de4e9409566f8e62191d154d2e1d655a6`。口径：`ai-team/domain/目录与资源/设计/2026-10-正式库全面去重方案/部分4-Work层无责任者与弱证据.md`（4a-B 节）、`细拆-20261026/README.md`、00 文件 Work 节 A 档、`.claude/qa/正式库并条审查规则.md`。

**规则**（`mkbatch_nr.py`）：细拆单元「新-无责任者余」是普查同题组里、非叢書子目、非譜志、至少一侧无责任者的组（一侧有一侧无、全无两类）。每对由子 agent 逐条读 Work／Book 著录判定，只收「同书」且卷数相合、证据属严格清单者：同源（同一源记录、同一目录同一条、同一叢書同一子目）、版本馆藏（同版本名且馆藏重合）、原文自证、辑佚同本、题含作者。脚本再加严：有责任者一侧含編／輯類责任者（证据非辑佚同本）、无责任者一侧有缺字责任者、两侧卷数不合、一条无责任者 Work 判与多处同书、全无组传递不一致，一律改存疑不并。一侧有一侧无：无责任者并入有责任者；全无：并入挂 Book 最多的一条。分立／存疑登记在 `.claude/qa/dedup-judged/新-无责任者余.tsv`。

工具：`apply_4.py`（`../dedup-part4/`，包装 mergework：著录并入、Book.work_id 与引用改指、分类成员改指，被并者留墓碑、keeper 记 merged_in／merged_from）、`postfix_common.py`、`fix_intra.py`、`update_index.py`、`fix_draft.py`。冲突字段保留 keeper 原值，被并值入台账 `retained_alternatives`；被并者原 ai_note／description 存 `loser_original_notes`；互斥分类登记见 `分类互斥登记.tsv`。

| 组 | 保留 | 并入条数 | 保留冲突字段数 | 分类互斥处理 |
|---|---|---:|---:|---:|
| NR-d59fxvleu6td | 周易象考（茹敦和） | 1 | 0 | 1 |
| NR-d59f2gphozy8 | 大學本旨（黎立武） | 1 | 2 | 1 |
| NR-d59fxxds7vup | 南江文鈔（邵晉涵） | 1 | 0 | 0 |
| NR-d59f2oft0k5e | 高適集（高適） | 1 | 2 | 0 |
| NR-d59fxvl63jlt | 易學啓蒙訂疑（董養性） | 1 | 0 | 1 |
| NR-d59f2px6a9ky | 高錫集（高錫） | 1 | 2 | 0 |
| NR-d59f2nn0d3wg | 昌黎詩增注證譌（黃鉞） | 1 | 0 | 0 |
| NR-d59f9nmzwljd | 黃門郎伏偉集（黃門郎伏偉） | 1 | 1 | 0 |
| NR-d59f2gdy84xu | 九經總例（廖氏） | 1 | 0 | 0 |
| NR-d59fygiax69s | 周易黄氏注（黃穎） | 1 | 0 | 1 |
| NR-d59f2nd1eb5s | 大學衍義節略（楊亷） | 1 | 0 | 1 |
| NR-d59f2nf6t5vm | 易指考辨（談綱） | 1 | 1 | 0 |
| NR-d59f2hpreo75 | 歲寒堂詩話（張戒） | 1 | 4 | 0 |
| NR-d59f9nn239c6 | 黃門郎范啓集（黃門郎范啓） | 1 | 1 | 0 |
| NR-d59f9nn2ehvp | 黃門郎王徽之集（黃門郎王徽之） | 1 | 1 | 0 |
| NR-d59fxu4tcni9 | 公羊問答（淩曙） | 1 | 0 | 0 |
| NR-d59fxvlagv7m | 周易黄氏義（黃歇） | 1 | 0 | 1 |
| NR-d59f2htvzmrk | 易數鉤隱圖（劉牧） | 1 | 0 | 0 |
| NR-d59f2q2xv2m9 | 答周官駁難（干寶） | 1 | 3 | 0 |
| NR-d59f9nn2pqf4 | 黃門郎魏遏之集（黃門郎魏遏之） | 1 | 1 | 0 |
| NR-d59f27tuor29 | 發蒙記（束晳） | 1 | 1 | 0 |
| NR-d59f27uvir5s | 秘書郎張委集（秘書郎張委） | 1 | 1 | 0 |
| NR-d59f6emjrifb | 厯法通書（宋魯珍/何士泰） | 1 | 0 | 0 |
| NR-d59fxwf8bawx | 周禮說畧（張嘉玲） | 1 | 0 | 1 |
| NR-d59f2m9u6bcw | 詩傳詩說駁義（毛奇齡） | 1 | 1 | 0 |
| NR-d59f8ii2o002 | 晋安王子懋集（蕭子懋） | 1 | 0 | 0 |
| NR-d59f27uh5u69 | 關內侯傅珉集（關內侯傅珉） | 1 | 1 | 0 |
| NR-d59f2nv3aa69 | 春秋傳彚（董漢䇿） | 1 | 2 | 1 |
| NR-d59f2m9mombk | 書經疏略（張沐） | 1 | 0 | 1 |
| NR-d59fyrmbjbia | 石鼓文音訓考正（馮承輝） | 1 | 3 | 1 |
| NR-d59fxyuh50xt | 緣情手鑒詩格（李洪宣） | 1 | 0 | 0 |
| NR-d59f9nmklywx | 漢晋陽秋（習鑿齒） | 1 | 1 | 0 |
| NR-d59fyjs7i51d | 周易沈氏要畧（沈驎士） | 1 | 0 | 1 |
| NR-d59f2q132a68 | 駁喪服經傳（卜氏） | 1 | 1 | 1 |
| NR-d59f2pxi59ts | 高智周集（高智周） | 1 | 2 | 0 |
| NR-d59f9nn0j2mh | 濟陽內史王曠集（濟陽內史王曠） | 1 | 2 | 0 |
| NR-d59f27xg88hs | 周易窮微論（王弼） | 1 | 3 | 1 |
| NR-d59f28lfmn0m | 春秋微旨（陸淳） | 1 | 1 | 0 |
| NR-d59f28m6sa9v | 高蟾詩（高蟾） | 1 | 0 | 0 |
| NR-d59fy3gqvuv4 | 陰丹内篇（佚名） | 1 | 0 | 1 |
| NR-d59fyjp34qv4 | 贊靈集（佚名） | 1 | 0 | 1 |
| NR-d59fy18hc2dd | 超凡入聖九還七返金液還丹祕訣（佚名） | 1 | 0 | 1 |
| NR-d59f2pxa13pe | 重添校正蜀本書林事類韻會（無責任者） | 1 | 0 | 1 |
| NR-d59fyjazw45d | 通幽訣（佚名） | 1 | 0 | 1 |
| NR-d59fy1asofep | 金丹上乘龍虎交併返還口訣（佚名） | 1 | 0 | 1 |
| NR-d59fy3gv96gw | 陰騭文註（佚名） | 1 | 0 | 1 |
| NR-d59fy1atxdkw | 金丹下手訣（佚名） | 1 | 0 | 1 |
| NR-d59fy1a32yv4 | 高上玉皇本行集經註解（佚名） | 1 | 0 | 1 |
| NR-d59fy1asd6v6 | 金丹祕訣（佚名） | 1 | 0 | 1 |
| NR-d59fy1a1is5c | 高上神霄玉清真王紫書大法（佚名） | 1 | 0 | 1 |
| NR-d59f2pr7u802 | 尚書百篇圗（無責任者） | 1 | 1 | 0 |
| NR-d59f2q05z4sg | 晉詔書黃素制（無責任者） | 1 | 1 | 0 |
| NR-d59fxzp3yg3k | 詩淵（佚名） | 1 | 2 | 1 |
| NR-d59f9nmsq51l | 彭祖經（無責任者） | 1 | 0 | 0 |
| NR-d59f9nmt1dl0 | 赤松子經（無責任者） | 1 | 0 | 0 |
| NR-d59f9nmt1dkz | 易內戒（無責任者） | 1 | 0 | 0 |
| NR-d59fyj7yn20w | 道典論（佚名） | 1 | 0 | 1 |
| NR-d59fy1b21jpd | 金蓬頭口授金丹祕旨（佚名） | 1 | 0 | 1 |

验证：audit-merge-ledger（--draft 草稿库已同步）T/L/P/R/D 全 0；check_v2、check-classification、check_promo_dup、check-duplicate-audit、build_derived --check-only 全 0。抽检见 `抽检.md`。回滚：revert 本 PR。
