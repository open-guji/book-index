# 僧道人物：逐字段无损台账与旧污染案续审

固定 main：`c6dd8356d613fc5614beb88f0a61a3d04cfb069e`。本轮是研究审查，未改原生数据、分支或提交。篆玉／释篆玉、唐菩提流志／释菩提流志两组延续原身份确认；新增确认0、实际并条0。另续审旧 PRV-R012，仍 open。`cases.json` 三案均有 supersedes，不能新增计数。本轮有效替代链为 PRV-ASTRA-P007 → PRV-H1900-P007、PRV-ASTRA-H001 → PRV-H1900-H001；原始 PRV-P007／PRV-H001 仅保留为 reviews_case_id／original_case_id，不再作为当前有效替代目标。PRV-R012 → PRV-H1900-R012 不变。

已完成11份定点原档验证（四个候选Entity、四个关联Work、僧肇两Entity及《道行經序》）：旧工作树文件的 Git blob SHA1 与固定main树逐份相同，另记SHA256；不是把旧工作树分支当main。两组8份既有证据的SHA256亦与Astra快照完全一致。7份规则/校验器文件也记录双散列。完整原档见 `source-snapshots.json`。

## 两组台账的关键修正

`candidate-ledger.json` 按官方台账基本形状给出 `merges[].type=people`、keeper、losers、preconditions，并附每个原有及新增字段的before/after、去向及候选完整记录。篆玉18行、唐人19行，共37行。只在研究目录输出，不存在自动原生写入函数。

| 事项 | 篆玉组 | 唐菩提流志组 |
|---|---|---|
| 映射 | hixhd2h9bjck → hixi8u5rf6fx | hixi5eks7m81 → hixhd2h9bsyc |
| 主名 | 釋篆玉 | 菩提流志 |
| 新增别名 | 篆玉／別名，附同人证据说明 | 釋菩提流志／別名，附同人证据说明 |
| 朝代／时代 | 清／qing保留；移入loser period_basis | 唐／sui-tang保留；两侧不同dynasty_basis署源联集 |
| 原说明 | keeper ai_note原文完整保留 | 两侧ai_note原文完整保留，各署源ID |
| 出处 | 上图Source对象逐字段保留，追加《话堕集》卷三原文链接 | 保留所有原字段，追加DILA A001358出处对象 |
| 外部ID | 不新增 | loser cbdb_match=none及cbdb_source原文完整移入，不新增CBDB/Wikidata |
| 审核状态 | unreviewed | unreviewed |

旧Astra候选覆盖集没有处理唐人loser独有 `dynasty_basis=中國古籍總目責任者著錄「唐」`。若仅沿用keeper再覆盖旧方案，此依据会消失。本轮明确将两侧basis分别署源保留；这不是同名或同值的冗余丢弃。

篆玉候选旧ai_note所引卷一URL与复核采用卷三不一致；本轮候选说明和description.sources均用卷三。卷一OCR「篆王」不得成为异名。本文与候选不新称籍贯、生卒、让山别号；三卷／六卷、《话堕二集》《话堕三集》继续保留为各自Work。

两组别名采用完整对象稳定去重，不只按name去重；有同名异type、note、source时不能丢信息。description.sources沿用合法Source对象`{name,type,details}`，不发明顶层Entity sources。Work责任者 `name/role/dynasty/source/name_basis` 不随人物ID机械改写而改；唐人大宝积经 name_basis 内旧建档ID是历史注释，不全局替换。

## 墓碑、历史与管理字段

每个loser只留8字段：`schema_version,id,type,subtype,primary_name,merged_into,revision,revised_at`，保持原路径、ID、原主名；不删档，不额外保留description/ai_note/dynasty/external_ids/updated_at。被移出的全部原值已存完整快照和字段台账，独有知识移入keeper。

keeper新增一条`merged_in`，明确loser ID及primary_name、at、by、rule、why。当前四Entity均无旧merged_in或merge_history；生成逻辑仍会联集旧事件原对象，历史ID不改写，不伪造merge_history。新事件使用Entity专有primary_name，不用Work的title替代。

