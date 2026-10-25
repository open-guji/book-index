# 去重方案部分 2.3：新建缺失作者 Entity

方案见 ai-team 仓 `domain/目录与资源/设计/2026-10-正式库全面去重方案/部分2-作者Entity治理.md`。本目录是脚本与各批台账。

## 用法

```bash
python3 .claude/qa/dedup-part2-3/plan23.py /tmp/p23          # 只读，出 plan.json / held.tsv / stats.json（约 20 秒）
python3 .claude/qa/dedup-part2-3/apply23.py /tmp/p23/plan.json .claude/qa/dedup-part2-3/batch-NN --start S --count N          # 乾跑
python3 .claude/qa/dedup-part2-3/apply23.py /tmp/p23/plan.json .claude/qa/dedup-part2-3/batch-NN --start S --count N --apply  # 写
```

依赖：`pip install opencc`；CBDB 用 open-guji-core/cbdb-archive 的 20260919 版（`--cbdb` 指路径）。
每批都从最新 main 重跑 plan23.py 再 apply（冲突一律重跑，不手解）。id 用 `mintid.py` 车道 `dedup23`（machine 2035）。

## 口径（2026-10-25 重算后修订）

1. **总目 person_uri 不是同人证据。** 实测正式库 Work 作者位 67,137 个名字只对 67,024 个 uri，基本一名一号（唐李賢、明李賢同号；錢選元／清同号）。故不按 uri 聚类，uri 只写进 `description.sources` 作溯源。2.2 串也已弃用 uri（#1252 起）。
2. **聚类单位＝（作者位原名，粗朝代）**。只取作者位自己的 `dynasty`，不拿 Work.dynasty 兜底（次位责任者常与作品异代）。粗朝代：两宋／趙宋并为宋，十六國诸国为一档，外国名单列；朝代互不相邻（相差两档以上）才算不同人。
3. **不建、登记（held.tsv）**：
   - 名字（宽归一：scan.VARIANTS＋繁简＋少数异体）撞到库中任一人物 Entity 的主名／别名（含墓碑）：朝代兼容的归 2.2 补挂；朝代不兼容的也不建（总目著录朝代常被解析器从前一责任者带过来，例「唐□□撰;唐陳運溶輯」），待核。
   - 同名在相邻或未定朝代各有作者位；无朝代而同名另有定代者；异体同名（宽归一相同、原名不同）。
   - CBDB 同名同朝代 ≥2 人且本组 ≥2 个作者位（同名同代多人风险）。
   - 组内 ≥2 个作者位时：硃卷与他书混组；各书最早年代相距逾 80 年；谱牒题名方括号省份不同或刊年相距逾 40 年。
   - 名字等于已有人物的「姓＋字号」（石天基＝石成金）也算撞名。
   - 机构名、某氏（仅姓）、名字含缺字／分隔符／括注、名前粘朝代或国别、名中夹责任方式字或名尾粘「藏／並／等」（解析粘连）。
   - 佚名类占位不计。
4. **CBDB 不写**：首轮抽检 73 个「同名同朝代唯一」的 CBDB 配对错 11 个（15%，多为缙绅录、方志孤条的同名小人物），故本部分一律不写 `cbdb_id`，只在 ai_note 记候选号，留给 2.4 加时地核对后再写。
5. 新 Entity 字段：`primary_name`＝作者位原名；`dynasty`＝组内最常见的著录朝代（原文写法），`dynasty_basis`＝據《中國古籍總目》責任者著錄；`ai_note` 写来源 Work、作者位数、聚合依据与 CBDB 情况；`review.status: unreviewed`。Work 只设 `authors[slot].entity_id`（同 2.2 apply_attach.py）。
6. 不改 index（同 #1258 等 Entity 新建 PR 的做法）。

## 抽检

- spot1（120 组，首版口径）：组内同名异人 3、CBDB 错配 11/73 → 停写 cbdb_id，加硃卷混组与 80 年规则。
- spot2（多位组 80 组，修订后口径）：DIFF 1（左逢原，两地谱）、UNSURE 2 → 加谱牒规则、姓＋字号撞名、名尾粘连规则。异质率 1/80＝1.3%。

## 台账

`batch-NN/created.json`：每个新建 Entity 的 id、路径、名、朝代、cbdb_id、所挂作者位（work_id、path、slot、题名、role）。
回滚：删去该批 Entity 档，并把所列作者位的 `entity_id` 去掉。
