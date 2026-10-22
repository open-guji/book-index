# 六路新增案件与未分类队列续接（2026-10-22 T2022）

本批由六个 `gpt-6-astra` / `high` / `fork_turns=none` 子会话完成，各自独占新目录。原生数据没有修改。研究基线是 `c6dd8356d613fc5614beb88f0a61a3d04cfb069e`，先核最新 main；历史第一批1876映射永久禁用，BOOK-0010仍defer，JC-001/JC-007仍hold。

## 计数入口

本目录 `current-rollup.json` 是截至T2022的研究累计；`prior-case-baseline.json` 冻结此前350个有效案件及历史替代关系，用于重复检查。不能把基线350案或本次26案重复加到另一份研究汇总。研究确认不等于数据合并；本次原生合并为0。

此前成果见 [PR #1215](https://github.com/open-guji/book-index/pull/1215)，其T2000批新增52案。此前四个人物数据修复在 [PR #1216](https://github.com/open-guji/book-index/pull/1216)，不属于本批；冯时行／冯当可有其他会话正在独立实施，本批不接管其工作区或宣称完成。

## 六路报告

- [经部](../classics_titles/hourly-20261022T2022/report.md)
- [史部](../history_titles/hourly-20261022T2022/report.md)
- [子部](../masters_titles/hourly-20261022T2022/report.md)
- [集部](../collections_titles/hourly-20261022T2022/report.md)
- [一般人物本名字号](../people_names_aliases/hourly-20261022T2022/report.md)
- [僧道帝王及异体人物](../people_religious_variants/hourly-20261022T2022/report.md)

每案保留判定范围、成员、原值／散列、外部证据及尚未完成的执行门槛。不同来源卷数或抄本范围不以推测消除；污染字段必须独立留痕处理。未实开页面、搜索片段与原典全文明确区分。

## 未分类Work队列

原发现队列198对，涉及177条Work、71个连通候选组，全部仍为unreviewed_candidate。

- 62对的责任人不同且复用馆藏版本摘要，列为优先误报核查；不同名可能是字号，故未自动排除。
- 108对缺少具名责任人，18对有不同具名责任，另10对为具名责任候选；四类互斥。
- 从原始indexed_by.section得到61对的分路线索，137对无此线索。来源章节不等于官方分类成员，未修改任何分类。
- 例如11位作者《易注》形成55条两两候选边；相同馆藏列表并不是同一著作证据。此观察只用于排队，不新增55项分立判断。

`unclassified-routing.json`保留198对的原队列位置、成员、责任、原字段指针、诊断、分路线索和禁止自动合并标记；没有丢弃候选。177份完整原字节压缩保存，逐份与固定main树OID、Git blob SHA1及SHA256核对。

## 验证与复现

`validation.json`给出新旧案件对重叠检查、本轮计数、全部成员原字节核验和六路文件散列。`selected-main-records.json.gz`存本轮成员完整原值。校验范围不包括全类型入边、Book/Collection、promotions、草稿和文本资产迁移，也未运行原生写后schema、分类、builder或正式并条审计，因为本PR没有原生数据变更。

在已恢复发现数据库的环境运行：

```sh
python triage_unclassified.py --repo /path/to/book-index --db /path/to/broad-current.sqlite
python validate_and_rollup.py --repo /path/to/book-index --db /path/to/broad-current.sqlite
```

发现数据库重建脚本及输入检查点在PR #1215的 `broad-discovery-checkpoint-20261022/`；本PR不复制旧提交。triage脚本的输入原队列在同PR的 `broad-census-20261022/`，完整输出与原字节已在本PR保存。统一复现须先恢复这些前置研究目录。

## 下一轮执行顺序

1. 重新检查main和#1215、#1216及冯时行数据PR的实际状态，已完成关系不得重做。
2. 先从本轮具备明确题名证据的格斋、阴阳管见或人物低引用组选择小批，建立全量入边与无损字段台账；身份确认不能跳过范围／污染门槛。
3. 在正式库、升格表、草稿库、完整非空文本索引上检查引用；保留墓碑、来源、别名及历史，官方builder生成索引后再审计并提交。
4. 将198对未分类候选沿原字段分流；无路由线索和不同责任的摘要碰撞优先人工判断。保持与六路cases的成员对去重。
5. 继续使用六个Astra/high独占子目录；疑难留明确下一步。检查点以已推远端为准，禁止假定仍有代理在运行。
