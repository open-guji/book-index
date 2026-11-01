# U3-a 子部：补挂首位责任者作者实体

范围：Work 未并、`authors[0]` 无 entity_id、非佚名/失譯，且所有 `indexed_by.section` 皆「子部」。基线 main c6ef9e22f6：3,981 个 Work、2,024 个名字（有候选 716 名／1,665 个 Work，无候选约 2,316 个 Work）。余下全是 2.2／2.3 未处理的硬骨头：佛经译者、西学外国译名、官署、撞名未判。

工具：`cand.py`（候选，只读）→ 轨 A：`packA.py` 出包、`审核说明A.md` 交子 agent 逐名判 → 第二审盲复核（只重判一审 SAME）→ `mkattach.py` 取两轮同 eid 的 SAME，剔人工名单 → `entity-governance-1025/apply_attach.py` 挂。轨 B（无候选，新建）：`packB.py`、`审核说明B.md`，见后续 PR。
台账：`台账/`。