候选keeper和墓碑revision设为1.1.0，因为并条内容、别名与事件属于知识变更；候选日期2026-10-22只是当日计划值，实际执行须重验日期及版本。旧revision/revised_at/updated_at全部归档；keeper既有updated_at在候选保留，执行时由项目存档流程维护实际修改时刻，不能把loser旧时刻冒作keeper本次修改时间。只改其他Work的结构化entity_id属于机械改指，依schema/common.md不bump。

旧建档说明「著录2处」「本人所系1部」「≥3部」按原文保留，并追加它们是建档历史、不是本轮扫描结论的解释。禁止为使叙述看似一致而重写历史数字。

## 正式校验器的实际边界

已读main的schema/common.md、schema/entity/_common.md、JSON schema、audit-merge-ledger.py、check-duplicate-audit.py及2026-10-21正式并条报告。

1. `audit-merge-ledger.py` 的T检查覆盖墓碑和keeper并入史，P/R/D覆盖promotions、原生引用及可选草稿；**L检查只分work/book，没有人物独有字段无损检查**。因此人物L=0不足以证明无损，本轮37行台账和原文保留检查必须另行复验。
2. `check-duplicate-audit.py` 硬编码2026-10-21历史merges.json。直接运行只能证明旧批次，不能给本轮两组背书；更不得误用已废弃1876映射。新批次必须绑定本次实际台账，检查全量非空book-text索引及原生引用。
3. 官方校验必须对真实修改路径运行，Git路径不转义。只读预检、内存候选JSON、草稿研究台账均不能冒称真实数据写后校验通过。
4. 本轮原字段覆盖、原ai_note、basis、sources保留以及墓碑8字段的断言全部通过。尝试独立jsonschema检查时当前默认Python缺jsonschema，未进行schema验证；不得计为通过。原生schema/check_v2、classification、builder尚未运行。

## 引用门槛与根会话结果

本路遵照分工未重复扫描全库。根会话报告正式库714388文件已扫描，四组人物中仅三处Work作者字段需改，含本组篆玉一处；唐loser零活动引用。草稿库563825文件仅两历史TSV命中、无活动JSON引用。这些是根会话集中扫描的报告，完整证据及book-text结论需由根会话关联；本路不将已知局部引用数写作自行完成的全库结论。

真正可执行前仍需：重验固定main及逐文件前置hash；把根正式库全部型别/promotions/草稿/book-text证据纳入台账；确认活动入边清零而历史ID保留；运行独立字段台账审计、官方audit-merge-ledger、真实变更路径schema/check_v2、分类和官方builder；以完整真实16分片book-text索引做文本ID保护；与基线比较既有失败，不能修改测试规避。北魏菩提流支／菩提留支严格不在任何映射内。

## 旧open案 PRV-R012：具体污染边界

固定main《道行經序》`d59f27vzh4oz`仍有结构化作者僧肇、东晋、hixhd2h9bixi。原目录summary只剩「道行經序一卷 僧 。謹按見《隋眾經目錄》。」；ai_note记2026-08-08由「僧」补「僧肇」，同时承认归属存疑、另有道安同题序。这说明当前结构化作者与description所作断言，不能由这条残缺目录文字独立推出。

下一步修复应同时覆盖authors[0]的name/entity_id/dynasty/dynasty_basis、description.text、追加纠正ai_note及各层dynasty_basis/period_basis。不能只机械换ID，让其余派生叙述继续声称僧肇。loss_status来自机读旧描述，作者校正不能直接推出存佚状态。

本轮网页检索得到隋法经《众经目录》僧叡条的索引线索，但SAT及deerpark已打开页面的可检索正文没有定位到该句，CBETA直链不可达、NCU PDF取回超时。因此未把搜索摘要升级为新原文证据，也不据此立即改挂僧叡。待丁国钧原页残字、对应隋目原条和候选Entity身份全部核定，才另作污染修复；道安同题序不因题名相同而并入。此案保持open，旧人物异称证据不等于污染已清。
