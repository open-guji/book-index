# 去重方案部分 3a 第四轮：同 Entity 同题同名组（署名异写单元普查转来）

背景：3b（署名异写）普查 `../../dedup-3b/scan.py` 以首位撰人 Entity 为键，顺带统计出「同一 Entity、题名归一相同、署名也相同」1,103 组，归 3a。3a 第三轮收口后在最新 main（`812a7d2a56`）复算。

## 流程与划界

1. `scan.py` 取 kind=同题同名，剔除已有 related_works 或已登 `dedup-judged/*.tsv` 的对：仍有未判对 659 组；
2. 组内含叢書子目（ai_note 记「叢書子目」或 section 起于「叢書部」）的 613 组归 4a-α，清单在项目文件 `dedup-3b/同Entity同题同名-含叢書子目-待4a-alpha-20261026.tsv`；
3. 余 46 组用 `../r2/dossier.py` 建档（`同题组.tsv` → `dossier.jsonl`），逐组判（`mkbatch.py` 的 MERGE／HOLD）：
   - 拆分另立 33 组：成员是 3a-2乙「先拆后并」按编次拆出、或部分 6 族谱按「各修各算」拆出的，保持拆分，登 C（这些拆分此前未登 dedup-judged，故普查又冒出来；登记后不再出现）；
   - 方志 2 组（仙遊縣志、寧津縣志）交「合并重复方志 Work」单元；
   - 存疑 3 组：異物彙苑（十卷／十八卷）、文溪集（兩宋名賢小集一卷选本）、文獻公全集（十卷本对 3a-2乙 拆出的十一卷本）；
   - 并 8 组：漢碑引經考、春秋穀梁傳（程闡）、紫桃軒雜綴、經德堂文鈔、周易講疏（張譏）、國初事跡、周易象論、集議孝經（荀昶）。
4. `prefix.py`：并条前把 d59f27y30k5e《集議孝經》（荀昶）误挂的丁志「東陽太守袁宏」一节删去（袁宏条 d59f27ycowzl 已有同一著录）；
5. `run.sh <分支>`：从最新 main 重跑 prefix → mkbatch → `../apply_3a.py` → postfix_common → update_index → fix_draft → 全部门禁。

## 结果

| 批 | 组 | 说明 |
|---|---:|---|
| r4-01 | 8 | 逐组复核并，独立子 agent 逐条读原文核验，异质 0 |
| 不并 | 38 | `../存疑-第四轮.tsv`；对子入 `../../dedup-judged/3a-第四轮.tsv`（C 33 组、D 3 组、方志 2 组记 D） |

核验旁注（未在本轮处理）：周易象論 另有 d59f27ycowzm（作「樂筆」，未繫 Entity）、d59f9uw63nk1（无撰人）两条当同书，归部分 4／人物线；d59f27tdtxqb《集議孝經》署荀朂，黃逢元按语谓撰集者即荀昶，待另裁。周易講疏 并后有两条同节《隋志》著录（張機／張譏录文），可留一。

门禁：audit-merge-ledger（--draft）T/L/P/R/D 全 0；check_v2 0；check-classification 0；check_promo_dup 0；check-duplicate-audit PASS；build_derived 自检 0。草稿库无引用需改。

回滚：revert 本 PR。
