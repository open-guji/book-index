# 子目-乙：跨丛书同题子目判定（只读研究）

范围：`dedup-census.py` 同题组中，`subitem_groups.py` 归为「子目但丛书异名」且组内每条都是叢書子目（不含单行本）的组。基线 main 07fc66fc：447 组、616 对。

- `run.sh`：从当前 main 一键重算（普查 → 分类 → 抽信号 → 判定），输出到 `$OUT`。
- `feat.py`：取每条 Work 的题名、撰人、所属丛书、indexed_by。
- `sig.py`：有效撰人（含獨撰类继承 Collection 撰人）、卷数串、总目互见、影印底本信号。
- `judge.py`：规则（同撰人／同源丛书家族／纬书辑者）＋逐组人工判定表 `O`，输出 `judged.tsv`。
- `review.py`：人读稿 `review.txt`（逐组列出两侧丛书、版本、撰人、卷数）。
- `judged-07fc66fc.tsv`：616 对全量判定（A 可并／B 证据可并／B? 待核／C 分立／D 存疑）及依据。

判据与结论见 ai-team `domain/目录与资源/设计/2026-10-正式库全面去重方案/子目-乙-跨丛书同题子目判据.md`。C／D 对已入 `../dedup-judged/子目-乙.tsv`。
