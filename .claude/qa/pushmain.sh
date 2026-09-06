#!/usr/bin/env bash
# 合流 origin/main 並推 main；索引分片撞衝突則取彼方後以記錄為真回寫（reindex.py）。最多三輪。
# 用法：bash .claude/qa/pushmain.sh [自己的分支名]
set -u
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"; cd "$ROOT"
BR="${1:-$(git rev-parse --abbrev-ref HEAD)}"
for i in 1 2 3; do
  git fetch -q origin main
  if ! git merge -q --no-edit origin/main 2>/dev/null; then
    for f in $(git diff --name-only --diff-filter=U); do
      case "$f" in index/*) git checkout --theirs -- "$f";; *) echo "非索引衝突，取己方：$f"; git checkout --ours -- "$f";; esac
    done
    python3 .claude/qa/reindex.py --run | tail -1
    git add -A && git -c core.editor=true commit -q --no-edit
  fi
  if ! python3 .claude/qa/verify.py | tail -1 | grep -q OK; then echo "VERIFY FAIL — 未推"; python3 .claude/qa/verify.py | head -12; exit 1; fi
  if git push -q origin HEAD:main 2>/dev/null; then git push -q origin "HEAD:$BR" 2>/dev/null; echo "已推 main（第 $i 輪）"; exit 0; fi
  echo "推 main 被拒，重合流（第 $i 輪）"
done
echo "三輪未成"; exit 1
