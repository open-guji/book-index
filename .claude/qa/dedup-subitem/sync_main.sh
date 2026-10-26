#!/bin/bash
# 本批分支与 main 同步：撞了他线改过的 Work 的组整组撤出（drop_groups.py，恢复原样不手解），再合 main；
# 余下冲突（他线改的关联 Work、index、promotions）取 main 版，fix_tomb_refs 改指墓碑引用，post.sh 重刷 index 并跑门禁。
# 用法：sync_main.sh <批次目录>
set -e
B=$1
git fetch -q origin main
MB=$(git merge-base HEAD origin/main)
C=$(git merge-tree --write-tree --name-only HEAD origin/main 2>/dev/null | grep '^CONFLICT' | sed 's/.*Merge conflict in //' || true)
[ -z "$C" ] && { echo 无冲突; git merge -q --no-edit origin/main; exit 0; }
IDS=$(printf "%s\n" "$C" | python3 .claude/qa/dedup-subitem/conflict_ids.py $B $MB)
[ -n "$IDS" ] && python3 .claude/qa/dedup-subitem/drop_groups.py $B $MB $IDS && git add -A && git commit -qm "子目-甲1：撤出与他线撞车的组" -m "Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01KkP9NxgDPHhn6JrmtZvRRD"
git merge --no-edit origin/main >/dev/null 2>&1 || true
for f in $(git -c core.quotePath=false diff --name-only --diff-filter=U); do git checkout --theirs -- "$f"; git add -- "$f"; done
python3 .claude/qa/fix_tomb_refs.py --apply | tail -1
git add -A && git commit -qm "合入 main（冲突取 main 版，fix_tomb_refs 改指墓碑引用）" -m "Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01KkP9NxgDPHhn6JrmtZvRRD"
