# 研-族谱：族谱同题组判定

口径全文：ai-team `domain/目录与资源/设计/2026-10-正式库全面去重方案/研-族谱-族谱同题判定口径.md`（逐对判定全表也在那边 `研-族谱/`）。

要点：一修一个 Work（10-26 定），同族不同修次、同县不同支派都不并；地望（题名前方括号）县级不同即同名异族；真重复只有「同一修被两馆或两批各录一次」——总目版本年份同、卷数同（或一侧缺）、堂号不冲突，纂修人不同不否定（族谱「某某等纂修」常各录一人）。

## 用法

```
python3 scripts/dedup-census.py --out /tmp/census $(for f in .claude/qa/dedup-judged/*.tsv; do echo --whitelist $f; done)
BOOK_INDEX=. python3 .claude/qa/dedup-zupu/zupu_pairs.py /tmp/census/同题组.tsv /tmp/zupu
```

输出 `族谱逐对判定-*.tsv`（C 异地望／S 异修异支／B 候选／D 存疑）与 `族谱-B候选与存疑D-详表-*.tsv`。并条用 `apply_zupu.py <batch.json> [--apply]`（包装 `../dedup-confirmed-163/apply_batch.py`）。

## 20261026/（基线 main e79f0d63）

题名以譜结尾的未判组 1,670：族谱 1,434、年谱 102、其他谱录 129（后两类按普通 Work 口径交 3a／3c／4／子目单元）。族谱 31,663 对：C 23,571、S 4,628、B 候选 29、D 3,434。
不含 B 候选的 1,405 组按生成树登记进 `../dedup-judged/研-族谱.tsv`（4,156 对：C分立 2,504／C异修 1,288／D存疑 364），普查譜类未判 1,670→265。含 B 候选的 29 组并完后补登。
`族谱-多修聚合Work.tsv`：F 道把多条上图记录合成一个的族谱 Work 262 个（混异年份 128、混异堂号 32），反向错并，留给拆回单元。
