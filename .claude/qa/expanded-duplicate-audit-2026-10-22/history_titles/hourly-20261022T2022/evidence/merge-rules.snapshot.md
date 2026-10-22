# 正式库并条审查规则（2026-10-22，据 PR #1209 审查整理）

适用：草稿升格完成后，在正式库内合并重复的 Person（Entity）、Work、Book。

## 一、判同口径
- 只认「确定同一」才并；错并难拆，漏并可等证据再并（沿用项目原则）。
- Book：同源记录（source_key）且去掉 id／work_id／管理字段后全字段相同，可机械并；只有 edition、dating、题名措辞不同的，须读原文。#1209 的 1,397 组里 1,395 组题名、版本、断代全等，是最安全的一类。
- Work：同题同首位责任者同朝代，可并。首位责任者或题名不同的（#1209 里约 15 组），逐组看证据：异体字、讹字、简称（摭言／唐摭言）、叢書子目与单行本，可并；集传／通释这类责任层次不同的，并后两个责任者都要留。
- Person：必须有独立证据（别名互列、共享 Wikidata/VIAF/上图 URI、生卒与籍贯一致、同一著录原文），并后加朝代与著作领域复核（防张果／张杲类错并）。只凭同名或形近不并。
- 不并：外部标识矛盾而无法解释的、一侧挂文章 Work 另一侧挂碑刻 Work 的（如 BOOK-0010）。

## 二、并后必须做到
1. 被并者只留墓碑（schema 允许的最小字段 + merged_into）；keeper 不是墓碑，且写 merged_from（Book）或 merged_in（Work／Entity）。
2. 无损：被并者的 contained_in、resources、indexed_by、作者、出边关系，并后在 keeper 里仍找得到；冲突字段不盲覆盖，记入台账。被并者的 ai_note／description 若有独有信息，要写进台账或 keeper，不要只靠 git 历史。
3. 引用全改写：Work／Book／Collection／Entity／分类成员／promotions 的 production_id。历史并条账里的旧 ID 不改。
4. promotions 只允许「被并者 → keeper」的值变化，不得有别的改动。（`check_promo_dup.py` 会把这些改动报成 DUP，是预期，不是双晋升；需让它识别 merged_into 链，或在 PR 里说明。）
5. 草稿库同步：草稿库里指向被并 ID 的 work_id、merged_into、related_works、分类成员要另开草稿库 PR 改指 keeper，否则形成「草稿墓碑 → 正式墓碑 → keeper」两跳链。
6. 父 Collection 重复而 Book 已并时：Book 的 contained_in 保留两侧，另立 Collection 墓碑 schema 后再并 Collection。

## 三、怎么审（脚本）
`python3 scripts/audit-merge-ledger.py --ledger <台账 merges.json> --base origin/main --draft ../book-index-draft`
工作树切到被审 PR 分支后运行。T 墓碑、L 无损、P 升格表、R 引用 任一 ERROR 即不放行；D 草稿库残留要有后续 PR；Q 是质量统计，看数不拦。

另需：`.claude/qa/check_v2.py --paths -`（只喂变更文件，路径用 `git -c core.quotePath=false diff --name-only`，否则「查 0 檔」假绿）、`scripts/check-classification.py`、`build/build_derived.py --check-only`。

## 四、流程
- 先出台账（每组：keeper、losers、证据、前置 sha256），后动数据；台账与数据同 PR。
- 合并脚本应入库，或明确复用 `.claude/qa/mergework.py`；不入库则无法复现。
- 分批合：每批 ≤ 几百组，便于抽检与回滚；正式库只追加的例外需用户逐类放行。
- 合 PR 前合 main，并重新跑审计脚本，确认没有新晋升记录指向被并 ID。
