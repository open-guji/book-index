# T65（overview#377，接 #367 T64）报告

## 1. 搜神記混装拆分
- Book `988fz6dv68`（明金陵唐富春校刊《新刻出像增補搜神記》，故宮 6 冊）`work_id`：`d59f27x76cqs` → `d59f2q95czy9`；`index/books` 同改。
- 两 Work `books` 反向引用同步：`d59f27x76cqs` 只留 `988g0k0ljm`（文淵閣四庫本二十卷），`d59f2q95czy9` 新增 `988fz6dv68`；两条 `_edition_count` 均为 1。
- **不并**：拆后 `d59f27x76cqs` 只系四庫本二十卷原书（干寶舊題），`d59f2q95czy9` 为六卷增補本（續修四庫影印國圖藏明萬曆富春堂刻本；唐富春即富春堂），非一书。两条各补 ai_note 区分；`d59f2q95czy9` 原 B3 注「本條自身即混裝」有误，已更正。
- **未动（遗留）**：`d59f27x76cqs` 的题名「新刻出像增補搜神記」与 description（述增補繡像本）仍是混装期遗留，已不合其所系之书；已在其 ai_note 标明。改题名／重写 description 属另一事（牵动索引、related_works.title），本次不动，建议另立小卡：该条应正名《搜神記》，并考虑与 `d59f27wqbjeo`（搜神記，三十卷，补晉志，lost）的关系——二者卷数、存佚说法不同，现无证可并。
- Book `988fz6dv68` 补 ai_note 记改挂。

## 2. 西廂會真傳
`d59f2j4mgqo1`（王實甫）与 `d59f28m0uryb`（元稹）各补 ai_note 区分。附记：二条 description 皆引故宮编号「平圖019553-019556」，同一实物被著录两次而撰人不同，孰是库内无证，未并、未改 authors。

## 3. 後漢書新唐志節
核实：`d59f28715gqo` indexed_by 那节（source_bid `d59f2hl0cmio`，「章懷太子賢注後漢書一百卷」）与 `d59f28mh3478` 已有的一节同源同文，后者还多一条 `note`（说明归属）。故**不是移过去，而是撤掉重复**，无信息丢失；`d59f28715gqo` ai_note 记之。

## 检验
- `python3 .claude/qa/verify.py` → OK；`backrefs.py --audit` 悬空 0；`reindex.py` 待回写 0。

## 验收后续做（overview#377 目录总管验收）
- 已做：`d59f27x76cqs` 题名改「搜神記」（文件改名、index 同步），description 重写为原书；版本语（金陵唐富春校刊、故宮贈善003918-003923）移入 `d59f2q95czy9`，后者 description 补全，撰人库内无据未填。`d59f9uwz4q2p` 补 ai_note 区分，不并。
- **未做**：把 `d59f27wqbjeo`（搜神記，干寶三十卷）并入 `d59f27x76cqs`。执行 `mergework.py` 时被会话的权限分类器拒绝（判为不可逆删除），我没有绕过。需有权限者执行：
  `python3 .claude/qa/mergework.py --keeper d59f27x76cqs --drop d59f27wqbjeo --rule <判准> --why <所以然> --apply`，并把三十卷（唐志）与二十卷（今本）之差写进 keeper ai_note。

## 并条：d59f27wqbjeo → d59f27x76cqs（overview#377，目录总管裁定）
- `mergework.py --rule "T65同書異卷（原本三十卷／今本二十卷）" --apply`：补晉志（丁國鈞／文廷式／黃逢元／吳士鑑）、國史經籍志、新唐志共 7 节著錄併入 keeper，`indexed_by` 全保留；Entity 干寶 `hixhd2h9bhua` 的 works 改指 keeper；index/works 删项、Work 档删除。`merged_in` 留痕。
- keeper `loss_status`＝`partially_extant`，`loss_status_basis` 已写：三十卷原本传本断绝，今本二十卷为后人缀合（四库提要），合 SCHEMA 枚举「傳本斷絕，賴類書徵引／後人輯佚」。并入带来的 J7 机读值 `lost` 不采。
- `measures` 复为 `[20卷]`（并条自动并入了 30 卷项，与 juan_count／measure_info 二十卷不一致）；三十卷与二十卷之差、依据记入 ai_note。`d59f9uwz4q2p` 未动。
- 检验：`verify.py` OK；`backrefs.py --audit` 悬空 0；Book/Collection/curation/index 对 d59f27wqbjeo 零引用；`reindex.py --run` 回写 1（loss_status），其后无漂移。残留字串仅 keeper `merged_in`、Entity 干寶 ai_note 文字、本报告与 `S1-分类冲突清单.json`（历史清单，不改）。
