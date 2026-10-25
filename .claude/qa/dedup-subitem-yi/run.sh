#!/bin/sh
# 子目-乙：跨丛书同题子目（组内全是叢書子目、丛书名不同）逐对判定。只读。
# 用法（book-index 根目录）：OUT=/tmp/subitem-yi sh .claude/qa/dedup-subitem-yi/run.sh <ai-team 细拆脚本目录>
set -e
OUT=${OUT:-/tmp/subitem-yi}; export OUT BOOK_INDEX=${BOOK_INDEX:-.}
D=$(dirname "$0"); SUB=${1:?给 ai-team 的 细拆脚本 目录（内含 subitem_groups.py）}
mkdir -p "$OUT/census"
args=""; for f in .claude/qa/dedup-judged/*.tsv; do [ -e "$f" ] && args="$args --whitelist $f"; done
python3 scripts/dedup-census.py $args --out "$OUT/census" > "$OUT/census.txt"
python3 "$SUB/subitem_groups.py" "$OUT/census/同题组.tsv" "$OUT/sub.tsv"
# 「子目但丛书异名」且组内每条都有所属丛书（不含单行本；含单行本的归 4a-α）
awk -F'\t' '$3=="子目但丛书异名" && $6!~/(^\||\|\||\|$)/' "$OUT/sub.tsv" > "$OUT/yi.tsv"
python3 "$D/feat.py" "$OUT/yi.tsv" "$OUT/feat.json"
python3 "$D/sig.py" > "$OUT/sig.txt"
python3 "$D/review.py"
python3 "$D/judge.py"
echo "组数 $(wc -l < "$OUT/yi.tsv")；逐对判定 $OUT/judged.tsv；人读稿 $OUT/review.txt"
