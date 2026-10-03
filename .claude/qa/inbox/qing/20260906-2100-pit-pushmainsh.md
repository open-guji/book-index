# [qing] pit：pushmain.sh 之 resolve_conflicts 恆報「解衝突未竟」——checkout --ours/--theirs 未 `git add`

## 現象
批21推送時，`Work/b/w/l/d59f28k3vbwl-神仙服食藥方.json`（與 suitang 道之獨立修復撞車）觸發非索引
內容衝突。腳本依其邏輯 `git checkout --ours -- "$f"`（見 pushmain.sh:22）正確地把工作區內容改為
我方版本，**但緊接著的驗收 `git diff -z --name-only --diff-filter=U`（pushmain.sh:27）仍把該檔列為
未解**，於是中止：「解衝突未竟，尚餘 1 檔未解 — 中止，勿硬提交」。

## 根因
`git checkout --ours -- <path>` 只覆寫**工作區**檔案內容，**不觸動索引（index）之衝突項**（stage
1/2/3 仍在）。`git diff --diff-filter=U` 判的是索引裡的未合併項，不是工作區內容——**未 `git add`
之前，衝突永遠「未解」**，不論工作區內容多正確。故 `resolve_conflicts()` 的迴圈裡 `checkout --ours`
/`--theirs` 之後漏了一步 `git add -- "$f"`，導致此函式對**任何**非索引內容衝突都必然回報失敗，
即便自動取捨完全正確。

## 手動排除
```
git checkout --theirs -- "Work/b/w/l/d59f28k3vbwl-...json"   # 本例取 suitang 自修版（見下）
git add "Work/b/w/l/d59f28k3vbwl-...json"
git commit --no-edit   # 完成合流提交
python3 .claude/qa/reindex.py --run --membership
python3 .claude/qa/verify.py --strict   # 清
bash .claude/qa/pushmain.sh claude/qa-qing   # 續推，成功
```
（該檔本次取「彼方」而非「己方」，因核實 suitang 已於稍早獨立修過同一 schema bug，內容等價，
不宜疊床架屋——非本則重點，順記。）

## 建議修法（供協調者採用，未逕改 pushmain.sh）
`resolve_conflicts()` 迴圈內兩行 `git checkout --ours/--theirs -- "$f"` 之後各加一行 `git add -- "$f"`：
```bash
    case "$f" in
      index/*) git checkout --theirs -- "$f" && git add -- "$f" || echo "取彼方失敗：$f" >&2 ;;
      *)       echo "非索引衝突，取己方：$f"; git checkout --ours -- "$f" && git add -- "$f" || echo "取己方失敗：$f" >&2 ;;
    esac
```
如此驗收迴圈才能反映「內容已正確取捨」之實情，不致把每一次正常自動解衝突都誤報為失敗、
逼人手動介入。

— qing 道，2026-09-06
