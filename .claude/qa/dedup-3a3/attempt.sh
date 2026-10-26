#!/bin/bash
# 3a-3 出一批并尝试合 main；冲突则丢弃（退出 1）。用法：attempt.sh <批名> <组数> <remaining.json> <工具备份目录>
set -e
N=$1; K=$2; R=$3; KEEP=$4; Q=.claude/qa; D=$Q/dedup-3a3/$N; LOG=$KEEP/../apply-$N.log
git fetch -q origin main && git checkout -q -f -B claude/dedup-3a3-$N origin/main
rm -rf $Q/dedup-3a3 && cp -r $KEEP/dedup-3a3 $Q/
python3 $Q/dedup-3a3/filter_live.py $R $D $K
python3 $Q/dedup-3a3/apply_3a3.py $D/batch.json --apply > $LOG 2>&1 || { tail $LOG; exit 2; }
python3 $Q/dedup-confirmed-163/postfix_common.py $D --apply | tail -1
python3 $Q/dedup-confirmed-163/update_index.py $D | tail -1 | cut -c1-40
G=$(python3 -c "import json;print(len(json.load(open('$D/batch.json'))['groups']))")
python3 $Q/dedup-3a3/mkreadme.py $D "$N（$G 组）"
git add -A . && git commit -qm "去重方案 3a-3：一名／又名自证异题同书 $N（$G 组）

Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01CX4jYWWA3Ke2Xy2rzV3ZtM"
git fetch -q origin main
if ! git merge -q --no-edit origin/main >/dev/null 2>&1; then git -c core.quotePath=false diff --name-only --diff-filter=U | head -5; git merge --abort; echo 冲突; exit 1; fi
echo 已合main
