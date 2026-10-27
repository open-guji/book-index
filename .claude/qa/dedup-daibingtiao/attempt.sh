#!/bin/bash
# 新-待並條 出一批并尝试合 main；冲突则丢弃（退出 1）。用法：attempt.sh <批名> <组数> <remaining.json> <工具备份目录> [判定.tsv]
# 判定.tsv 给出时一并改分立／存疑链接的注、写 dedup-judged 登记。
set -e
N=$1; K=$2; R=$3; KEEP=$4; J=$5; Q=.claude/qa; D=$Q/dedup-daibingtiao/$N; LOG=$KEEP/../apply-$N.log
git fetch -q origin main || exit 3; git checkout -q -f -B claude/dedup-daibingtiao-$N origin/main
mkdir -p $Q/dedup-daibingtiao && cp $KEEP/*.py $KEEP/*.sh $KEEP/*.md $Q/dedup-daibingtiao/ 2>/dev/null || true
python3 $Q/dedup-daibingtiao/filter_live.py $R $D $K
python3 $Q/dedup-daibingtiao/apply_dbt.py $D/batch.json --apply > $LOG 2>&1 || { tail $LOG; exit 2; }
python3 $Q/dedup-confirmed-163/postfix_common.py $D --apply | tail -1
python3 $Q/dedup-confirmed-163/update_index.py $D | tail -1 | cut -c1-40
G=$(python3 -c "import json;print(len(json.load(open('$D/batch.json'))['groups']))")
python3 $Q/dedup-daibingtiao/mkreadme.py $D "$N（$G 组）"
if [ -n "$J" ]; then
  cp $J $Q/dedup-daibingtiao/判定.tsv
  python3 $Q/dedup-daibingtiao/apply_notes.py $J --apply | tail -1
  python3 $Q/dedup-daibingtiao/mk_judged.py $J $Q/dedup-judged/新-待並條.tsv
fi
[ -n "$FIX" ] && python3 $FIX
git add -A . && git commit -qm "去重 新-待並條：待並條链接逐条定论 $N（并 $G 组）

Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_018LSz3UtE6nNCB8dFviJmqB"
git fetch -q origin main
if ! git merge -q --no-edit origin/main >/dev/null 2>&1; then git -c core.quotePath=false diff --name-only --diff-filter=U | head -5; git merge --abort; echo 冲突; exit 1; fi
echo 已合main
