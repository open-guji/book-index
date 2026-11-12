# L4 目录书拆分（志书 → indexed_by）

把 book-text 里已有转录的目录书拆成条目，匹配到库内 Work，写 `indexed_by`（只写 Work 侧，不写 book-text、不新建 Work）。

- 用法：`python3 split.py junzhai|suichu|wenyuan [--apply]`（先不加 `--apply` 乾跑，台账落到 `$SC/<书>-ledger.tsv`）；`audit.py <书> <A|B|C|N> <n>` 随机抽样看匹配对不对。
- 前置：`$SC/idx.pkl`（全库 Work 题名／作者／时代索引，脚本见 PR 说明，约 40 秒生成）；book-text 稀疏检出 `Work/**`。
- 分档：A 作者吻合且朝代不晚于志书；B 无撰人时，题名全库唯一、≥4 字、已有≥2 处别的著录、朝代已知且不晚于志书；C 题名同但撰人不合或候选多（不写，进人核清单）；N 无同题（新建候选，不写）。
- 保序、幂等（同 source+title_info 已有不重写）；保持原文件缩进，只增不改。
- 新增一本目录书：在 `BOOKS` 加一行，写一个 `parse_<书>`（条目 = 类目、题名、卷数、提要、撰人原文）。
