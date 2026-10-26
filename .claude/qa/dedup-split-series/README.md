# 拆回丛书版次错并的 Book（去重方案部分 6 附）

方案：ai-team `domain/目录与资源/设计/2026-10-正式库全面去重方案/部分6-Collection丛书与文本迁移.md` 第四节第 1 条。

## 成因
草稿库提交 `449d40913f2`（2026-10-19「跨部查重 Book 层：同 Work 同版本重复 Book 并条」）把各叢書版次里的同一子目（同 Work、`edition` 同为空或同写「道光本」之类）当成同版本并成一条：被并者留草稿墓碑，keeper 随后升格。于是一个正式 Book 同时带着几个丛书版次（或几部不同丛书）的馆藏、著录、源记录和 `contained_in`。一个 Book 是一个具体版本，应拆。

## 口径
- 只拆「被并者所挂 Collection（按 promotions 译成正式 id）与 keeper 不同」的；与 keeper 同挂一个 Collection 的继续并着。
- 同一组里挂同一 Collection 的几个被并者（同一丛书版次的同一子目、源记录不同）合成一个新 Book，其余草稿 `merged_into` 新 Book，新 Book 记 `merged_from`。
- **不拆**：一侧本来没有 Collection 的组（抽检发现多是总目「叢編之屬」单条与该丛书子目，实为同一版本，10-19 并对了）；同 Work 已有别的活 Book 挂同一 Collection、同题同版本名 Collection 或同一实物的跨源 Collection（文淵閣 8rldp1yeqrk0≡8rlb6yi1ecqo、摛藻堂 8rldo48qtsld≡8rlb6yk66qdc）的组（新建会重复，交部分 5）。这些组都记在各批 `splits.json` 的 `problems`。
- 新 Book＝被并草稿并前原记录（取自 `449d40913f2^`），草稿 id 按 promotions 译成正式 id，`work_id` 取 keeper 现值，`revision` 1.0.0，ai_note 加来历；promotions 加「被并草稿 → 新 Book」。
- keeper 做减法：只删来自被并者的 provenance／indexed_by／sources／contained_in／merged_from 项，10-19 后别人的改动原样保留；keeper 自己原挂、升格时因 Collection 未升格而没带进来的 Collection 补回。10-19 查重线原说明保留，另加一行拆分说明。`revision` 升 major（schema/common.md：同 Work 下并／拆 Book）。
- 草稿库：被并草稿改成已升格残档（只留 schema_version／id／type／title），keeper 草稿残档的 `merged_from` 去掉拆出者。

## 工具
`split.py --draft ../book-index-draft [--limit N] [--only 文件] [--skip 文件] --out <批目录> [--apply]`：乾跑默认，写 `plan.json`（全记录）与 `splits.json`（台账）；`--apply` 改两库、加 promotions、给新 Book 写 index/books 条目。重跑是幂等的：已拆的被并草稿已在 promotions 里，自动跳过。PR 只入 `splits.json`，`plan.json` 太大不入库。

## 规模（main 204dea4eb3 重算）
449d409 里被并 4,889 条、keeper 3,665 条。可拆 2,735 组、新建 3,755 个 Book；不拆或跳过：同 Collection 或都无 668、一侧无 Collection 59、同 Work 已有同丛书 Book 200、keeper 未升格 1。
另有约 385 个非查重线来源（E/F/G 道版本补录把多个源记录合成一个 Book）的跨版次多挂，不在本工具范围，另串研究。

## 抽检（独立子 agent）
- 第一轮 20 组判错 5 组（25%），停批：「一侧无 Collection」3 组不该拆、同 Collection 的被并者拆成了两个 2 组。已改口径。
- 第二轮 62 组（22 组落地＋40 组计划）：拆分判断判错 0；落地数据与原记录逐字段一致；新 Book 与跨源旧 Book 同一实物 3 组（文淵閣／摛藻堂两套 Collection），已加跨源等价规则跳过；revision 改 major。

## 批次
- batch-01：968 组、新建 1,000 个 Book（#1280）。
- batch-02：734 组、新建 1,000 个 Book（main a3128d5695 重跑）。
