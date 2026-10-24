# 僧道／帝王称谓／异体人名：Astra 定点复核与两组候选方案

研究日期：2026-10-22。固定 main：`c6dd8356d`。本轮只研究，原生 Entity、Work、Book、Collection、墓碑、索引、分支及提交均未修改。

本轮选择准备最小人物批次：**唐菩提流志／释菩提流志、篆玉／释篆玉**。这两组均属旧已确认案的定点复核，不是新发现，不能再计为新增确认。方案已具备 keeper／loser、逐字段覆核值、前置快照及只读预检脚本；**目前仍为候选，尚未达到可写原生数据的执行门槛**。

## 计数与 main 实际进度

唯一读取旧 `cases-all.json`，再加 `hourly-20261022/cases.json`：有效49案，**33确认／6分立／10待核**，拟被并ID共38个。不得把首批、前缀批、第三批与 cases-all 重计。

本轮四个选定 Entity 均按固定 main 重新读取，SHA256 与旧证据完全相同；两组均仍是两个活动人物条目，**main 尚未实施这两组并条**。本轮新增身份裁决0、新增实际合并0，累计仍33／6／10。全部49案的 main 覆盖状态本轮未完成，不把旧检查点的“尚未应用”推断成最新全量结论。

范围收束后，旧49案读取任务的续跑被自动审查拒绝，理由是超出仅核两案的当前范围并可能触发额外远端对象读取；未恢复或绕过该任务。本报告仅主张实际完成的两案核验。选定原档的最终结果见 `selected-current-snapshots.json`。

## PRV-P007：篆玉／释篆玉

候选映射：`hixhd2h9bjck → hixi8u5rf6fx`。

- 《话堕集》卷三卷端明署“西湖釋篆玉讓山”，是本轮新增的直接署名证据。[卷三原文](https://www.shidianguji.com/zh/book/CADAL02036163/chapter/1lafpp28af1nv)
- 本库《话堕集》`d59f2nqjeozk` 的两项独立目录来源分别记清史稿艺文志“篆玉撰”、中国古籍总目“清释篆玉撰”；与卷端互证，同为清代诗僧。不是单凭删除“释”前缀。
- 旧卷一来源页虽然题头明确署清释篆玉，正文卷端OCR却作“篆王”并缺字。本轮改用卷三完整署名；**篆王不是可新增的异名**。
- 关联研究范围为《话堕集》《话堕二集》《话堕三集》三Work。清史稿记六卷、总目记三卷，二集和三集另立。这是文集范围／版本问题，不影响人物同一，但本方案不合并这些Work或其Book。

字段策略：保留keeper主名“释篆玉”、清／qing、上图来源、原ai_note及unreviewed；加入篆玉别名；补入loser的period_basis。无依据不新增生卒、籍贯或外部ID。原 `updated_at`、revision等管理值保存在完整快照和后续台账，执行时按项目规范更新，不伪装字段原样未变。

预期最小结构化引用改写为《话堕集》现有作者entity_id一处；这只是已知原档范围，**不是全库引用扫描结论**。二集、三集原已指keeper，作者name和role保持原著录。

## PRV-H001：唐菩提流志／释菩提流志

候选映射：`hixi5eks7m81 → hixhd2h9bsyc`。

- DILA A001358 明列唐代，作译目录同时收《大宝积经》和《不空羂索呪心经》，并在《宋高僧传》链接题中直接出现释菩提流志传。[DILA A001358](https://authority.dila.edu.tw/person/search.php?aid=A001358)
- 本库《大宝积经》`d59f28jd0x6w` 的中国古籍总目责任者原文署“唐释菩提流志等译”及“唐释菩提流志译集”；keeper所系书与loser建档所据译作都与权威作译范围相符。
- 北魏菩提流支／菩提留支及其释氏前缀条不在映射内。梵文同为Bodhiruci并非跨时代合并依据。

字段策略：保留菩提流志为主名，释菩提流志作别名；两侧说明逐项署来源保留，保留unreviewed及loser原CBDB未匹配说明。DILA生年为依文献寿数推算，说明内另有异说；不藉并条新增生卒。页面并列两个Wikidata号，**不自动写入或声称等价**。

旧快照仅keeper有《大宝积经》一条Work责任者引用，loser为零；loser建档说明的“三部”不可冒充当前真实引用数。本轮读取该Work用于定点复验，未重新做全库反向引用扫描。

## 可执行的研究交付与实施前置

- `cases.json`：两案复核，均标 `counts_as_new_case: false`，逐案证据、字段风险和pending gates。
- `sources.json`：本轮实际打开的来源及定位，不把搜索摘要当读过全文。
- `selected-current-snapshots.json`：四Entity与四Work的固定main完整记录、旧／新SHA256。
- `candidate-plan.json`：两个映射、逐字段候选覆核值、保留策略及实施顺序；`ready_to_apply: false`。
- `preflight_candidates.py`：只读预检，固定仅这八份源档；不改原生数据。示例：`python preflight_candidates.py --repo /path/to/book-index --ref c6dd8356d`。哈希一致只说明源档未漂移，不代表并条所有门槛通过。

实际实施之前仍须完成：正式库所有结构化入边（含Entity、分类与promotions）、草稿库生产ID／墓碑链及book-text文本元数据引用检查；逐字段无损台账；按schema生成最小墓碑并在keeper联集历史及merged_in。其后运行 `audit-merge-ledger.py`、只喂真实变更路径的 `check_v2.py`、`check-classification.py`、`build_derived.py --check-only`。这些写后测试本轮没有执行，也不声称通过。

原待核污染案仍保持open；本轮没有因为称谓、同名、相同梵文名或相似字形扩大并条范围。
