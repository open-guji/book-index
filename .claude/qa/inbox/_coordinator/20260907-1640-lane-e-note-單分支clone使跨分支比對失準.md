# lane-E 短記｜各道之 clone 是**單分支**的,跨分支比對因此可能失準(並解一個假警報)

## 事

各道之工作區皆由 `git clone --depth 1` 而來,而 `--depth 1` 會**隱含 `--single-branch`**,
於是 `remote.origin.fetch` 只有一條:

```
+refs/heads/main:refs/remotes/origin/main
```

**`git fetch origin` 於是永遠只更新 `origin/main`,不更新任何 `origin/claude/qa2-*`。**

## 兩個後果

**其一,跨分支比對可能讀到舊狀態。** 我先前補回 492 筆用的
`git rev-list --all --remotes`,其所讀之 `origin/claude/qa2-*` 是我當初以顯式 refspec
抓下來的**一次性快照**,此後各道再推,那些 ref 一動不動。
本道方才把 refspec 補正後重抓,`qa2-b` 與 `qa2-f` 二 ref **確實往前跳了**
——即先前那幾次比對讀的是過期的分支。**這次重比遺落仍是 0(未致傷),但那是運氣,不是保證。**

**其二,一個會反覆出現的假警報。** stop-hook 拿 HEAD 比 `origin/<自己的分支>`,
而該 ref 停在舊值,遂報「有 N 筆未推」——本道被報過兩次(14 筆、64 筆),
兩次查證都是 **HEAD＝遠端實況＝main,一筆未推之commit也沒有**。
（`pushmain.sh` 之 `git push -q origin "HEAD:$BR" 2>/dev/null` 推得成功,只是本地 ref 沒跟上。）

## 補法(一行,各道自便,不動共用工具)

```bash
git config --add remote.origin.fetch '+refs/heads/claude/qa2-*:refs/remotes/origin/claude/qa2-*'
git fetch origin          # 此後 origin/claude/qa2-* 會隨 fetch 自動更新
```

**凡要跑跨分支之賬比對者,請先補這一條再跑**,否則比的是自己上次抓的快照。
（水位線之閘不受此影響——它只看本地賬,不看分支。）

## 一句

這與本道今日所報之另二事是同一族:**`--ours` 靜默刪行、except 靜默放行、
單分支 clone 靜默不更新**——**都不報錯,都朝著「看起來沒事」的方向失效**。
查一個數對不對,得先問「我讀的這個數是什麼時候的」。
