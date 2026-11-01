# U3-a 经部串：补挂首位责任者无 entity_id 的 Work（2026-11-01）

脚本由 2.2续-丁（dedup-2.2x-ding）改来：baseline.py 加 `--section 經部`，只取 Work 的 authors[0]，不分份；linkage.py／pack.py／from_verdicts.py 同前（from_verdicts 对 R4 档不再因朝代冲突剔除，因 R4 已由复核员按书与人的对应逐名判过）。写入用 entity-governance-1025/apply_attach.py。

## 基线（main c6ef9e22f6）
經部首位无 entity_id 的 Work 2,117（佚名类 686，有名 1,431）。有名者中：命中 live 人物 1,016 位／416 名；无人物命中 415 位（未处理，见下）。
档：A 同书互证 4 位；R1 唯一同朝 192 名；R2 别名 7、朝代相邻 38、朝代未知 39；R3 多候选 70；R4 朝代冲突 66。

## 流程与数字
- 5 个子 agent 逐名复核（复核提示词.txt），412 名：挂 665 位／181 名；DIFF 69 位、UNSURE 161 位、朝代冲突 10 位不挂（台账/不挂-复核判DIFF或UNSURE.jsonl）。
- 独立抽检 150 条：SAME 139、UNSURE 11（7.3%，超 3% 停批线）。UNSURE 集中于「Entity 仅挂一两部诗文集／硃卷，与经学书无关」。整名剔除 9 名 26 位（台账/不挂-抽检UNSURE名.json）。
- 第二次抽检 150 条（余下 500 位中）：SAME 129、UNSURE 21（要求更严：Entity 已挂作品与本书无关一律 UNSURE）。
- 据此加机械规则：只保留「Entity 已挂作品 ≥5 部，或已挂作品含經部」者；其余 177 位不挂（台账/不挂-Entity单薄.json），待有旁证再补。该规则剔掉抽检中 21 个 UNSURE 里的 18 个；保留者在两次抽检共 205 条中 UNSURE 3（1.5%），DIFF 0。
- 实挂 462 位（台账/经部-1.json），一个 PR。

## 顺带发现（未改）
- 陳鍾英 Entity 生年 1613、籍贯德州疑误；章炳麟 Entity 籍贯「大興」误；張鳳翔 Entity 混了堂邑、洵阳两人；
- Work 作者位朝代误标：鄒之麟标清（应明）、胡思敬标魏（应清）。
- 廖平等「清」著录对 Entity「中華民國」的朝代标注差异致 R4，已按人判。

## 未做
- 无人物命中的 415 位（经部）：需 2.3 流程新建（plan23.py 需 CBDB sqlite，本环境未接 cbdb-archive），多为生僻名，价值低；已列入 ai-team 记录。
