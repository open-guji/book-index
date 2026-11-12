# L1 续修四库提要（WP-5）

输入：book_index_json `tiyao_data/續四庫總目1931.json`（33,857 条，仅 sort／bookName／summaryPage，无作者）。
流程：`build_idx.py`（全库 Work 压缩索引 works.pkl）→ `match.py`（拆卷数、题名归一〔异体字＋t2s〕、同题候选）→ `tier.py`（分档，出 tier.tsv）→ `near.py`（C 档近似候选，仅作旁证）→ `apply_a.py [--apply]`（A 档追加 indexed_by）。
分档：A＝唯一同题且 Work 为清／民国（或作者朝代为清民国）、卷数不矛盾、部类不矛盾、非四库已收；B＝多候选／复合题名／≤2字／唯一同题但朝代、卷数、部类冲突或缺朝代；C＝无同题。
各脚本在工作目录里读写 pkl（路径写在脚本里，`/home/user/lane/l1`）；apply_a 的 `--root` 指 book-index 仓。
进展与经验：ai-team `domain/目录与资源/设计/2026-11-目录领域总计划-车道/L1.md`。
