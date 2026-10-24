# 修复冯时行／冯当可人物重出

《易论》当前把“冯当可”系到独立人物。本批将该实体合入冯时行，保留原署名和《经义考》名与字次序倒置的异说；不合并《易论》或缙云相关Work。

固定base：`c6dd8356d613fc5614beb88f0a61a3d04cfb069e`。keeper `hixhd2h9bfe9`，loser `hixhd2h9bun9`。2 Entity、1 Work、1官方索引分片；loser原路径留8字段墓碑，keeper新增别称和并条史。keeper既有日期、外部ID、上图来源及说明不变；loser独有说明和全部原值按原owner保存在merges.json，period_basis也署源并入keeper。

身份依据：[《经义考》卷25](https://zh.wikisource.org/wiki/經義考_(四庫全書本)/卷025)同一易论三卷条并列两种名字次序；[《总目》卷158](https://zh.wikisource.org/wiki/四庫全書總目提要/卷158)缙云文集条与地域、官历相合。状元传说等既有争议不作为判同依据，不借本批改写。

## 验证

三仓固定SHA完整归档扫描覆盖714388/563825/190821档；正式唯一活动引用是易论作者ID，草稿仅历史TSV，文本内容和路径零命中。引用扫描逐字节检查常规归档成员，不解压仓内嵌套压缩容器。草稿TSV压缩保存原字节，按原SHA256复验。

独立审查通过；47字段行与最终投影完全匹配；3实际原生文件schema及check_v2均0错误，分类0问题。官方审计T/L/P/R全0；其未传--draft时D=0不作为证据，草稿由完整归档扫描补足。Person的官方L缺项由完整原档、逐字段与独立审查补足。官方index_entry/write_index更新一片；全量builder前后报告完全相同、fatal为空。基线已有79779条索引遗漏和悬空引用，本批未新增、未混入修复。

## 复现

在固定base完整干净checkout中放入本目录：`python .claude/qa/person-feng-alias-2026-10-22/apply.py --apply`，默认不带apply只预检。脚本先验HEAD、三个原档散列及三仓扫描完整性，再原子替换三档；不是旧1876映射。实际执行前仍须确认三仓HEAD未变，变化则刷新扫描。

随后运行本目录verify_fields.py和update_index.py，官方audit-merge-ledger.py（本目录merges.json与上述base）、schema/check_schema.py及check_v2.py（schema-input-paths.txt三档）、scripts/check-classification.py、build/build_derived.py --check-only --text-index 指向经核定的16片文本索引。索引写入使用官方投影/写入函数定点更新，避免混入main既有全库漂移。

`evidence/field-ledger.json`是原研究候选快照；实施以根目录field-ledger.json为准。独立审查明确记录了审计器边界和未采用的争议信息。PR只供审阅，不自动合入main。
