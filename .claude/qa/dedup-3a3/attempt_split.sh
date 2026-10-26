#!/bin/bash
# 3a-3 先拆后并：从最新 main 拆分＋整并，提交后合 main；冲突则丢弃（退出 1）。用法：attempt_split.sh <批名> <plan.json> <工具备份目录>
set -e
N=$1; PLAN=$2; KEEP=$3; Q=.claude/qa; D=$Q/dedup-3a3/$N; LOG=$KEEP/../apply-$N.log
git fetch -q origin main && git checkout -q -f -B claude/dedup-3a3-$N origin/main
cp -r $KEEP/dedup-3a3/*.py $KEEP/dedup-3a3/*.sh $Q/dedup-3a3/
cp $KEEP/audit-merge-ledger.py scripts/audit-merge-ledger.py
mkdir -p $D && cp $PLAN $D/plan.json
python3 $Q/dedup-3a3/split_works.py --plan $D/plan.json --out $D --apply > $LOG 2>&1 || { tail $LOG; exit 2; }
grep 问题 $LOG
python3 $Q/dedup-3a3/mk_whole.py $D
python3 $Q/dedup-3a3/apply_3a3.py $D/batch.json --apply >> $LOG 2>&1 || { tail $LOG; exit 2; }
python3 $Q/dedup-confirmed-163/postfix_common.py $D --apply | tail -1
python3 $Q/dedup-confirmed-163/update_index.py $D | tail -1 | cut -c1-40
[ -n "$EXTRA" ] && bash $EXTRA $D
G=$(python3 -c "import json;print(len(json.load(open('$D/batch.json'))['groups']))")
python3 $Q/dedup-3a3/mkreadme.py $D "$N（先拆后并，并 $G 组）"
git add -A . && git commit -qm "去重方案 3a-3 先拆后并：$N（拆混入同名别书著录后并 $G 组）

Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01CX4jYWWA3Ke2Xy2rzV3ZtM"
git fetch -q origin main
if ! git merge -q --no-edit origin/main >/dev/null 2>&1; then git -c core.quotePath=false diff --name-only --diff-filter=U | head -5; git merge --abort; echo 冲突; exit 1; fi
echo 已合main
