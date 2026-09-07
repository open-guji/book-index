# 急報｜`pushmain.sh` 之解衝突規則**靜默吞掉他道已推之裁決**（v2 地基受損，五道皆中）

**報者**：lane-E　**時刻**：2026-09-07 01:50　**嚴重度**：高（傷的是 `verdicts.jsonl` 本身）

## 現象（本道剛剛親歷，已自行補回）

推第一批時，`pushmain.sh` 印出：

```
非索引衝突，取己方：.claude/qa/for-user.md
非索引衝突，取己方：.claude/qa/verdicts.jsonl
```

`resolve_conflicts()` 對非 `index/*` 之衝突一律 `git checkout --ours`。
於是合流前 origin/main 上 lane-B 剛推的 **4 筆裁決憑空消失**，`for-user.md` 中
lane-B 的**兩則待裁條目**一併消失。**推成功，閘全綠，無任何告警**——
`verify.py` 查的是索引與記錄之一致，不查賬有沒有被吞。

本道已比對合流前之 `949bfd0cf7` 逐行補回（賬 496→500，for-user.md 補回 lane-B 一節）。

## 何以這是地基之傷，不是一次意外

`verdicts.jsonl` 是 **append-only 的共用賬**，五道同時往同一個檔尾追加，
**衝突是常態而非例外**。而 `--ours` 對 append-only 檔是**最壞的一種解法**：
它不是「取捨」，是**單方面刪除對方剛寫的行**，且刪得無聲無息。

PROTOCOL 改動一說「一條 rule 落賬，2,807 立刻變 2,297，而且不是把問題掃到地毯下」——
**但賬若會被下一個推的人吞掉，落賬就真的變成掃到地毯下了**：
掃描器不再報（本地賬還在），而賬上已無其據，下一輪誰也不知道那 4 條是誰判的、判了什麼。

本次是本道吞了 lane-B。**下一個推的人會照樣吞掉本道這 71 筆**，因為規則對誰都一樣。
以 v1 之數推之：九道十一小時，若每道每小時推一次，這種吞併每天發生數十次。

## 建議之修（規格。`pushmain.sh` 是共用工具，本道不自行改——硬規矩一）

1. **`.claude/qa/verdicts.jsonl` 之衝突不得取任一方，須「兩方並取」**：
   取 `--ours` 與 `--theirs` 兩份之行聯集，按 `(id, check, rule, verdict, by, at)` 去重後寫回。
   賬是 append-only 且後寫蓋先寫（`verdicts.load()` 之語意），**聯集即是正解**，順序無關緊要。
   最省事之法是給該檔設 union 合流驅動：
   `.gitattributes` 加 `.claude/qa/verdicts.jsonl merge=union`。**一行可了。**
   （`for-user.md` 亦是各道只追加自己一節，同樣適用 `merge=union`；
   其結果或有重複之分隔線，但**寧可留贅字，不可失他道之條目**。）
2. **加一道驗收**：推前比對「合流後之賬行數 ≥ 合流前兩方各自之行數」，不足即中止。
   坑 36 之教訓正是「靜默失敗後硬提交」——本則是同一個病在另一個檔上復發：
   `git checkout --ours` 這次**成功**了，成功地刪掉了不該刪的東西，所以連中止都不會觸發。
3. 順帶：`resolve_conflicts()` 現行之 `*)` 全包規則，對**任何**新增的共用檔都會如此。
   建議改為白名單——`index/*` 取彼方、賬與佇列取聯集、**其餘未列者一律中止並印檔名**，
   由人決定，不要替人猜。

## 各道請即自查

凡 2026-09-07 之後推過 main 且見過「非索引衝突，取己方：.claude/qa/verdicts.jsonl」
一行者，請以合流前之 origin/main 逐行比對自己是否吞了人。查法：

```bash
git log --oneline --all -- .claude/qa/verdicts.jsonl   # 找合流前之 commit
python3 - <<'PY'
import json,subprocess
def L(ref):
    o=subprocess.run(['git','show',ref+':.claude/qa/verdicts.jsonl'],capture_output=True,text=True).stdout
    return [l for l in o.splitlines() if l.strip()]
k=lambda l:(lambda d:(d.get('id'),d.get('check'),d.get('rule'),d.get('verdict'),d.get('by')))(json.loads(l))
mine=[l for l in open('.claude/qa/verdicts.jsonl').read().splitlines() if l.strip()]
have={k(l) for l in mine}
print([l for l in L('<合流前之 commit>') if k(l) not in have])
PY
```
