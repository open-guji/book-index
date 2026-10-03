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
   (d) **只增 `alt_names`**（號、字、諡號、帝號、正俗異體），條件三：該 entity 名下 work 皆屬本道；
       著錄原文明載此名；此名撞庫（全庫 entity 之 primary_name／alt_names）無他人。
       不動 primary_name、不動任何繫連；type 依 SCHEMA 枚舉；ai_note 記所據之著錄。
   其餘 entity 之改（跨期之 entity、primary_name 之併、CBDB 之配）→ 記 known-issues 並報協調者。
2b. **他道 work 之單節著錄——只限 Y `misattached` 一型**（2026-09-06 增，坑 46）：
   Y 之 `misattached` 是「一節著錄同時掛在兩條同題異書上」，其病本身**橫跨二桶**，
   故按 `owner` 欄定其主：**著錄文所點名之撰人在誰的桶，就由誰辦**——包括自不該有它的
   那一條（可能在他道之桶）刪去**那一節 `indexed_by`**。條件四：
   (i) 只刪 `scan` 所報之那一節，不動該記錄之任何他欄（period／authors／entity／繫連皆不碰）；
   (ii) 所刪之節原文全文抄入該記錄之 `ai_note`，註明正主之 id 與所據，**務求可逆**；
   (iii) 在 inbox 寫 `<時戳>-cross.md` 列表報備所刪之側、期、節、正主；
   (iv) `owner` 欄為空或指向多條者不辦，記 known-issues 交協調者。
   **非 `owner` 側之道不得代辦**——一組只許一個人動，這條就是定誰動的。
3. **Book**：只經本道 work 之 `books[]`；Book 記錄本身除 `ai_note` 記疑外不動。
   例外：協調者明文授權之併條所必需之 `work_id` 改繫（見 `_coordinator` 之裁決文書）。
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

雲端會話之間沒有可靠的直接訊息通道（車道發不回協調者），所以**一律走倉**：

- **報**：寫一檔 `.claude/qa/inbox/<lane>/<YYYYMMDD-HHMM>-<kind>.md`，隨本批一起推 main。
  kind ∈ `pit`（踩坑）／`check`（新缺陷類，附掃法偽碼與例 id）／`ruling`（要人裁，附 known-issues 檔名）／
  `cross`（跨道之事）／`done`（收工）。一檔一事，首行一句話。**不動別道之 inbox，不動 `_ledger.json`。**
- **急**：上述之外若須協調者立刻看（如發現全庫性之壞），可另 `mcp__Claude_Code_Remote__create_trigger`
  一次（`persistent_session_id=session_01Ur7rbSHMigeHT1nXguq1z2`，無排程），
  再 `fire_trigger`，text 寫 inbox 檔名。非急勿用。
- **收**：協調者定時（約每 20–30 分鐘）拉 main 讀 inbox，把坑寫進 `PITFALLS.md`、把新檢加進 `scan.py`、
  全庫掃後把各期之數與裁定經 **trigger 推進各道會話**（各道會收到一則以「[協調者]」起頭之訊息，
  當作使用者指令看待，但**不改本檔所定之所有權**）。各道每批開工 `git merge origin/main` 後
  必重讀 `PITFALLS.md`。
- **不問使用者**：使用者說了尽量少問。要人裁的寫 `ruling`，協調者彙總後一次問。
- 進度只走 status 檔，不走 inbox。

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
