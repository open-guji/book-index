# 混记录 Work 拆分（ncltw 混书清单＋3a-2丙 混记录对）

来源：`.claude/qa/dedup-ncltw/README.md` 所列混了两部书的 Work，及 `dedup-judged/3a-2丙.tsv` 标「混记录」的 12 对。
做法同 3a-2乙「先拆后并」：逐 Work 按书分组，留一组在原 Work，其余组新建 Work 或并入已有的同书 Work；拆后成同一书的整条 Work 再并（墓碑）。

- `plan.json`：方案（13 Work）。`split_works.py` 抄自 `dedup-3a2yi-split/`，另按 Book 文件补齐 index/books 缺的新近 Book（既有索引漂移）。
- `apply_mix.py`：整 Work 并 Work（apply_batch，署名 A11-去重混记录拆分）。
- `out/`：`splits.json`（拆分台账）、`batch-whole.json`、`merges.json`。

结果（2026-10-26）：拆 13 Work（萬里海防圖論、歷代三寶記、晉朝雜事、通易象論、儀禮節要、夷堅志、唐書、吳興統記、周易探玄、西山讀書記、樞垣紀略、喪服要記、古文尚書），
新建 9 Work，5 组并入已有 Work，13 Book 改挂；整条并 4 对（d59fy7s3mps1→d59fyh8129z5、d59f2mwhi682→d59f2make8zl、d59f27yzsh6o→d59f27uzku82、d59fyro7l1c1→d59f2hq4in0g）。
复核（独立 agent）19 条对、5 条错，已改：韓詩翼要 d59f23nqsf0j 輯本组混了馬國翰／王謨／王仁俊三家，本批不动；吳興統記、樞垣紀略、古文尚书补上索引缺的 Book。

未做（证据不足或需人工）：金剛經四译本（Book 无法按译者归属）、合刻本诸条、春秋傳 d59f2pzp4bup（无 Book）、周禮（作者著录错）、
周官總義、剿平粵匪方略、六書音均表／六書音韻表、楹書偶錄；晉朝雜事、通易象論拆了但未整条并。
樞垣紀略 d59f2n5ctxxd 另挂一部十六卷 Book 9952qtzo5c，应属另一 Work，待核。
resources／resource_groups 仍留原 Work，未按书分。
