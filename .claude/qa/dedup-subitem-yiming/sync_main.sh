#!/bin/bash
# 本批分支与 main 同步（沿用 ../dedup-subitem/sync_main.sh 办法）：撞了他线改过的 Work 的组整组撤出
# （drop_groups.py 恢复原样；本批 fix_my_chains 改指过的旧墓碑一并恢复），再合 main；余下冲突取 main 版，fix_tomb_refs 改指墓碑引用。
# 用法：sync_main.sh <批次目录>；之后再跑 fix_my_chains.py 与 ../dedup-subitem/post.sh
set -e
B=$1; Q=.claude/qa/dedup-subitem
git fetch -q --depth=50 origin main
MB=$(git merge-base HEAD origin/main)
C=$(git merge-tree --write-tree --name-only HEAD origin/main 2>/dev/null | grep '^CONFLICT' | sed 's/.*Merge conflict in //' || true)
[ -z "$C" ] && { echo 无冲突; git merge -q --no-edit origin/main; exit 0; }
IDS=$(printf "%s\n" "$C" | python3 $Q/conflict_ids.py $B $MB)
if [ -n "$IDS" ]; then
  LOSERS=$(python3 -c "import json,sys;b=json.load(open('$B/batch.json'));k=set(sys.argv[1:]);print(' '.join(l for g in b['groups'] if k&{g['keeper'],*g['losers']} for l in g['losers']))" $IDS)
  python3 $Q/drop_groups.py $B $MB $IDS
  python3 - $MB $LOSERS <<'PY'
import json, subprocess, sys
mb, losers = sys.argv[1], set(sys.argv[2:])
fs = subprocess.check_output(['git', '-c', 'core.quotePath=false', 'diff', '--name-only', mb, '--', 'Work'], text=True).split()
n = 0
for f in fs:
    try: d = json.loads(subprocess.check_output(['git', 'show', f'{mb}:{f}'], text=True, stderr=subprocess.DEVNULL))
    except Exception: continue
    if d.get('merged_into') in losers:
        subprocess.check_call(['git', 'checkout', mb, '--', f]); n += 1
print('恢复本批改指过的旧墓碑', n)
PY
  git add -A && git commit -qm "新-子目异名：撤出与他线撞车的组" -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01WCV8imboYGcNXmiHAJdcg6"
fi
git merge --no-edit origin/main >/dev/null 2>&1 || true
for f in $(git -c core.quotePath=false diff --name-only --diff-filter=U); do git checkout --theirs -- "$f"; git add -- "$f"; done
python3 .claude/qa/fix_tomb_refs.py --apply | tail -1
git add -A && git commit -qm "合入 main（冲突取 main 版，fix_tomb_refs 改指墓碑引用）" -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01WCV8imboYGcNXmiHAJdcg6"
