#!/usr/bin/env bash
# 合流 origin/main 並推 main；索引分片撞衝突則取彼方後以記錄為真回寫（reindex.py）。最多三輪。
# **非索引（條目檔）衝突一律中止交人**，不自動取捨——見 resolve_conflicts() 內 2026-09-14 那段。
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

# 列出當前未解衝突（NUL 分隔且關閉檔名跳脫，中文檔名方能正確取得），一行一檔
unresolved() {
  git -c core.quotePath=false diff -z --name-only --diff-filter=U | tr '\0' '\n' | grep . || true
}

resolve_conflicts() {
  # ── 2026-09-14 改（先秦-傳世版本道所報，用戶當日裁「甲案」）───────────────────
  # 原作：非 index/ 之衝突一律 `git checkout --ours`，只 echo 一行，不中止、不非零退出。
  # 那正是[任務書模板]§四鐵律 2 明令禁止的一件：**條目檔衝突不許 --ours**，
  # 因為 --ours 對條目檔的語義是「丟掉對方對這個檔的全部改動」——
  # 兩道各改各的字段族本不該衝突，是 git 行級合併把 JSON 相鄰字段判成撞行；
  # 一 --ours，後推的那道就把先推的那道抹掉，而且**雙方都不會收到任何告警**。
  #
  # 2026-09-14 當日四道並行，實測踩中兩次、兩次都真丟了東西（野老 resources、
  # 周禮題名訂正＋ai_note），皆靠人事後肉眼發現才修回。協調者以三方 blob OID
  # 掃當日 11 個合流提交覆核，確為此二處、無第三處。
  #
  # 今改為：**非索引衝突一律中止，不自動解**。代價只是多推一輪，
  # 而 --ours 丟數據是不可逆且無聲的。衝突狀態原樣留在工作區，由人做三方合併後再推。
  local nonidx
  nonidx="$(unresolved | grep -v '^index/' || true)"
  if [ -n "$nonidx" ]; then
    echo "非索引衝突 $(printf '%s\n' "$nonidx" | grep -c .) 檔 — 中止，不自動解：" >&2
    # 檔名一律整行處理，**不得讓 shell 按空白斷詞**（坑 36 同族：此檔的舊病正在檔名處理）
    printf '%s\n' "$nonidx" | sed 's/^/  /' >&2
    cat >&2 <<'EOF'
  這些是條目檔，不許用 --ours／--theirs 了事（鐵律 2）。請人做三方合併：
      git show :1:<檔>  # base    :2:<檔>  # ours    :3:<檔>  # theirs
  逐頂層鍵比對：只有一方改過的鍵取那一方；兩方都改過同一鍵才須人裁。
  合好後 git add 該檔，再重跑本腳本。衝突狀態已原樣保留，未做任何自動取捨。
EOF
    return 1
  fi

  # 至此只剩 index/* —— 索引分片是派生物，取彼方後由 reindex.py 以記錄為真回寫
  git -c core.quotePath=false diff -z --name-only --diff-filter=U | \
  while IFS= read -r -d '' f; do
    git checkout --theirs -- "$f" || echo "取彼方失敗：$f" >&2
    # `git checkout --ours/--theirs` 只還原內容，**不把該路徑自未合併之列除去**——
    # 須 `git add` 方算解決。2026-09-06 加了「提交前驗收未解之衝突為零」一步（坑 36 之乙法）
    # 後，此漏遂現形：內容已取而路徑仍列未合併，驗收即誤判為「解衝突未竟」而中止（坑 58）。
    git add -- "$f" || echo "標記已解失敗：$f" >&2
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
  # 2026-09-07 lane-B 所報：`git commit -m "…`x`…"` 之中，雙引號裡的反引號是**命令替換**
  # ——shell 先去執行它、得 command not found、replace 成空字串，再把空字串交給 git。
  # git 不報錯、提交成功、推送成功、verify 全綠，**只有字沒了**。而我們的提交訊息是 markdown，
  # 標記檔名／id／欄位名的正規寫法正是反引號——**這個坑正對著我們的寫作習慣**。
  # 治本是一律用 `-m "$(cat <<'EOF' … EOF)"`（界詞必加單引號）或 `-F <檔>`；
  # 此處只加一道極輕之警（反引號數為奇即疑有被吃掉者，不完備而夠用），不中止。
  if [ "$(git log -1 --format=%B | tr -cd '`' | wc -c)" -gt 0 ] && \
     [ $(( $(git log -1 --format=%B | tr -cd '`' | wc -c) % 2 )) -ne 0 ]; then
    echo "警：本次提交訊息之反引號為奇數個，疑有整段被 shell 之命令替換吃掉（lane-B 所報）" >&2
    echo "    治本：git commit -m \"\$(cat <<'EOF' … EOF)\"，界詞必加單引號" >&2
  fi
  if ! python3 .claude/qa/verify.py | tail -1 | grep -q OK; then echo "VERIFY FAIL — 未推"; python3 .claude/qa/verify.py | head -12; exit 1; fi
  if git push -q origin HEAD:main 2>/dev/null; then
    # 2026-09-07：推自己的分支原作 `git push -q … 2>/dev/null`——**失敗即被吞**，
    # 於是 main 推成了、分支落在後面，而腳本照印「已推 main」。停止鉤子隔了幾輪才報
    # 「有 8 筆未推」，查證方知是這一行。與 lane-E 所歸納之「都不報錯、都朝著看起來沒事的
    # 方向失效」同族——凡以 2>/dev/null 掩其口者，都該問一句「它閉嘴的時候發生了什麼」。
    if ! git push -q origin "HEAD:$BR"; then
      echo "警：main 已推，但推自己的分支 $BR 失敗（見上之錯誤）——本地與該分支自此分歧" >&2
    fi
    echo "已推 main（第 $i 輪）"; exit 0
  fi
  echo "推 main 被拒，重合流（第 $i 輪）"
done
echo "三輪未成"; exit 1
