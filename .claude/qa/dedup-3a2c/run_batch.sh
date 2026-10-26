#!/bin/bash
# 用法：run_batch.sh <批次目录> <簇前缀>   在已切到「最新 origin/main 起的分支」上运行
set -e
B=$1; P=$2; R=$(git rev-parse --show-toplevel); cd "$R"
python3 .claude/qa/dedup-3a2c/build_batch.py $B/pairs.tsv $B --cluster-prefix $P
python3 .claude/qa/dedup-3a2c/apply_3a2c.py $B/batch.json --apply > $B/.apply.log 2>&1 || { tail $B/.apply.log; exit 1; }
python3 .claude/qa/dedup-confirmed-163/postfix_common.py $B --apply | tail -2
python3 .claude/qa/dedup-confirmed-163/update_index.py $B | tail -2
python3 .claude/qa/dedup-confirmed-163/fix_draft.py $B/merges.json ../book-index-draft --apply | tail -2
rm -f $B/.apply.log
