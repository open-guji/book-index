# 待使用者裁決之佇列 —— 已遷走

**2026-09-07 使用者定：待審問題一律放**

```
overview/项目进展/古籍索引网站/待审元数据/
```

**其他所有會話都往那裡放。本檔不再受理，勿再往下追加。**

那個資料夾的規矩見其 `README.md`，撮要如下：

- **一個會話一個檔**，檔名 `<會話名>-<YYYYMMDD>-<短題>.md`。
  各寫各的，不共寫一檔——共寫必生衝突（本檔即為此才打了 `merge=union` 的補丁）。
- 協調者維護兩個匯總檔，各會話勿動：
  - `00-待裁总清单.md`——本檔遷去之全文，並各道待裁項之匯總；
  - `01-全库质量复查-待裁清单.md`——`report.py` 每輪重跑生成。
- **放檔之外仍要落賬**：`verdict=open` 該落照落。
  只放檔不落賬，下一道會把同一批再讀一遍（v1 九道之敗正在此處）。

本檔遷走前之全文，逐字存於 `00-待裁总清单.md`，未刪一條。
- [ ] 2026-09-07 [lane-F] **`mergework.py` 之善後尚缺第八、第九件**（本道併二十二組所見）：
      **第八：不搬被併者獨有之欄位。** 七件只管 id 之指向（索引項、entity 反邊、著錄、他條
      related_works、Book、Collection、merged_in），而 `emendated_by`／`additional_titles`／
      `original_title`／`period_upper`(+basis)／`loss_status`／`juan_count`／`resources`／`fragments`
      若只被併者有，併後即隨檔而亡。本道十組撞上，皆以人手搬入並記於 keeper 之 ai_note。
      **第九：節數增則以節數為閾之檢會由不報變報。** 《答問雜儀》併後著錄達四節而 description
      全缺，J 檢立刻報之（≥4 源而 desc 全缺）——本道併條所生，本道補之。
      建議 `mergework.py` 加一步「併後復驗 keeper」，至少驗 J／V 二檢。
- [ ] 2026-09-07 [lane-F] **併條後空無所繫之 entity 又添六條**（前記五條，今共十一）：
      `hixhd2h9bmt5`（謝嶠，與 hixhd2h9bkcb 重出）、`hixhd2h9bl68`（袁折）、`hixhd2h9biwy`（楊義）、
      `hixhd2h9bl5f`（顔彪）、`hixhd2h9bl86`（叚弘）——皆一名二形所生之重出人條，其名已收入正條之
      alt_names。宜一次刪或併（走 `dropnode.py`，並驗七處反邊）。
- [ ] 2026-09-07 [lane-F] **庫例未備一處：「引他條之著錄節以存異說」沒有位置**。
      《喪服變除》戴德條之 description 明寫「諸志撰人所歸不一……本條依多數之志從戴德」，
      而其所引之《隋志》「葛洪撰」二節，正是用來存那個異說的——**不是誤掛**。
      現行 Y 之 `misattached` 假定「一節只該掛一條」，於此型必恆報而無可辦。
      宜為之立一欄位（如 `cited_by`／`counter_evidence`，或於節上加 `as_counter_evidence` 之記），
      使「引以存異說」與「誤掛」可分。詳見 `lane-f-20260907-喪服變除戴德抑葛洪.json`。
