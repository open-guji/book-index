# qa-sweep 車道作業規程

多車道並行，對 production（本倉）逐時期做一次品質複查。每一車道是一個獨立會話，
領一個或數個 `period`，在自己的分支上做，**每批合流 main 並推 main**。
協調者（coordinator）另有一會話，收各道之報、彙坑、加檢、全庫掃、派活。

作業法本身見 `book-index-draft/.claude/skills/hanzhi-curation/SKILL.md`（必讀，尤其
〈只掃不改→零判斷批次→抽樣精讀→帶棄權批次→逐條裁決→快掃收尾〉、
〈磁鐵與合併陷阱〉、〈史料圈套〉、〈繫連寧缺毋濫〉）。本檔只講多道並行之規矩。

## 一、開工

```bash
git fetch origin main && git checkout -b claude/qa-<lane> origin/main
cat .claude/qa/PITFALLS.md                       # 每批開工前都再讀一次，它會長
python3 .claude/qa/scan.py --period <p1,p2> --out /tmp/<lane>.json   # 只掃不改
python3 .claude/qa/status.py --lane <lane> --periods <p1,p2> --works <N> --set batch=0 focus="畫像"
```

第一件事是把 `scan.py` 的計數表貼進 status 的 `found.*`，並讀每一類 15–30 條明細，
**先分清哪些是真缺陷、哪些是本時期之常態**（如唐人注漢書之 C 類、諸家各為注本之 I 類）。
常態者記一行於 status 之 note，不做。

## 二、三檔處置（使用者定的）

| 檔 | 判準 | 動作 |
|---|---|---|
| **明確** | 記錄自身之著錄原文、所繫之志、所繫之 entity 已足以定 | 直接修，`ai_note` 記據 |
| **不明確** | 庫內證據不足或互斥 | **先上網查**（維基百科優先，次 維基文庫／ctext／漢典／中國哲學書電子化計劃／各大學圖書館目錄），查到 ≥1 可靠且獨立之證再修；`ai_note` 記所查之頁（URL）與所得 |
| **仍不確定** | 查後仍兩可、或需要使用者裁 | **記入** `.claude/qa/known-issues/<lane>-<日期>-<題>.json`，附證與兩案，不動資料 |

「明確」的門檻按 skill：**同名不是同書，名之一部相合不是據，差一字且唯一不足以定人**。
凡改 period／撰人／entity 繫連，須有**獨立佐證欄**（skill〈表層計數不是缺陷之證據〉）：
著錄語、斷代志、entity 之生卒、同一 entity 名下他書之期分布（孤雁徵候）、period_upper。

網上查證之用法：`WebFetch` 抓 `https://zh.wikipedia.org/wiki/<題名或人名>`，
問「此人生卒、朝代、著作；此書撰人、成書年代、存佚」。維基之說須與庫內著錄相印證；
維基與著錄相斥時，以著錄原文為準而記疑，不逕從維基。

## 三、所有權（防撞）

只動這些：

1. **Work**：`period` 屬本道者。改其任何欄。
2. **Entity**：只在三種情形下動——
   (a) 改本道 work 之 `authors[].entity_id` 時，同步該 entity 之 `works[]`（雙向）；
   (b) 該 entity 名下**所有** work 皆屬本道，且其代（dynasty/period）明顯錯；
   (c) 該 entity 之名為 CBDB 卸除所遺之錯名（PITFALLS 坑 2），且名下唯本道之書。
   其餘 entity 之改（跨期之 entity、primary_name 之併、CBDB 之配）→ 記 known-issues 並報協調者。
3. **Book**：只經本道 work 之 `books[]`；Book 記錄本身除 `ai_note` 記疑外不動。
4. **索引**：只回寫自己改過之記錄之索引項，用 `jio.update_index`（保留分片原格式，diff 最小）。
5. **自己的檔**：`.claude/qa/status/<lane>.json`、`.claude/qa/known-issues/<lane>-*.json`。

**絕不**：批量刪 Work、批量併 Work（併一律逐條裁）、改 `PITFALLS.md`／`scan.py`（報協調者改）、
force-push、rebase、動別道之 status。

## 四、每批節奏（一批一類問題）

```
1. 寫腳本（乾跑 → 讀 15 條 → 真跑）          腳本須冪等：可在合流後重跑
2. python3 .claude/qa/verify.py                 漂移必須 0，懸空不得增
3. python3 .claude/qa/status.py --lane <lane> --set batch=N focus="…" \
       --add fixed.X=n researched.X=m recorded.X=k --note "本批一行" --commit $(git rev-parse --short HEAD)
4. git add -A && git commit                     訊息：做了什麼、幾條、依據、驗數
5. git fetch origin main && git merge origin/main --no-edit
       撞衝突：記錄檔取己（--ours）後重跑本批腳本；索引分片取彼（--theirs）後重跑本批之索引回寫
6. python3 .claude/qa/verify.py                 合流後再驗一次（坑 22）
7. git push origin HEAD:claude/qa-<lane> && git push origin HEAD:main
       推 main 被拒（有人先推）→ 回第 5 步，最多三輪
```

批要小（≤200 條記錄），合流要勤。改動大的批（如一次改幾百個 entity）先報協調者排時段。

## 五、學到的東西怎麼流通

- **踩坑**：一發現，`SendMessage` 協調者，格式：`[坑] <一句話> | 例：<id> | 判準：<一句話>`。
  協調者寫進 `PITFALLS.md` 並推 main；各道每批開工 `git merge origin/main` 後再讀。
- **新缺陷類**：`[新檢] <描述> | 例：<id,id> | 掃法：<一句偽碼>`。協調者加進 `scan.py`，
  全庫掃，把各期之數派給各道。
- **要人裁的**：寫 known-issues，`[待裁] <題> | <lane>-<日期>-<題>.json`。**不要問使用者**——
  使用者說了尽量少問；協調者彙總後一次問。
- **跨道之事**（entity 橫跨數期、一書兩期各有一條）：`[跨道] …`，協調者裁定誰動。
- 進度只走 status 檔，不走訊息。

## 六、記錄格式

`ai_note` 每次改動一段，以日期起頭：`2026-09-06 qa-sweep/<lane>：<改了什麼>。據：<著錄原文／志／URL>。原值：<可逆>。`
period 改動同時改 `period_basis`；撰人代改動寫 `authors[].dynasty_basis`；改繫寫 `authors[].name_basis`。

known-issues JSON：
```json
{"lane":"song","date":"2026-09-06","title":"…","kind":"重出待併|誤繫待裁|斷代兩可|其他",
 "records":[{"id":"…","title":"…","period":"…"}],
 "evidence":"…著錄原文、查到的頁…","options":["甲…","乙…"],"recommend":"甲","why":"…"}
```

## 七、收工

`scan.py --period <本道>` 再掃一次，計數貼 status；`verify.py --strict` 須 OK；
`status.py --lane <lane> --done --note "收工：…"`；推 main；`SendMessage` 協調者 `[收工] <lane>`。
