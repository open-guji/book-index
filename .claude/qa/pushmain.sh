#!/usr/bin/env bash
# 合流 origin/main 並推 main；索引分片撞衝突則取彼方後以記錄為真回寫（reindex.py）。最多三輪。
# 用法：bash .claude/qa/pushmain.sh [自己的分支名]
#
# 2026-09-06 修（song 道所報，坑 36）：解衝突迴圈原作 `for f in $(git diff --name-only ...)`，
# 對非 ASCII 檔名踩兩個坑——(1) core.quotePath 預設為真，輸出的是帶引號之八進位跳脫字串
# （"Entity/i/k/j/...-\351\253\230\351\207\214.json"），不是可用之路徑；(2) $(...) 按空白
# 斷詞且不解跳脫。於是 git checkout 找不到檔案而**靜默失敗**（有 set -u 而無 set -e），
# 衝突標記原封未動，後面 git add -A + commit --no-edit 就把 `<<<<<<< HEAD` 提交了下去。
# 今改：quotePath=false ＋ -z NUL 分隔 ＋ while read -d ''（治本），
# 並在提交前檢查衝突標記是否真的清乾淨，未清則中止而非硬提交（防他日重蹈）。
set -u
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"; cd "$ROOT"
BR="${1:-$(git rev-parse --abbrev-ref HEAD)}"

resolve_conflicts() {
  # NUL 分隔且關閉檔名跳脫，中文檔名方能正確取得
  git -c core.quotePath=false diff -z --name-only --diff-filter=U | \
  while IFS= read -r -d '' f; do
    case "$f" in
      index/*) git checkout --theirs -- "$f" || echo "取彼方失敗：$f" >&2 ;;
      *)       echo "非索引衝突，取己方：$f"; git checkout --ours -- "$f" || echo "取己方失敗：$f" >&2 ;;
    esac
  done
  # 顯式驗收：迴圈跑完後不得再有未解之衝突，也不得有衝突標記殘留於工作區
  local left
  left="$(git -c core.quotePath=false diff -z --name-only --diff-filter=U | tr '\0' '\n' | grep -c . || true)"
  if [ "${left:-0}" -ne 0 ]; then
    echo "解衝突未竟，尚餘 $left 檔未解 — 中止，勿硬提交" >&2
    git -c core.quotePath=false diff --name-only --diff-filter=U >&2
    return 1
  fi
  if git grep -lI -e '^<<<<<<< ' -e '^>>>>>>> ' -- '*.json' >/dev/null 2>&1; then
    echo "工作區仍有衝突標記殘留於 JSON — 中止，勿硬提交" >&2
    git grep -lI -e '^<<<<<<< ' -e '^>>>>>>> ' -- '*.json' >&2
    return 1
  fi
  return 0
}

for i in 1 2 3; do
  git fetch -q origin main
  if ! git merge -q --no-edit origin/main 2>/dev/null; then
    resolve_conflicts || { echo "VERIFY FAIL — 解衝突未竟，未推"; exit 1; }
    git add -A && git -c core.editor=true commit -q --no-edit
  fi
  # 合流後一律以記錄為真回寫索引（上游若改記錄未回寫，在此補上），有改則另提交。
  # --membership 併治「有檔而索引無鍵／有鍵而無檔／path 過時」三型（坑 41）——
  # 大宗入庫與批次併條屢屢漏此善後，一漏則全庫閘紅，九道齊卡。
  python3 .claude/qa/reindex.py --run --membership | tail -2
  if ! git diff --quiet; then git add -A && git commit -q -m "合流後索引回寫（reindex.py）"; fi
  if ! python3 .claude/qa/verify.py | tail -1 | grep -q OK; then echo "VERIFY FAIL — 未推"; python3 .claude/qa/verify.py | head -12; exit 1; fi
  if git push -q origin HEAD:main 2>/dev/null; then git push -q origin "HEAD:$BR" 2>/dev/null; echo "已推 main（第 $i 輪）"; exit 0; fi
  echo "推 main 被拒，重合流（第 $i 輪）"
done
echo "三輪未成"; exit 1
