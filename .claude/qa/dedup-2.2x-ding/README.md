# 去重方案 2.2续-丁：撞名作者补挂已有人物 Entity（md5(norm_name)%4==3）

脚本沿用 2.2续-乙（baseline.py／linkage.py／pack.py／from_verdicts.py／spot.py），写入用 entity-governance-1025/apply_attach.py（只设 authors[slot].entity_id）。

基线 main e79f0d63465：本份无 entity_id 非佚名作者位 38,581，其中名字命中 live 人物 Entity 的 23,550 位（4,367 个名字）。

## A 档：同书互证（Book 作者位随所属 Work 同名作者位已挂的人物）
- linkage.py 得 4,054 位；剔别名命中而姓不同的 1 位（乙份教训）。
- 独立子 agent 抽检 205 条（5%）：SAME 202、DIFF 1、UNSURE 2（1.5%，低于 3% 停批线）。
  这 3 条都是 Work 层同名位原本就疑似挂错（萬曆順德府志王守誠挂了元人；呂舍人官箴著录作者存疑；得宜本草明抄本与清人王子接时代不合），
  连同同 Work 下同一人物的作者位共 4 位不挂，登记在 台账/A-不挂.jsonl，Work 层勘误另交。
- 实挂 4,049 位，分 3 批（台账/A-1～A-3.jsonl）。

## R 档：逐名复核（其余 3,551 个名字）
子 agent 逐名判 SAME／DIFF／UNSURE，from_verdicts.py 落成清单；朝代冲突的 207 名一律不挂。
