# 急報［lane-D］`pushmain.sh` 之解衝突把他道之賬吞了——已補回，並附治本

## 一、發生了什麼

本道推第一批時，`pushmain.sh` 印：

```
非索引衝突，取己方：.claude/qa/for-user.md
非索引衝突，取己方：.claude/qa/verdicts.jsonl
已推 main（第 1 輪）
```

「已推」而**未失敗**，故不會有人察覺。實則吞掉了合流時 main 上的：

| 被吞者 | 筆數 |
|---|---:|
| lane-E `P-異體形近` normal | 29 |
| lane-E `P-庫證異稱` normal | 18 |
| lane-E `O-跨代標籤確證已撤` fixed | 9 |
| lane-E `P-名字封號` normal | 5 |
| lane-E 其餘（`P-偽稱標廢`／`E-題名孤證繫Book待裁`／`R-`／`S-`） | 6 |
| lane-B `I-秦榮光補晉志入庫重出` 等 | 4 |
| **合計** | **71 筆** |

另 `for-user.md` 之 **lane-B 整段**（入庫撞庫「兩造撰人皆空不得逕判異書」、
秦志《孝經》待裁二則）亦被整段刪去。

**已全數補回**（本提交）：71 筆逐筆追加（與本道所裁之 `(id,check)` 撞者為 0，
故無覆蓋之虞），lane-B 之 for-user 段落照原文補回本道段之前。
賬今為 788 筆＝717（本道推前）＋71。

## 二、病根：**「取己方」對 append-only 之檔是刪除**

```bash
*)  echo "非索引衝突，取己方：$f"; git checkout --ours -- "$f" ;;
```

索引檔取彼方而後 `reindex` 回寫，是對的——索引可由記錄重建。
但 `verdicts.jsonl` 是 **append-only 之賬**、`for-user.md` 是 **append-only 之佇列**，
**二者都重建不了**。兩道各自在檔尾追加，git 視為衝突，而「取己方」＝把對方那一段扔掉。

坑 36 治的是「衝突標記被硬提交」（看得見的病）；
此則是「衝突被靜默地解錯」（看不見的病）——**驗收全過、verify 全 0、推送成功**，
唯獨資料少了。提交 `254023de39` 已為 lane-B 補過一次四筆，今又重演，是**第三次**。

## 三、治本（本提交已行，請覆核）

新增 `.gitattributes`：

```
.claude/qa/verdicts.jsonl merge=union
.claude/qa/for-user.md    merge=union
```

`union` 是 git 內建之合流驅動，兩造之行皆留，**故此二檔根本不再產生衝突**，
`resolve_conflicts()` 也就永遠碰不到它們——不必改 `pushmain.sh` 一個字。

已實測（另起一空庫，兩造各自於檔尾追加一行）：
合流後兩行俱在，且 `Auto-merging` 無衝突。

`verdicts.jsonl` 用 union 正合其語意：一行一裁，`load()` 以後寫者為準，
兩道之裁本就該並存。`for-user.md` 用 union 之果或有重複條目，
**但重複可刪，刪掉的找不回來**。

## 四、請協調者再做兩件（本道不敢代行）

1. **查前幾輪是否也吞過**。本次之所以查出，是因為本道在推完後
   逐筆比對了合流之第二 parent（`git show <merge>^2:.claude/qa/verdicts.jsonl`）。
   若他道推送時亦印過「非索引衝突，取己方：.claude/qa/verdicts.jsonl」而未比對，
   則那一輪的賬也少了。建議把每個合流提交都跑一次此比對，補齊為止。
   （本道只查了自己這一次，不敢代斷他輪。）
2. **`pushmain.sh` 宜加一句事後驗收**：合流後 `verdicts.jsonl` 之行數
   不得少於 `^2` 之行數。union 之後理應恆真，加之則日後若有人改回舊法即刻現形。

## 五、通則（擬入 PITFALLS）

**「取己方／取彼方」只對「可重建之衍生檔」是安全的解法。**
對 append-only 之賬與佇列，任何一造之「取」都是刪除——
而刪除之後，驗收、閘、推送全都會通過，**因為少掉的東西不會讓任何檢查失敗**。
凡共用之檔，先問一句：**它是衍生的，還是累積的？** 累積者只能 union，不能取捨。
