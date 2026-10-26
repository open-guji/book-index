# 去重方案 2.2续-丙：撞名作者补挂已有人物 Entity（md5(norm_name)%4==2）

脚本沿用 2.2续-乙／丁（baseline.py／linkage.py／pack.py／from_verdicts.py／spot.py），写入用 entity-governance-1025/apply_attach.py（只设 authors[slot].entity_id）。

基线 main 1d86693567：本份无 entity_id 非佚名作者位 39,799，其中名字命中 live 人物 Entity 的 25,179 位。

## A 档：同书互证（Book 作者位随所属 Work 同名作者位已挂的人物）
- linkage.py 得 4,428 位；剔别名命中而姓不同的 5 位（黃成→侯峒曾 ×4、西清→項應蓮）。
- 独立子 agent 抽检 220 条（5%）：SAME 219、DIFF 0、UNSURE 1（0.5%，低于 3% 停批线）。
  UNSURE 为《揚雄太玄經校正》紹興先正遺書本的倪燦（候选是錢塘倪燦），该位不挂；Work 层同名位待另核。
  不挂共 6 位，见 台账/A-不挂.jsonl。
- 实挂 4,422 位，分 3 批（台账/A-1～A-3.jsonl）。
- 抽检附带发现的实体重复（黃宗羲 hixi8u5xcotf／hixhd2f8wait、傅恒 hixi8u62chjj／hixhd2h9bcl7、樊騰鳯 hixhd2h9bro0／樊騰鳳 hixhd2h9bjl9）留给人物实体去重。

## R 档：逐名复核
见下一批 PR。
