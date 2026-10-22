# 子部续核（2026-10-22 19:00 批）

固定主线 `c6dd8356d613fc5614beb88f0a61a3d04cfb069e`。已读 PLAN、Astra 三案及该提交《正式库并条审查规则》。本轮深入两个有效既案：`MR-H1900-001 → MR-A001 → MR-012`，`MR-H1900-002 → MR-A002 → MR-046`。分别维持 confirmed、open，均为替代裁决，**新增身份确认0、实际合并0、原生数据修改0**。MR-A003不动，BOOK-0010继续defer；未使用旧1876映射。

## 夢溪筆談：从单纯卷数疑问推进到责任层与挂接范围审查

`d59fxwylng8x`的两份Work著录均写一卷，但它当前承载的Book远超一卷子目。本轮仅按固定main树中题含「夢溪」的Book路径定点读取，找到35条 `work_id=d59fxwylng8x`，全部以原字节Git blob SHA1证明等于固定main，保存SHA256和完整正文。它们包含一卷、二十六卷、补续卷和卷数未载者。**不可继续把这一ID简单称作纯“一卷本”，也不可据此整包并入二十六卷Work。** 这里是有界样本的已知挂接，不声称全库只有35条。

已具体复原两条一卷子目的载体链：

| Book | 源instance | 父Collection | 当前著录 |
|---|---|---|---|
| 994hr7l7nl | 4p4exdbghctw7mad | 8rldot389yx0 | 蒼雪菴日鈔十一種；明朱格抄本；臺灣圖書館 |
| 993yln4etd | wdxz72pncliv7l10 | 8rldo9qhnwua | 待清書屋雜鈔四百九十三種；清同治間管氏稿本；天津圖書館 |

两个Collection均重核main字节。第一条父源确是 `s830ijgc7k0exr0x`，补上上一轮只知源ID、未落到Book的缺口。第二条一卷子目不能与第一条默认为同一摘录：仍须比较目录、首末段和选录范围。Collection中的“朱格”被结构化为抄录者是现有源数据，本文没有独立确认它是人名，也不据此修正版本字段。

直接打开 [CiNii NCID BB13733082](https://ci.nii.ac.jp/ncid/BB13733082)，该馆际目录将沈括著述与林思进补校分列，并列《夢溪筆談補校》为收入子目，所指为东京大学所藏不全抄本。它提供独立的责任层证据，使旧 `merged_in.why` 的“作者异写（别名/同人ID）”不能继续充当判同理由；**并未证明这个日本藏本就是旧被并成员 `1exoli8a3q2v4` 的版本**。

本库上述35条Book中7条原著录出现「（補筆談）清林思進撰」，其版本包括明崇祯四年本、清代刻本及丛书本。例如 `995a5685q8`（源 `fu8e6r63vccj5pqu`）含「二十六卷續筆談一卷補筆談二卷」，责任摘要同时记宋沈括与清林思进。该责任与明代版本的组合本身需要解释；不能将本库“补笔谈撰”与CiNii“补校”无条件等同，也不能把补续责任消成沈括别名。

东京大学OPAC点击返回403，上图 `4p4exdbghctw7mad` 直接访问失败。国学大师相似记录仅搜索摘要，未实开，未计入判定依据；访问状态及证据边界分列于 `external-evidence.json`。固定main树未见文件名含 `1exoli8a3q2v4` 的成员，本轮没有草稿原档或旧并条前正文，不能宣称已复原该成员。

结论仍open。下一步先追该旧成员原档，再区分两条一卷子目、完整本与带补续本的挂接。此轮没有提出把35条Book批量改指的可执行计划。

## 沈注金匱要畧：逐字段与第三条历史的执行前审查

身份confirmed不变。此次实读第三条 `d59fxuzex79d` 墓碑及当前正式库 WORK-0187 台账，二者方向一致：**d59fxuzex79d → d59fxunlrzeo**。该事实解决旧ai_note中“并入”措辞的方向歧义；不是本案 `d59fxunlrzeo → d59fxziflw5e` 已实施。

`field-retention-plan.json`覆盖双方全部15个顶层字段，没有漏项。主要要求：

- 两份indexed_by均保留全文。相同source_bid不构成去重键，原分类、题名、撰/辑注及版本摘要各异。
- 沈明宗“輯注”“撰”两个完整来源责任对象都保留，不按人物名或上图URI去掉角色差异。
- `merged_in`完整保留已吸收第三条的历史对象，再追加本次成员；原ai_note独有信息留在keeper或台账，并另加正确方向说明，不静默改写历史ID。
- 如沿用既定keeper `d59fxziflw5e`，第三条墓碑的存储侧 `merged_into` 也应直接改指它，防止新生两跳链。历史WORK-0187台账不改写；此为未来执行提案，不是已改数据。
- 当前两条Work都无contained_in、resources、description、related_works；这只是这两条原档的字段检查，不代替其他类型出边与反向引用清单。

正式库/草稿/promotions/book-text全引用扫描仍由根代理完成。本目录不生成未经全扫的最终实施台账；当前 `execution_ready=false`。后续执行必须重验前置哈希并跑正式规则要求的T/L/P/R、草稿残留、schema、分类、builder检查。

## 验证与交付范围

`work-records.json`保存5个Work（含第三条墓碑），`mengxi-book-records.json`保存35个Book，`mengxi-collection-records.json`保存2个Collection；全部核对固定main Git blob，快照重建部分另核旧SHA256。`WORK-0187-ledger-extract.json`只摘一组，所列散列针对完整来源台账，明确标注extract_only，不能当成摘录文件散列。`validation.json`记录范围和未跑项目。

`build_evidence.py`只读固定树及候选源字节，只写本目录；它使用旧book-index文件时先算Git blob与main树比照，不把旧工作树当main。没有全库git grep，也没有数据提交、分支或共用文件修改。两案状态不新增累计计数。
