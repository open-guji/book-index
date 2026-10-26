# 2.2续-甲：撞名作者补挂（md5(norm_name)%4==0 一份）

基线 main 07fc66fc3b：本份无 entity_id、名字命中人物主名或别名的作者位 27,489（Work 9,423／Book 17,415／Collection 651），4,252 个名字；四份合计 99,723。

- `base.py`：重算本份候选（名字＝人物主名／alt_names，本份按 dedup-census.norm_name 的 md5 取模）。
- `tier.py`、`dyn2.py`：分档；dyn2 是 entity-governance-1025/dyn.py 的扩充版（趙宋、中華民國、宋末元初、十六國等写法，宋与遼金并列）。
- **T1 继承档**：Book 作者位所属 Work 的同名作者位已挂某人物，且该人物的名字含此名 → Book 位挂同一人物。朝代机械冲突者（44 位）不挂。子 agent 抽检 250 条：SAME 246、DIFF 3、UNSURE 1（1.6%，<3%）；4 条错误都来自 Work 层原挂错，见 `抽检-T1-250.tsv`，相关 4 个 Work 的 Book 一律不挂，Work 层误挂另行处理。
- `attach-t1-*.json`：各批挂接清单（apply_attach.py 输入）。
