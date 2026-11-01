# U3-a 叢書部（乙份）：首位责任者补挂作者实体（2026-11-01）

范围：Work 未并、authors[0] 无 entity_id、非佚名／失譯，任一 indexed_by.section 以「叢書部」开头。与甲份按 md5(norm_name 的 utf-8)%2 分名字，乙取 1。基线 main 7ac2995a95：乙份 689 个 Work、328 名（有候选 212 名／526 Work；无候选 163 Work）；佚名失譯 230。新建人物车道 `u3a叢乙`（machine 2079）。

工具：cand.py → packA/packB → 子 agent 逐名判（说明 审核说明A/B.md）→ 轨 A 二审盲复核 → mkattach.py／mkplanB.py → apply_attach.py／applyB.py。台账在 `台账/`。

## 数字
- 轨 A：125 名进包（朝代冲突 87 名不进包）。一审 SAME 60／DIFF 24／UNSURE 41；二审盲复核 SAME 36／DIFF 1／UNSURE 23；两轮同 eid 且剔人工名单 33 名／129 个 Work。**再按「Entity 已挂作品≥5 部」只挂 15 名／93 个 Work**，其余 18 名／36 个 Work（候选已挂作品<5 部）不挂，见 `台账/A-held-lt5.json`。
- 轨 B：111 组进包，NEW 89／SKIP 22。宽归一撞名等不建 31 组；再手工剔 11 组（沈祖榮、金江聲、王壬甫、瑞徵：子 agent 自报没把握；呂居仁、姚石甫、王勉夫：疑为字号，应挂已有人物；蓬道人、靜軒居士：别号；孫廷翰、李齊賢：朝代／题名可疑）。新建人物 47 个，挂 49 个 Work。
- 异写截断（祝允→祝允明、劉曾→劉曾騄、戴表、何景、洪應、元董鼎）挂已有人物 15 个 Work；金正煒、燕田融两条推测性强，不挂。
- 合计：挂已有人物 93＋15，新建 47 人挂 49，共 157 个 Work。乙份余约 530 个 Work 未处理（朝代冲突、UNSURE、DIFF、held、SKIP）。

## 说明
- 因叢書子目多为小众书目，轨 A 在 Entity 作品<5 部时子 agent 多凭「同丛书」推断，二审后仍不稳，沿用集部教训直接收紧到≥5 部，未再做 100 条抽检。
- 门禁：check_v2、check_schema、check_promo_dup 0 问题。
